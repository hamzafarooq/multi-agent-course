# Workflow Guide

## 🚀 Getting Started (3 Simple Steps)

### Step 1: Setup (Only Once)

Run the setup script to initialize everything:

```bash
python setup.py
```

**What this does:**
- ✅ Checks your environment variables
- ✅ Tests Neo4j connection
- ✅ Loads dataset (~50 articles)
- ✅ Creates embeddings for semantic search
- ✅ Verifies queries work

**Time:** 2-3 minutes on first run

---

### Step 2: Launch the App

```bash
streamlit run app.py
```

**Or use the quick launcher:**
```bash
./run_app.sh    # macOS/Linux
run_app.bat     # Windows
```

**Time:** 5 seconds

---

### Step 3: Compare Approaches

1. **Select or type a question**
   - Use sample questions from sidebar
   - Or type your own

2. **Click "Compare Both"**
   - Wait 10-15 seconds for processing

3. **View results**
   - RAG answer
   - Knowledge Graph answer
   - LLM judge verdict
   - Visual comparison

---

## 📊 Workflow Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                     FIRST TIME ONLY                          │
│                                                              │
│  1. Edit .env file with credentials                         │
│  2. Run: python setup.py                                    │
│  3. Wait 2-3 minutes for setup to complete                  │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                    EVERY TIME YOU USE                        │
│                                                              │
│  1. Run: streamlit run app.py                               │
│  2. Open browser to http://localhost:8501                   │
│  3. Enter question                                           │
│  4. Click "Compare Both"                                     │
│  5. View results                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔄 Data Flow

```
Question Input
     │
     ▼
┌────────────────────────────┐
│  Streamlit App (app.py)    │
│                            │
│  - User Interface          │
│  - Progress Tracking       │
│  - Results Display         │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  Helper (streamlit_helper) │
│                            │
│  - Orchestrates queries    │
│  - No console output       │
│  - Clean results           │
└────────────┬───────────────┘
             │
             ├─────────────────┐
             │                 │
             ▼                 ▼
┌──────────────────┐  ┌──────────────────┐
│   RAG System     │  │  Knowledge Graph │
│                  │  │                  │
│  - Keyword       │  │  - Text-to-      │
│    Search        │  │    Cypher        │
│  - Embeddings    │  │  - Neo4j Query   │
│  - GPT-4o-mini   │  │  - GPT-4o-mini   │
└─────────┬────────┘  └────────┬─────────┘
          │                    │
          └─────────┬──────────┘
                    │
                    ▼
          ┌─────────────────┐
          │   LLM Judge     │
          │                 │
          │  - GPT-4o-mini  │
          │  - Comparison   │
          │  - Scores       │
          └────────┬────────┘
                   │
                   ▼
           ┌───────────────┐
           │ Results       │
           │               │
           │ - Winner      │
           │ - Scores      │
           │ - Reasoning   │
           └───────────────┘
```

---

## 🎯 Question Types & Expected Winners

### Knowledge Graph Wins ✅
- Counting queries: *"How many researchers published?"*
- Relationship queries: *"Who collaborated with X?"*
- Filtering queries: *"Show papers from 2024"*
- Multi-hop queries: *"Find colleagues of colleagues"*

### RAG Wins ✅
- Semantic queries: *"What are the challenges in AI safety?"*
- Summarization: *"Explain innovations in transformers"*
- Conceptual questions: *"What are ethical concerns?"*
- Interpretive queries: *"Compare approaches to X"*

### Both Useful 🤝
- Topic queries: *"What topics does Emily research?"*
- Mixed queries: *"Compare researchers' focus areas"*

---

## ⚙️ System Requirements

**Minimum:**
- Python 3.8+
- 2GB RAM
- Internet connection

**Accounts Needed:**
- Neo4j Aura (free tier)
- OpenAI API (pay-as-you-go)

**Estimated Costs:**
- Neo4j: Free
- OpenAI: ~$0.05-0.10 per comparison

---

## 🔧 Troubleshooting

### "No data found"
→ Run `python setup.py` first

### "Connection refused"
→ Check `.env` credentials and Neo4j instance

### "OpenAI error"
→ Verify API key and account credits

### Slow performance
→ Normal on first run (loading data + embeddings)

---

## 📚 Learn More

Want to build systems like this?

**[Advanced LLM Multi-Agent Architecture Course](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)**

Learn:
- Multi-agent orchestration
- RAG + Knowledge Graph hybrids
- Production deployment
- Evaluation frameworks

**Use code `200OFF` for $200 off!**

---

**Happy comparing! 🚀**
