# Quick Start Guide - Streamlit App

Get up and running with the RAG vs Knowledge Graph web app in 5 minutes!

## 📋 Prerequisites

Before you start, make sure you have:

1. ✅ Python 3.8 or higher installed
2. ✅ A Neo4j Aura account (free tier available at [neo4j.com/cloud/aura](https://neo4j.com/cloud/aura/))
3. ✅ An OpenAI API key (get one at [platform.openai.com/api-keys](https://platform.openai.com/api-keys))

## 🚀 Step-by-Step Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `streamlit` - Web app framework
- `neo4j` - Neo4j database driver
- `openai` - OpenAI API client
- `plotly` - Interactive charts
- `python-dotenv` - Environment variable management

### Step 2: Configure Environment Variables

Edit the `.env` file with your credentials:

```env
NEO4J_URI=neo4j+s://your-instance.databases.neo4j.io
NEO4J_USERNAME=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=neo4j
OPENAI_API_KEY=your-openai-api-key-here
```

**How to get your Neo4j credentials:**
1. Log into [Neo4j Aura](https://console.neo4j.io/)
2. Create or select a database instance
3. Copy the connection URI, username, and password

**How to get your OpenAI API key:**
1. Log into [OpenAI Platform](https://platform.openai.com/)
2. Navigate to API Keys section
3. Create a new API key
4. Copy and paste it into your `.env` file

### Step 3: Launch the App

**Option A: Quick Launch (Easiest)**

macOS/Linux:
```bash
./run_app.sh
```

Windows:
```bash
run_app.bat
```

**Option B: Manual Launch**

```bash
streamlit run app.py
```

### Step 4: Open in Browser

The app will automatically open in your default browser at:
```
http://localhost:8501
```

If it doesn't open automatically, just paste that URL into your browser.

## 🎯 First-Time Usage

### 1. Initialize the System

When you first open the app:

1. Look at the **left sidebar**
2. Click the **"🚀 Initialize System"** button
3. Wait for the system to:
   - Connect to Neo4j
   - Load the sample dataset
   - Create embeddings for articles

This takes about 1-2 minutes on first run.

### 2. Ask Your First Question

Once initialized:

1. Look at the **Sample Questions** dropdown in the sidebar
2. Select a question like *"Who are the collaborators of Emily Chen?"*
3. Click the **"⚖️ Compare Both"** button
4. Watch the progress bar as it:
   - Gets the RAG answer
   - Gets the Knowledge Graph answer
   - Runs the LLM judge evaluation

### 3. Explore the Results

You'll see:

- **Side-by-side comparison** of RAG vs Knowledge Graph answers
- **LLM Judge Verdict** with winner and confidence level
- **Detailed scores** for accuracy, completeness, and precision
- **Visual radar chart** comparing both approaches
- **Judge's reasoning** explaining the decision
- **Strengths & weaknesses** of each method
- **Recommendations** for when to use each approach

### 4. Try More Questions

You can:

- Type your own questions in the input field
- Try different sample questions
- Toggle "Show Details" to see:
  - Retrieved context (RAG)
  - Cypher queries (Knowledge Graph)
  - Raw results

## 💡 Sample Questions to Try

### RAG Should Win:
- "What are the main challenges in AI safety?"
- "Explain innovations in transformer architectures"
- "Summarize ethical concerns in AI research"

### Knowledge Graph Should Win:
- "Who are the collaborators of Emily Chen?"
- "How many articles has each researcher published?"
- "Which researchers work on AI Ethics?"

### Mixed Results:
- "What topics does Emily Chen research?"
- "Compare the research focus of Emily Chen vs Michael Brown"

## 🔧 Troubleshooting

### Issue: "Module not found" errors

**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

### Issue: "Connection refused" to Neo4j

**Solution:** Check your Neo4j credentials in `.env`
- Make sure your Neo4j instance is running
- Verify the URI starts with `neo4j+s://`
- Check username and password are correct

### Issue: "OpenAI API error"

**Solution:** Check your API key
- Verify your API key in `.env` is correct
- Make sure you have credits in your OpenAI account
- Check the key hasn't been revoked

### Issue: App won't start

**Solution:** Check Python version
```bash
python --version  # Should be 3.8 or higher
```

If using Python 3.7 or lower, upgrade to 3.8+

### Issue: Slow performance

**Solution:** This is normal on first run
- First time: 1-2 minutes (loading data + creating embeddings)
- Subsequent runs: Much faster (data is cached)

## 🎓 Learn More

Want to master building systems like this?

**[Join the Advanced LLM Multi-Agent Architecture Course](https://maven.com/boring-bot/advanced-llm?promoCode=200OFF)**

Learn to build:
- Production-ready RAG systems
- Knowledge Graph integrations
- Multi-agent orchestration
- Evaluation frameworks
- And much more!

**Use code `200OFF` for $200 off!**

## 📚 Additional Resources

- **Full Documentation:** See [README.md](README.md)
- **Feature Guide:** See [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md)
- **Python API:** See [knowledge_graph_rag_comparison.py](knowledge_graph_rag_comparison.py)
- **Sample Questions:** See [sample_questions.py](sample_questions.py)

## 🆘 Need Help?

- Check the [README.md](README.md) for detailed documentation
- Review [STREAMLIT_FEATURES.md](STREAMLIT_FEATURES.md) for UI explanations
- Open an issue on GitHub
- Reach out to course instructors

---

**Happy Comparing! 🚀**

*Built with ❤️ for the AI community*
