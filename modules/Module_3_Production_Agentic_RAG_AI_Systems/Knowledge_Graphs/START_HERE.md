# 🚀 START HERE - Quick Setup Guide

## What You Have

A beautiful Streamlit web app that compares RAG vs Knowledge Graph approaches with visual results and LLM evaluation.

---

## ⚡ Quick Start (3 Commands)

### 1️⃣ Install Dependencies

```bash
cd "/Users/traversaal-001-hf/Dropbox/Mac (3)/Documents/Github/multi-agent-course/Module_4_Knowledge_Graphs"

pip install -r requirements.txt
```

---

### 2️⃣ Run Setup (IMPORTANT - Only Once!)

```bash
python setup.py
```

**What this does:**
- ✅ Checks your `.env` credentials are correct
- ✅ Tests Neo4j connection
- ✅ Loads dataset into Neo4j (~50 articles)
- ✅ Creates embeddings for articles
- ✅ Verifies everything works

**Time:** 2-3 minutes

**Output:** You'll see green checkmarks ✅ if everything works!

---

### 3️⃣ Launch the App

```bash
streamlit run app.py
```

**Or:**
```bash
./run_app.sh
```

The app will open automatically in your browser at `http://localhost:8501`

---

## 🎯 Using the App

1. **Wait for "System Ready"** message in sidebar
2. **Choose a sample question** from dropdown OR type your own
3. **Click "⚖️ Compare Both"**
4. **View results:**
   - RAG answer (left)
   - Knowledge Graph answer (right)
   - LLM Judge verdict (below)
   - Visual comparison chart

---

## 🆘 Troubleshooting

### Problem: "No data found in Neo4j database!"

**Solution:** You forgot to run setup!
```bash
python setup.py
```

---

### Problem: "Connection refused" or "Failed to connect to Neo4j"

**Solution:** Check your `.env` file has correct credentials:
```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-actual-password
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=sk-your-actual-key
```

Also verify your Neo4j instance is running at [console.neo4j.io](https://console.neo4j.io/)

---

### Problem: Knowledge Graph queries fail with emojis

**Solution:** This is a terminal display issue. The app itself works fine! You can:
1. Ignore the console output (it's just debug info)
2. Or use the cleaner Streamlit interface (recommended)

---

### Problem: "Module not found" errors

**Solution:** Install dependencies:
```bash
pip install -r requirements.txt
```

---

### Problem: OpenAI API errors

**Solution:**
1. Check your `OPENAI_API_KEY` in `.env` is valid
2. Verify you have credits: https://platform.openai.com/usage
3. Make sure key hasn't been revoked

---

## 📚 Files Explained

| File | Purpose |
|------|---------|
| `setup.py` ⭐ | **Run this first!** Loads data and creates embeddings |
| `app.py` | Streamlit web interface |
| `streamlit_helper.py` | Clean helper functions (no console spam) |
| `knowledge_graph_rag_comparison.py` | Core RAG & KG implementation |
| `sample_questions.py` | Pre-made question sets for testing |
| `.env` | Your credentials (keep this private!) |

---

## 🎨 What Makes This Special

✅ **No console spam** - Clean Streamlit interface
✅ **Pre-initialized data** - Setup runs once, app is fast
✅ **Beautiful UI** - Modern gradient design
✅ **Side-by-side comparison** - RAG vs KG clearly shown
✅ **LLM Judge** - Objective evaluation with scores
✅ **Visual charts** - Plotly radar charts
✅ **Sample questions** - Quick testing

---

## 🎓 Next Steps

1. ✅ Run `python setup.py` (if you haven't)
2. ✅ Launch `streamlit run app.py`
3. ✅ Try sample questions
4. ✅ Experiment with your own questions

---

## 📖 Learn More

**Want to master building systems like this?**

[Advanced LLM Multi-Agent Architecture Course](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)

Learn to build:
- Production RAG systems
- Knowledge Graph integrations
- Multi-agent orchestration
- Evaluation frameworks

**Use code `200OFF` for $200 off!**

---

## 📞 Need Help?

- Read [WORKFLOW.md](WORKFLOW.md) for detailed workflow
- Check [QUICKSTART_STREAMLIT.md](QUICKSTART_STREAMLIT.md) for setup details
- Review [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md) for UI guide
- See [README.md](README.md) for full documentation

---

**Happy Comparing! 🚀**

*Built with ❤️ for the AI community*
