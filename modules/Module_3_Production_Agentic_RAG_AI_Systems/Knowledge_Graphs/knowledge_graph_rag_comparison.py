"""
RAG vs Knowledge Graph Evaluation System
=========================================

A comprehensive framework for comparing Retrieval-Augmented Generation (RAG)
and Knowledge Graph (KG) approaches for question-answering systems.

Built with Neo4j and OpenAI GPT-4o-mini for production-ready evaluations.

Learn more about building advanced multi-agent systems:
https://maven.com/boring-bot/advanced-llm?promoCode=200OFF
"""

import os
from neo4j import GraphDatabase
from openai import OpenAI
from typing import List, Dict, Any
import time
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Neo4jGraphRAG:
    """
    A comprehensive system for comparing RAG and Knowledge Graph approaches.

    Features:
    - RAG with semantic search and embedding-based retrieval
    - Knowledge Graph queries with Text-to-Cypher conversion
    - LLM-based evaluation and comparison framework
    """

    def __init__(self):
        """Initialize Neo4j connection and OpenAI API."""
        self.uri = os.getenv("NEO4J_URI")
        self.username = os.getenv("NEO4J_USERNAME")
        self.password = os.getenv("NEO4J_PASSWORD")
        self.database = os.getenv("NEO4J_DATABASE", "neo4j")

        if not all([self.uri, self.username, self.password]):
            raise ValueError(
                "Missing Neo4j credentials. Please set NEO4J_URI, "
                "NEO4J_USERNAME, and NEO4J_PASSWORD in your .env file"
            )

        self.driver = GraphDatabase.driver(
            self.uri,
            auth=(self.username, self.password)
        )

        # Initialize OpenAI client (v1.0+ style)
        openai_api_key = os.getenv("OPENAI_API_KEY")
        if not openai_api_key:
            raise ValueError(
                "Missing OpenAI API key. Please set OPENAI_API_KEY in your .env file"
            )

        # Create OpenAI client without proxy configuration
        try:
            self.openai_client = OpenAI(api_key=openai_api_key)
        except TypeError as e:
            if 'proxies' in str(e):
                # Fallback: create client with explicit httpx client to bypass proxy issues
                import httpx
                http_client = httpx.Client(
                    timeout=httpx.Timeout(60.0, connect=10.0),
                    limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
                )
                self.openai_client = OpenAI(api_key=openai_api_key, http_client=http_client)
            else:
                raise

    def close(self):
        """Close the Neo4j driver connection."""
        self.driver.close()

    def execute_query(self, query: str, parameters: Dict = None) -> List[Dict]:
        """Execute a Cypher query and return results."""
        with self.driver.session(database=self.database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def load_data(self, csv_url: str):
        """Load data from CSV into Neo4j graph database."""
        q_load = f"""
        LOAD CSV WITH HEADERS
        FROM '{csv_url}'
        AS row
        FIELDTERMINATOR ';'
        MERGE (a:Article {{title:row.Title}})
        SET a.abstract = row.Abstract,
            a.publication_date = date(row.Publication_Date)
        WITH a, row
        FOREACH (researcher in split(row.Authors, ',') |
            MERGE (p:Researcher {{name:trim(researcher)}})
            MERGE (p)-[:PUBLISHED]->(a))
        WITH a, row
        FOREACH (topic in [row.Topic] |
            MERGE (t:Topic {{name:trim(topic)}})
            MERGE (a)-[:IN_TOPIC]->(t))
        """
        return self.execute_query(q_load)

    def get_embedding(self, text: str) -> List[float]:
        """Generate embeddings using OpenAI's text-embedding model."""
        response = self.openai_client.embeddings.create(
            model="text-embedding-3-small",
            input=text
        )
        return response.data[0].embedding

    def create_embeddings_for_articles(self):
        """Create and store embeddings for all articles in the database."""
        articles = self.execute_query("""
            MATCH (a:Article)
            RETURN id(a) as id, a.title as title, a.abstract as abstract
        """)

        print(f"Creating embeddings for {len(articles)} articles...")
        for i, article in enumerate(articles, 1):
            text = f"{article['title']} {article['abstract']}"
            embedding = self.get_embedding(text)

            self.execute_query("""
                MATCH (a:Article)
                WHERE id(a) = $id
                SET a.embedding = $embedding
            """, {
                "id": article['id'],
                "embedding": embedding
            })

            if i % 10 == 0:
                print(f"  Progress: {i}/{len(articles)}")

        print(f"✅ Created embeddings for all {len(articles)} articles")

    def retrieve_context(self, question: str, limit: int = 5) -> str:
        """
        Retrieve relevant context from the graph using keyword matching.

        This is the RAG retrieval step - finding relevant documents.
        """
        keywords = question.lower().split()

        cypher_query = """
        MATCH (a:Article)
        WHERE ANY(keyword IN $keywords WHERE
            toLower(a.title) CONTAINS keyword OR
            toLower(a.abstract) CONTAINS keyword)
        OPTIONAL MATCH (a)-[:IN_TOPIC]->(t:Topic)
        OPTIONAL MATCH (r:Researcher)-[:PUBLISHED]->(a)
        WITH a,
             collect(DISTINCT t.name) as topics,
             collect(DISTINCT r.name) as authors
        RETURN a.title as title,
               a.abstract as abstract,
               a.publication_date as date,
               topics,
               authors
        ORDER BY size(authors) DESC
        LIMIT $limit
        """

        results = self.execute_query(cypher_query, {
            "keywords": keywords,
            "limit": limit
        })

        context_parts = []
        for i, record in enumerate(results, 1):
            context = f"""
Article {i}: {record['title']}
Authors: {', '.join(record['authors']) if record['authors'] else 'N/A'}
Topics: {', '.join(record['topics']) if record['topics'] else 'N/A'}
Abstract: {record['abstract']}
Date: {record['date']}
---"""
            context_parts.append(context)

        return "\n\n".join(context_parts)

    def retrieve_with_vector_search(self, question: str, limit: int = 5) -> str:
        """Retrieve using vector similarity for semantic search."""
        embedding = self.get_embedding(question)

        cypher_query = """
        MATCH (a:Article)
        WHERE a.embedding IS NOT NULL
        WITH a,
             gds.similarity.cosine(a.embedding, $query_embedding) AS similarity
        ORDER BY similarity DESC
        LIMIT $limit
        OPTIONAL MATCH (a)-[:IN_TOPIC]->(t:Topic)
        OPTIONAL MATCH (r:Researcher)-[:PUBLISHED]->(a)
        WITH a, similarity,
             collect(DISTINCT t.name) as topics,
             collect(DISTINCT r.name) as authors
        RETURN a.title as title,
               a.abstract as abstract,
               topics,
               authors,
               similarity
        """

        results = self.execute_query(cypher_query, {
            "query_embedding": embedding,
            "limit": limit
        })

        context_parts = []
        for i, record in enumerate(results, 1):
            context = f"""
Article {i} (Similarity: {record['similarity']:.3f}):
Title: {record['title']}
Authors: {', '.join(record['authors'])}
Topics: {', '.join(record['topics'])}
Abstract: {record['abstract']}
---"""
            context_parts.append(context)

        return "\n\n".join(context_parts)

    def generate_answer(self, question: str, context: str) -> str:
        """
        Generate answer using LLM with retrieved context.

        This is the generation step of RAG.
        """
        prompt = f"""You are a helpful assistant that answers questions based on the provided context from a knowledge graph.

Context from Knowledge Graph:
{context}

Question: {question}

Please provide a comprehensive answer based on the context above. If the context doesn't contain enough information to answer the question, say so.

Answer:"""

        response = self.openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful research assistant."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )

        return response.choices[0].message.content

    def query(self, question: str, use_vector_search: bool = False) -> Dict[str, Any]:
        """
        Main RAG query method.

        Args:
            question: The user's question
            use_vector_search: Whether to use semantic vector search or keyword matching

        Returns:
            Dictionary containing answer, context, sources, and timing info
        """
        start_time = time.time()

        if use_vector_search:
            context = self.retrieve_with_vector_search(question)
        else:
            context = self.retrieve_context(question)

        if not context:
            return {
                "answer": "I couldn't find any relevant information in the knowledge graph.",
                "context": "",
                "sources": [],
                "time": time.time() - start_time
            }

        answer = self.generate_answer(question, context)

        return {
            "answer": answer,
            "context": context,
            "sources": self.extract_sources(context),
            "time": time.time() - start_time
        }

    def extract_sources(self, context: str) -> List[str]:
        """Extract article titles from context as sources."""
        sources = []
        for line in context.split('\n'):
            if line.startswith('Article') and ':' in line:
                title = line.split(':', 1)[1].strip()
                sources.append(title)
        return sources

    # ============================================
    # TEXT-TO-CYPHER FUNCTIONALITY
    # ============================================

    def get_graph_schema(self) -> str:
        """Get the current graph schema with examples."""
        sample_query = """
        MATCH (r:Researcher)-[:PUBLISHED]->(a:Article)-[:IN_TOPIC]->(t:Topic)
        RETURN r.name as researcher, a.title as article, t.name as topic
        LIMIT 3
        """

        samples = self.execute_query(sample_query)

        schema = f"""
Graph Database Schema:
=====================

Node Types:
-----------
1. Researcher
   Properties: name (string)
   Example: "Emily Chen", "Dr. Sarah Williams"

2. Article
   Properties: title (string), abstract (string), publication_date (date)
   Example: "AI in Healthcare", "Machine Learning Applications"

3. Topic
   Properties: name (string)
   Example: "Artificial Intelligence", "Climate Change"

Relationships:
--------------
1. (Researcher)-[:PUBLISHED]->(Article)
   - A researcher published an article

2. (Article)-[:IN_TOPIC]->(Topic)
   - An article belongs to a topic

Important Notes:
----------------
- Multiple researchers can publish the SAME article (co-authorship)
- An article can have multiple topics
- Use MATCH patterns to find relationships
- Use WHERE clauses for filtering
- Use toLower() for case-insensitive matching
- Property access: node.property (e.g., r.name, a.title)

Sample Data:
------------
"""
        for sample in samples:
            schema += f"\n• {sample['researcher']} -> {sample['article'][:50]}... -> {sample['topic']}"

        return schema

    def text_to_cypher(self, question: str) -> Dict[str, Any]:
        """
        Convert natural language question to Cypher query using LLM.

        This is the key step in the Knowledge Graph approach.
        """
        schema = self.get_graph_schema()

        prompt = f"""{schema}

Task: Convert the following natural language question into a valid Neo4j Cypher query.

Rules:
1. Return ONLY the Cypher query, no explanations
2. Use proper Neo4j syntax
3. Use MATCH for finding patterns
4. Use WHERE for filtering
5. Use RETURN to specify what to return
6. Use toLower() for case-insensitive text matching
7. Limit results to 20 unless asked otherwise
8. For "collaborators", find researchers who published the SAME article
9. For counting, use count() function
10. For finding by name, use WHERE node.name = "exact name" or CONTAINS for partial match

Common Query Patterns:
- Find collaborators: MATCH (r1:Researcher)-[:PUBLISHED]->(a:Article)<-[:PUBLISHED]-(r2:Researcher)
- Count articles: MATCH (r:Researcher)-[:PUBLISHED]->(a) RETURN r.name, count(a)
- Find by topic: MATCH (a:Article)-[:IN_TOPIC]->(t:Topic) WHERE toLower(t.name) CONTAINS 'keyword'
- Find researcher's work: MATCH (r:Researcher {{name: "Name"}})-[:PUBLISHED]->(a) RETURN a.title

Question: "{question}"

Cypher Query:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a Neo4j Cypher query expert. Generate only valid, executable Cypher queries. Be precise with syntax."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=300
            )

            cypher = response.choices[0].message.content.strip()
            cypher = cypher.replace("```cypher", "").replace("```", "").strip()

            return {
                "success": True,
                "cypher": cypher,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "cypher": None,
                "error": str(e)
            }

    def execute_text_to_cypher(self, question: str) -> Dict[str, Any]:
        """Generate Cypher from text and execute it."""
        start_time = time.time()

        cypher_result = self.text_to_cypher(question)

        if not cypher_result['success']:
            return {
                "success": False,
                "error": f"Failed to generate Cypher: {cypher_result['error']}",
                "time": time.time() - start_time
            }

        cypher = cypher_result['cypher']

        try:
            results = self.execute_query(cypher)

            # Try to extract graph visualization data
            graph_data = self._extract_graph_from_results(results, cypher)

            return {
                "success": True,
                "cypher": cypher,
                "results": results,
                "result_count": len(results),
                "graph_data": graph_data,
                "time": time.time() - start_time,
                "error": None
            }

        except Exception as e:
            return {
                "success": False,
                "cypher": cypher,
                "results": [],
                "result_count": 0,
                "graph_data": {"nodes": [], "relationships": []},
                "time": time.time() - start_time,
                "error": f"Cypher execution error: {str(e)}"
            }

    def _extract_graph_from_results(self, results: List[Dict], cypher: str) -> Dict[str, Any]:
        """
        Extract graph visualization data from query results.
        Attempts to identify nodes and relationships from the data.
        """
        nodes_dict = {}
        relationships_list = []

        try:
            # Try to identify entity names from results and fetch their graph structure
            entity_names = set()

            for result in results:
                for key, value in result.items():
                    if isinstance(value, str) and value:
                        entity_names.add(value)
                    elif isinstance(value, list):
                        for item in value:
                            if isinstance(item, str) and item:
                                entity_names.add(item)

            # If we found entity names, try to fetch their graph structure
            if entity_names and len(entity_names) < 50:
                # Limit to first 20 entities to avoid huge queries
                entity_names = list(entity_names)[:20]

                # Simplified approach: Find researchers and their immediate neighborhood
                graph_query = """
                // Find researchers by name
                MATCH (r:Researcher)
                WHERE r.name IN $names

                // Get their published articles
                OPTIONAL MATCH (r)-[pub:PUBLISHED]->(a:Article)

                // Get topics for these articles
                OPTIONAL MATCH (a)-[in_topic:IN_TOPIC]->(t:Topic)

                // Get co-authors (other researchers who published the same articles)
                OPTIONAL MATCH (a)<-[pub2:PUBLISHED]-(co_author:Researcher)
                WHERE co_author <> r

                // Collect all nodes and relationships
                WITH collect(DISTINCT r) + collect(DISTINCT a) + collect(DISTINCT t) + collect(DISTINCT co_author) as all_nodes,
                     collect(DISTINCT pub) + collect(DISTINCT in_topic) + collect(DISTINCT pub2) as all_rels

                // Return formatted data
                RETURN
                    [node in all_nodes WHERE node IS NOT NULL | {
                        id: id(node),
                        label: head(labels(node)),
                        properties: properties(node)
                    }] as nodes,
                    [rel in all_rels WHERE rel IS NOT NULL | {
                        source: id(startNode(rel)),
                        target: id(endNode(rel)),
                        type: type(rel)
                    }] as relationships
                """

                graph_results = self.execute_query(graph_query, {"names": entity_names})

                if graph_results and len(graph_results) > 0 and graph_results[0]:
                    # Process nodes
                    for node in graph_results[0].get('nodes', []):
                        if node and node.get('id') is not None:
                            nodes_dict[node['id']] = node

                    # Process relationships
                    for rel in graph_results[0].get('relationships', []):
                        if rel and rel.get('source') is not None and rel.get('target') is not None:
                            # Only include relationships where both nodes exist
                            if rel['source'] in nodes_dict and rel['target'] in nodes_dict:
                                relationships_list.append(rel)

                # If no nodes found yet, try finding by article titles
                if not nodes_dict:
                    article_query = """
                    // Find articles by title
                    MATCH (a:Article)
                    WHERE a.title IN $names

                    // Get their authors and topics
                    OPTIONAL MATCH (r:Researcher)-[pub:PUBLISHED]->(a)
                    OPTIONAL MATCH (a)-[in_topic:IN_TOPIC]->(t:Topic)

                    // Collect all nodes and relationships
                    WITH collect(DISTINCT a) + collect(DISTINCT r) + collect(DISTINCT t) as all_nodes,
                         collect(DISTINCT pub) + collect(DISTINCT in_topic) as all_rels

                    // Return formatted data
                    RETURN
                        [node in all_nodes WHERE node IS NOT NULL | {
                            id: id(node),
                            label: head(labels(node)),
                            properties: properties(node)
                        }] as nodes,
                        [rel in all_rels WHERE rel IS NOT NULL | {
                            source: id(startNode(rel)),
                            target: id(endNode(rel)),
                            type: type(rel)
                        }] as relationships
                    """

                    article_results = self.execute_query(article_query, {"names": entity_names})

                    if article_results and len(article_results) > 0 and article_results[0]:
                        for node in article_results[0].get('nodes', []):
                            if node and node.get('id') is not None:
                                nodes_dict[node['id']] = node

                        for rel in article_results[0].get('relationships', []):
                            if rel and rel.get('source') is not None and rel.get('target') is not None:
                                if rel['source'] in nodes_dict and rel['target'] in nodes_dict:
                                    relationships_list.append(rel)

        except Exception as e:
            # If extraction fails, log and return empty graph
            print(f"Debug: Graph extraction failed: {str(e)}")
            pass

        return {
            'nodes': list(nodes_dict.values()),
            'relationships': relationships_list
        }

    def format_kg_results(self, results: List[Dict]) -> str:
        """Format KG results into readable text."""
        if not results:
            return "No results found."

        formatted = []
        for i, row in enumerate(results[:20], 1):
            row_text = f"Result {i}:"
            for key, value in row.items():
                if isinstance(value, list):
                    value = ", ".join(str(v) for v in value[:5])
                row_text += f"\n  • {key}: {value}"
            formatted.append(row_text)

        return "\n\n".join(formatted)

    def kg_query_with_explanation(self, question: str) -> Dict[str, Any]:
        """Execute KG query and generate natural language explanation."""
        start_time = time.time()

        kg_result = self.execute_text_to_cypher(question)

        if not kg_result['success']:
            return {
                "method": "Knowledge Graph (Text-to-Cypher)",
                "success": False,
                "error": kg_result['error'],
                "answer": f"Failed to query knowledge graph: {kg_result['error']}",
                "time": time.time() - start_time
            }

        formatted_results = self.format_kg_results(kg_result['results'])

        explanation_prompt = f"""You are explaining database query results to a user.

Question: {question}

Cypher Query Used:
{kg_result['cypher']}

Query Results:
{formatted_results}

Provide a clear, natural language answer based on these EXACT results. Be specific with numbers and names from the data. If there are no results, say so clearly.

Answer:"""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that explains database query results clearly and accurately."},
                    {"role": "user", "content": explanation_prompt}
                ],
                temperature=0.7,
                max_tokens=500
            )

            answer = response.choices[0].message.content

        except Exception as e:
            answer = f"Found {kg_result['result_count']} results, but failed to generate explanation: {str(e)}"

        return {
            "method": "Knowledge Graph (Text-to-Cypher)",
            "success": True,
            "cypher": kg_result['cypher'],
            "results": kg_result['results'],
            "result_count": kg_result['result_count'],
            "formatted_results": formatted_results,
            "answer": answer,
            "graph_data": kg_result.get('graph_data', {"nodes": [], "relationships": []}),
            "time": time.time() - start_time
        }

    # ============================================
    # LLM JUDGE COMPARISON
    # ============================================

    def compare_with_judge(self, question: str) -> Dict[str, Any]:
        """
        Use LLM to judge which method (RAG vs KG) gave a better answer.

        This provides objective evaluation of both approaches.
        """
        print("\n" + "⚖️ " * 40)
        print("LLM JUDGE: Comparing RAG vs Knowledge Graph")
        print("⚖️ " * 40)
        print(f"\nQuestion: {question}\n")

        # Get both results
        print("🔄 Getting RAG answer...")
        rag_result = self.query(question, use_vector_search=False)

        print("🔄 Getting Knowledge Graph answer...")
        kg_result = self.kg_query_with_explanation(question)

        # Display both answers
        print("\n" + "=" * 80)
        print("📚 RAG ANSWER:")
        print("-" * 80)
        print(rag_result['answer'])
        print(f"⏱️  Time: {rag_result['time']:.2f}s")
        print(f"📄 Sources: {len(rag_result['sources'])} documents")

        print("\n" + "=" * 80)
        print("🔍 KNOWLEDGE GRAPH ANSWER:")
        print("-" * 80)
        if kg_result['success']:
            print(f"Cypher: {kg_result['cypher']}")
            print(f"\n{kg_result['answer']}")
            print(f"⏱️  Time: {kg_result['time']:.2f}s")
            print(f"📊 Results: {kg_result['result_count']} exact matches")
        else:
            print(f"❌ Failed: {kg_result['error']}")

        # If KG failed, RAG wins by default
        if not kg_result['success']:
            print("\n" + "🏆" * 40)
            print("WINNER: RAG (Knowledge Graph query failed)")
            print("🏆" * 40)
            return {
                "question": question,
                "winner": "RAG",
                "reason": "Knowledge Graph query failed",
                "rag_result": rag_result,
                "kg_result": kg_result,
                "judgment": None
            }

        # Ask LLM to judge
        print("\n🤔 Asking LLM judge to evaluate...")

        judgment_prompt = f"""You are an expert judge evaluating two AI systems answering the same question.

Question: "{question}"

SYSTEM A (RAG - Retrieval-Augmented Generation):
Answer: {rag_result['answer']}
Method: Retrieved {len(rag_result['sources'])} relevant documents and generated answer using LLM
Time: {rag_result['time']:.2f}s

SYSTEM B (Knowledge Graph with Text-to-Cypher):
Cypher Query: {kg_result['cypher']}
Answer: {kg_result['answer']}
Method: Generated structured database query and retrieved {kg_result['result_count']} exact results
Time: {kg_result['time']:.2f}s
Raw Results: {kg_result['formatted_results'][:500]}...

Evaluation Criteria:
1. **Accuracy**: Which answer is more factually correct?
2. **Completeness**: Which answer provides more complete information?
3. **Precision**: Which answer is more specific and exact?
4. **Verifiability**: Which answer can be verified/proven?
5. **Usefulness**: Which answer better serves the user's intent?

Provide your evaluation in the following JSON format:
{{
    "winner": "A" or "B" or "TIE",
    "confidence": "high" or "medium" or "low",
    "accuracy_score_a": 1-10,
    "accuracy_score_b": 1-10,
    "completeness_score_a": 1-10,
    "completeness_score_b": 1-10,
    "precision_score_a": 1-10,
    "precision_score_b": 1-10,
    "reasoning": "Detailed explanation of your judgment",
    "strengths_a": ["strength 1", "strength 2"],
    "strengths_b": ["strength 1", "strength 2"],
    "weaknesses_a": ["weakness 1", "weakness 2"],
    "weaknesses_b": ["weakness 1", "weakness 2"],
    "recommendation": "When to use each method for this type of question"
}}

Be objective and thorough in your analysis."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an expert AI judge evaluating different question-answering systems. Be objective, thorough, and fair in your evaluations."},
                    {"role": "user", "content": judgment_prompt}
                ],
                temperature=0.0,
                seed=42,
                max_tokens=1000
            )

            judgment_text = response.choices[0].message.content.strip()

            # Try to parse JSON
            try:
                if "```json" in judgment_text:
                    judgment_text = judgment_text.split("```json")[1].split("```")[0].strip()
                elif "```" in judgment_text:
                    judgment_text = judgment_text.split("```")[1].split("```")[0].strip()

                judgment = json.loads(judgment_text)
            except json.JSONDecodeError:
                judgment = {"raw_text": judgment_text}

        except Exception as e:
            print(f"❌ Error getting LLM judgment: {e}")
            judgment = {"error": str(e)}

        # Display judgment
        print("\n" + "🏆" * 40)
        print("LLM JUDGE VERDICT")
        print("🏆" * 40)

        if "error" in judgment:
            print(f"❌ Error: {judgment['error']}")
        elif "raw_text" in judgment:
            print(judgment['raw_text'])
        else:
            winner_map = {"A": "RAG", "B": "Knowledge Graph", "TIE": "TIE"}
            winner = winner_map.get(judgment.get('winner', 'UNKNOWN'), 'UNKNOWN')

            print(f"\n🎯 WINNER: {winner}")
            print(f"📊 Confidence: {judgment.get('confidence', 'unknown').upper()}")

            print(f"\n📈 Scores:")
            print(f"  RAG:")
            print(f"    • Accuracy: {judgment.get('accuracy_score_a', 'N/A')}/10")
            print(f"    • Completeness: {judgment.get('completeness_score_a', 'N/A')}/10")
            print(f"    • Precision: {judgment.get('precision_score_a', 'N/A')}/10")

            print(f"  Knowledge Graph:")
            print(f"    • Accuracy: {judgment.get('accuracy_score_b', 'N/A')}/10")
            print(f"    • Completeness: {judgment.get('completeness_score_b', 'N/A')}/10")
            print(f"    • Precision: {judgment.get('precision_score_b', 'N/A')}/10")

            print(f"\n💭 Reasoning:")
            print(f"  {judgment.get('reasoning', 'No reasoning provided')}")

            if judgment.get('strengths_a'):
                print(f"\n✅ RAG Strengths:")
                for strength in judgment['strengths_a']:
                    print(f"  • {strength}")

            if judgment.get('strengths_b'):
                print(f"\n✅ Knowledge Graph Strengths:")
                for strength in judgment['strengths_b']:
                    print(f"  • {strength}")

            if judgment.get('weaknesses_a'):
                print(f"\n⚠️  RAG Weaknesses:")
                for weakness in judgment['weaknesses_a']:
                    print(f"  • {weakness}")

            if judgment.get('weaknesses_b'):
                print(f"\n⚠️  Knowledge Graph Weaknesses:")
                for weakness in judgment['weaknesses_b']:
                    print(f"  • {weakness}")

            if judgment.get('recommendation'):
                print(f"\n💡 Recommendation:")
                print(f"  {judgment['recommendation']}")

        print("\n" + "=" * 80)

        return {
            "question": question,
            "winner": judgment.get('winner'),
            "confidence": judgment.get('confidence'),
            "judgment": judgment,
            "rag_result": rag_result,
            "kg_result": kg_result
        }

    def get_graph_data(self, limit: int = 50) -> Dict[str, Any]:
        """
        Get graph data for visualization.

        Args:
            limit: Maximum number of nodes to include

        Returns:
            Dictionary with nodes and relationships
        """
        query = f"""
        MATCH (n)
        WITH n LIMIT {limit}
        OPTIONAL MATCH (n)-[r]->(m)
        RETURN
            collect(DISTINCT {{
                id: id(n),
                label: head(labels(n)),
                properties: properties(n)
            }}) as nodes,
            collect(DISTINCT {{
                source: id(startNode(r)),
                target: id(endNode(r)),
                type: type(r)
            }}) as relationships
        """

        result = self.execute_query(query)

        if result and result[0]:
            # Get all unique nodes
            nodes_set = {}
            relationships_list = []

            # Add nodes from the first result
            for node in result[0].get('nodes', []):
                if node and node.get('id') is not None:
                    nodes_set[node['id']] = node

            # Add relationships
            for rel in result[0].get('relationships', []):
                if rel and rel.get('source') is not None and rel.get('target') is not None:
                    relationships_list.append(rel)

            return {
                'nodes': list(nodes_set.values()),
                'relationships': relationships_list
            }

        return {'nodes': [], 'relationships': []}


# ============================================
# STANDALONE HELPER FUNCTIONS
# ============================================

def quick_ask_with_judge(question: str):
    """Quick function to ask a question and get LLM judgment."""
    rag = Neo4jGraphRAG()

    # Check if data exists
    count = rag.execute_query("MATCH (n) RETURN count(n) as count")
    if count[0]['count'] == 0:
        print("📥 Loading data first...")
        rag.load_data('https://raw.githubusercontent.com/dcarpintero/generative-ai-101/main/dataset/synthetic_articles.csv')

        # Check if embeddings exist
        emb_count = rag.execute_query("MATCH (a:Article) WHERE a.embedding IS NOT NULL RETURN count(a) as count")
        if emb_count[0]['count'] == 0:
            print("🔢 Creating embeddings...")
            rag.create_embeddings_for_articles()

    result = rag.compare_with_judge(question)
    rag.close()
    return result


def batch_judge_questions(questions: List[str]):
    """Judge multiple questions and show aggregate statistics."""
    print("\n" + "🎯" * 40)
    print("BATCH LLM JUDGMENT - Multiple Questions")
    print("🎯" * 40)

    rag = Neo4jGraphRAG()

    # Check/load data
    count = rag.execute_query("MATCH (n) RETURN count(n) as count")
    if count[0]['count'] == 0:
        print("📥 Loading data...")
        rag.load_data('https://raw.githubusercontent.com/dcarpintero/generative-ai-101/main/dataset/synthetic_articles.csv')
        print("🔢 Creating embeddings...")
        rag.create_embeddings_for_articles()

    results = []
    for i, question in enumerate(questions, 1):
        print(f"\n{'='*80}")
        print(f"Question {i}/{len(questions)}")
        print(f"{'='*80}")

        result = rag.compare_with_judge(question)
        results.append(result)

        if i < len(questions):
            time.sleep(1)

    # Aggregate statistics
    print("\n" + "📊" * 40)
    print("AGGREGATE STATISTICS")
    print("📊" * 40)

    rag_wins = sum(1 for r in results if r.get('winner') == 'A')
    kg_wins = sum(1 for r in results if r.get('winner') == 'B')
    ties = sum(1 for r in results if r.get('winner') == 'TIE')

    print(f"\n🏆 Overall Results:")
    print(f"  • RAG Wins: {rag_wins}/{len(questions)} ({rag_wins/len(questions)*100:.1f}%)")
    print(f"  • Knowledge Graph Wins: {kg_wins}/{len(questions)} ({kg_wins/len(questions)*100:.1f}%)")
    print(f"  • Ties: {ties}/{len(questions)} ({ties/len(questions)*100:.1f}%)")

    # Average scores
    rag_accuracy = [r['judgment'].get('accuracy_score_a', 0) for r in results if 'judgment' in r and r['judgment'] and isinstance(r['judgment'].get('accuracy_score_a'), (int, float))]
    kg_accuracy = [r['judgment'].get('accuracy_score_b', 0) for r in results if 'judgment' in r and r['judgment'] and isinstance(r['judgment'].get('accuracy_score_b'), (int, float))]

    if rag_accuracy and kg_accuracy:
        print(f"\n📈 Average Accuracy Scores:")
        print(f"  • RAG: {sum(rag_accuracy)/len(rag_accuracy):.1f}/10")
        print(f"  • Knowledge Graph: {sum(kg_accuracy)/len(kg_accuracy):.1f}/10")

    # Question type analysis
    print(f"\n🔍 Question Type Analysis:")
    for i, (question, result) in enumerate(zip(questions, results), 1):
        winner_name = {"A": "RAG", "B": "KG", "TIE": "TIE"}.get(result.get('winner'), '?')
        print(f"  {i}. {question[:60]}...")
        print(f"     Winner: {winner_name}")

    print("\n" + "=" * 80)

    rag.close()
    return results


# ============================================
# MAIN EXECUTION
# ============================================

if __name__ == "__main__":
    print("=" * 80)
    print("RAG vs Knowledge Graph Evaluation System")
    print("=" * 80)
    print("\nLearn more about building advanced multi-agent systems:")
    print("🎓 https://maven.com/boring-bot/advanced-llm?promoCode=200OFF")
    print("=" * 80)

    # Example: Single question with judgment
    print("\n\nExample: Single Question Evaluation")
    quick_ask_with_judge("Who are the collaborators of Emily Chen?")
