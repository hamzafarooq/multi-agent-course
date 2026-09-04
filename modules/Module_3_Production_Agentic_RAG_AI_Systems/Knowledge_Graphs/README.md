# RAG vs Knowledge Graph Evaluation Framework

A comprehensive system for comparing **Retrieval-Augmented Generation (RAG)** and **Knowledge Graph (KG)** approaches for question-answering systems.

Built with **Neo4j Aura** and **OpenAI GPT-4o-mini**, this framework provides objective, LLM-based evaluation to determine which approach works best for different types of questions.

**NEW:** Interactive query-specific graph visualizations show the exact data path used for each answer!

## Demo

See the Streamlit app in action:

https://github.com/user-attachments/assets/a749e811-d5ba-4b42-9772-056afe500b1e




*Full walkthrough: side-by-side RAG vs KG comparison, LLM judge evaluation, and interactive query-specific graph visualizations*

## What This Does

Three distinct query methods:

**1. RAG (Retrieval-Augmented Generation)**
- Uses semantic search or keyword matching to find relevant documents
- Passes retrieved context to an LLM for answer generation
- Best for: Natural language understanding, semantic queries, summarization

**2. Knowledge Graph with Text-to-Cypher**
- Converts natural language questions into Cypher queries using GPT-4o-mini
- Executes structured queries directly on Neo4j
- Best for: Precise counts, relationship queries, aggregations, filtering

**3. LLM Judge Evaluation**
- Uses GPT-4o-mini as an impartial evaluator
- Scores each method on accuracy, completeness, precision
- Produces detailed reasoning and recommendations

## Key Features

- No Hardcoded Queries — Cypher is generated dynamically from natural language
- Objective Evaluation — Unbiased LLM-based scoring system
- Interactive Visualizations — Dual graph views (full graph + query-specific)
- Production Ready — Graceful error handling, retry logic, logging
- Batch Evaluation — Evaluate many questions together

## When to Use Which Method

**Knowledge Graph Excels At:**
- "Who are the collaborators of Emily Chen?"
- "How many articles has each researcher published?"
- "Which researchers work on AI Ethics?"

**RAG Excels At:**
- "What are the main challenges in AI safety?"
- "Explain innovations in transformer architectures."
- "Summarize ethical concerns in AI research."

## Quick Start

### Prerequisites

- Python 3.8+ (3.10+ recommended)
- [Neo4j Aura](https://neo4j.com/cloud/aura/) free account
- [OpenAI API key](https://platform.openai.com/api-keys) (~$1 for full evaluation)

### Installation

```bash
# Clone and navigate
git clone https://github.com/yourusername/multi-agent-course.git
cd multi-agent-course/Module_4_Knowledge_Graphs

# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Create `.env` file:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-your-key-here
```

### Setup & Launch

**Step 1: Run setup (only once)**
```bash
python setup.py  # Loads data & creates embeddings
```

**Step 2: Launch Streamlit app**
```bash
streamlit run app.py
# Open http://localhost:8501
```

**Streamlit Features:**
- Beautiful minimal UI with side-by-side comparison
- Interactive Pyvis visualizations (drag, zoom, click)
- Radar charts and detailed metrics
- Query-specific graph visualization (shows exact data path)
- Pre-loaded sample questions

**Alternative: Python script**
```bash
python knowledge_graph_rag_comparison.py
```

**Alternative: Jupyter notebook**
```bash
jupyter notebook knowledge_graph_neo4j_with_evals.ipynb
```

## Code Examples

### Single Question with Judge

```python
from knowledge_graph_rag_comparison import quick_ask_with_judge

result = quick_ask_with_judge("Who are the collaborators of Emily Chen?")
```

### Batch Evaluation

```python
from knowledge_graph_rag_comparison import batch_judge_questions

questions = [
    "How many articles has each researcher published?",
    "What are the ethical concerns in AI?",
    "Which researchers work on Model Optimization?"
]

results = batch_judge_questions(questions)
```

### Custom Implementation

```python
from knowledge_graph_rag_comparison import Neo4jGraphRAG

rag = Neo4jGraphRAG()
rag.load_data('https://your-data-source.csv')
rag.create_embeddings_for_articles()
result = rag.compare_with_judge("Your question here")
rag.close()
```

## Interactive Graph Visualization

The Streamlit app includes two types of visualizations:

### 1. Full Graph Exploration
- Browse entire knowledge graph structure
- Color-coded nodes: Blue (Researchers), Green (Articles), Red (Topics)
- Interactive: drag, zoom, click for details
- Customizable: 20-50 nodes

### 2. Query-Specific Visualization (Fixed!)

Shows the exact subgraph used to answer your question.

After each Knowledge Graph answer, see:
- Relevant entities extracted from query results
- Their relationships and connections
- Complete graph traversal path

**Example:** "Who are Emily Chen's collaborators?" displays:
- Emily Chen node (center)
- Collaborator nodes
- Shared articles connecting them
- PUBLISHED relationships

**How it works:**
1. Question → Cypher query
2. Query executes on Neo4j
3. System extracts entity names from results
4. Fetches graph neighborhood (researchers → articles → topics → co-authors)
5. Renders interactive visualization

**Recent Fix:** Improved extraction algorithm to handle edge cases and empty collections, ensuring visualizations display reliably.

---

### 🎓 Want to Learn More?

Master advanced multi-agent systems, RAG, and Knowledge Graphs with our comprehensive bootcamp.

[**Agent Engineering Bootcamp - Save $200 with code 200OFF →**](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)

---

## Project Structure

```
Module_4_Knowledge_Graphs/
├── setup.py                                # First-time setup
├── app.py                                  # Streamlit web interface
├── streamlit_helper.py                     # Helper functions
├── knowledge_graph_rag_comparison.py       # Core implementation
├── sample_questions.py                     # Test question sets
├── requirements.txt                        # Dependencies
├── .env                                    # Your credentials (create this!)
└── README.md                               # This file
```

## Data Schema

**Nodes:**
- `Researcher` (name) — Research authors
- `Article` (title, abstract, publication_date, embedding) — Research papers
- `Topic` (name) — Research areas

**Relationships:**
- `(Researcher)-[:PUBLISHED]->(Article)` — Authorship
- `(Article)-[:IN_TOPIC]->(Topic)` — Categorization

## Troubleshooting

### Visualization Not Showing

**Cause:** Query returns aggregations (counts) without actual nodes.

**Solution:** Ask about specific entities:
- Good: "Who are Emily Chen's collaborators?"
- Poor: "How many collaborators does everyone have?"

Check terminal for: `Debug: Graph extraction failed: [details]`

### Common Issues

**"No data found"**
```bash
python setup.py  # Load dataset first
```

**"Failed to generate Cypher"**
- Check OpenAI API key is valid
- Ensure you have API credits

**"Connection timeout"**
- Verify Neo4j Aura instance is running
- URI should start with `neo4j+s://`

**"Embeddings not found"**
```bash
python setup.py  # Creates embeddings automatically
```

## Tips

**Writing effective questions:**
- For KG: Use specific names, ask "How many...", "Who are...", "Which..."
- For RAG: Ask for explanations, summaries, "What are the challenges..."

**Performance:**
- Start with 20-30 nodes for visualizations
- Use `batch_judge_questions()` for multiple queries
- Costs: ~$0.01-0.05 per query

**Extending:**
```python
# Use your own data
rag.load_data('https://your-domain.com/data.csv')
# Ensure CSV has: Title, Abstract, Authors, Topics, Publication_Date
```

## FAQ

**Q: Can I use my own data?**
A: Yes! Use `rag.load_data('your-data.csv')` with appropriate columns.

**Q: Do I need to pay for Neo4j?**
A: No, free tier supports 200K nodes (sufficient for this project).

**Q: How much does this cost?**
A: ~$0.50-$1.00 for full evaluation with OpenAI.

**Q: Can I use local models?**
A: Yes, but requires code modifications to replace OpenAI client calls.

**Q: Can I use on-premise Neo4j?**
A: Yes! Change URI in `.env` to `bolt://localhost:7687`.

**Q: Why use both RAG and KG?**
A: They excel at different tasks. This framework shows when to use which approach.

## Why This Matters

Most implementations choose either RAG or Knowledge Graphs. This framework shows **when to use which**, backed by objective LLM evaluations.

Ideal for:
- Building hybrid QA systems
- Understanding semantic vs. structured query trade-offs
- Making informed architectural decisions
- Demonstrating KG value vs pure LLM approaches
- Benchmarking different retrieval strategies

## Learn More

Want to master building advanced multi-agent systems?

<a href="https://maven.com/boring-bot/advanced-llm?promoCode=200OFF">
  <img src="course_img.png" alt="Agent Engineering Bootcamp" width="600">
</a>

### Agent Engineering Bootcamp: Developers Edition

**Rating:** ⭐⭐⭐⭐⭐ 4.8 (96 reviews)

**Instructor:** Hamza Farooq - Founder | Ex-Google | Prof UCLA & UMN

Master production-ready multi-agent systems, RAG, Knowledge Graphs, and advanced LLM architectures.

**Topics:**
- Multi-agent system design and orchestration
- RAG, Knowledge Graphs, and hybrid approaches
- Production-ready AI architecture patterns
- Evaluation frameworks and best practices

[**Enroll Now - Save $200 with code 200OFF**](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)

## Contributing

Contributions welcome! Ways to help:
- Add support for other graph databases (ArangoDB, TigerGraph)
- Enhance LLM judge prompts
- Add unit/integration tests
- Create tutorials or blog posts
- Translate documentation

[GitHub Repository](https://github.com/hamzafarooq/multi-agent-course)

## License

Apache 2.0 — free to use in your projects!

## Acknowledgments

Built with [Neo4j](https://neo4j.com/), [OpenAI](https://openai.com/), [Streamlit](https://streamlit.io/), [Pyvis](https://pyvis.readthedocs.io/), and [Plotly](https://plotly.com/).

Dataset adapted from [generative-ai-101](https://github.com/dcarpintero/generative-ai-101).

## Support

- **Issues:** [GitHub Issues](https://github.com/hamzafarooq/multi-agent-course/issues)
- **Course:** [Agent Engineering Bootcamp](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)

---

**Happy Evaluating!** 🚀

*Building the future of AI, one agent at a time.*
