"""
Streamlit Helper Functions
===========================

Clean wrapper functions for Streamlit that don't print to console.
"""

from knowledge_graph_rag_comparison import Neo4jGraphRAG
from typing import Dict, Any
import json
import os
from openai import OpenAI


def get_comparison_results(rag_system: Neo4jGraphRAG, question: str) -> Dict[str, Any]:
    """
    Get comparison results without console output.
    Streamlit-friendly version.
    """
    # Get RAG result
    rag_result = rag_system.query(question, use_vector_search=False)

    # Get Knowledge Graph result
    kg_result = rag_system.kg_query_with_explanation(question)

    # If KG failed, return early
    if not kg_result['success']:
        return {
            "question": question,
            "winner": "RAG",
            "reason": "Knowledge Graph query failed",
            "rag_result": rag_result,
            "kg_result": kg_result,
            "judgment": None
        }

    # Get LLM judgment (simplified, no console output)
    judgment = get_llm_judgment(question, rag_result, kg_result)

    return {
        "question": question,
        "winner": judgment.get('winner'),
        "confidence": judgment.get('confidence'),
        "judgment": judgment,
        "rag_result": rag_result,
        "kg_result": kg_result
    }


def get_llm_judgment(question: str, rag_result: Dict, kg_result: Dict) -> Dict:
    """Get LLM judgment without console output."""

    # Initialize OpenAI client with error handling
    try:
        openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    except TypeError as e:
        if 'proxies' in str(e):
            # Fallback: create client with explicit httpx client to bypass proxy issues
            import httpx
            http_client = httpx.Client(
                timeout=httpx.Timeout(60.0, connect=10.0),
                limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
            )
            openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"), http_client=http_client)
        else:
            raise

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
        response = openai_client.chat.completions.create(
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
            judgment = {"raw_text": judgment_text, "error": "Could not parse JSON"}

    except Exception as e:
        judgment = {"error": str(e)}

    return judgment
