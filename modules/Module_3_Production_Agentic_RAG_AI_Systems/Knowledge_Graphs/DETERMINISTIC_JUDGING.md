# Deterministic LLM Judge Configuration

## Problem

Users were experiencing inconsistent results between running the same question through:
1. `sample_questions.py` (batch evaluation)
2. Streamlit app (interactive evaluation)

**Example:**
- Question: "Which researchers work on the same topics as Emily Chen?"
- Result: Different winners on different runs or between different interfaces

## Root Cause

The LLM judge was using `temperature=0.3` which introduces randomness:

```python
# Previous configuration
temperature=0.3  # Allows for creative variation in responses
```

Even though both code paths used the same temperature, `0.3` still allows the LLM to give different answers to the same question, causing:
- Different winner declarations (RAG vs KG vs TIE)
- Varying confidence levels
- Different scores and reasoning

## Solution

Changed both evaluation paths to use deterministic settings:

```python
# New configuration
temperature=0.0  # Maximum determinism
seed=42          # Consistent random seed
```

### Files Updated

1. **`knowledge_graph_rag_comparison.py`** (line ~637)
   - Used by: `sample_questions.py`, Jupyter notebooks, direct Python scripts
   - Function: `compare_with_judge()`

2. **`streamlit_helper.py`** (line ~117)
   - Used by: Streamlit web app
   - Function: `get_llm_judgment()`

## How It Works

### Temperature Parameter

- **`temperature=0.0`**: Most deterministic
  - Model picks the highest probability token every time
  - Same input → same output (with same seed)
  - Best for reproducible evaluations

- **`temperature=0.3`**: Low creativity (previous setting)
  - Some variation allowed
  - Can produce different outputs for same input
  - Better for general use, worse for consistency

- **`temperature=0.7`**: Moderate creativity
  - Used for answer generation (RAG, KG explanations)
  - More natural and varied responses

### Seed Parameter

- **`seed=42`**: Ensures consistent random sampling
  - OpenAI uses this to initialize their sampling
  - Combined with `temperature=0.0`, provides maximum consistency
  - Note: OpenAI doesn't guarantee 100% determinism but this is close

## Expected Behavior Now

### Consistent Results
✅ Same question → same winner (across runs)
✅ Same confidence levels
✅ Same scores (accuracy, completeness, precision)
✅ Same reasoning and recommendations

### Between Interfaces
✅ `sample_questions.py` and Streamlit should give identical results
✅ Running the same question multiple times gives same answer
✅ Batch evaluations are reproducible

## When You Might Still See Differences

### Different Inputs
- RAG might retrieve different context if embeddings change
- KG might generate different Cypher if schema changes
- Timestamps or dynamic data can affect results

### OpenAI API Changes
- Model updates (even same model name)
- Backend changes at OpenAI
- Very rare but possible

### Different Contexts
- Running questions in different order (affects conversation state)
- Different data in the database
- Different environment variables

## Testing Consistency

Run the same question multiple times:

```bash
# Test 1: Streamlit
streamlit run app.py
# Enter: "Which researchers work on the same topics as Emily Chen?"
# Note the winner

# Test 2: Python script
python -c "
from knowledge_graph_rag_comparison import quick_ask_with_judge
result = quick_ask_with_judge('Which researchers work on the same topics as Emily Chen?')
print(f'Winner: {result[\"winner\"]}')
"

# Test 3: Batch questions
python sample_questions.py
```

All three should now give the same winner and scores.

## Trade-offs

### Benefits of temperature=0.0
✅ Reproducible results
✅ Consistent evaluations
✅ Easier to debug
✅ Better for benchmarking
✅ More trustworthy metrics

### Potential Downsides
⚠️ Less natural language variation
⚠️ Slightly more rigid reasoning
⚠️ Less exploration of edge cases

For evaluation purposes, consistency is more important than variation, so `temperature=0.0` is the right choice.

## Other Temperature Settings in the Codebase

These remain unchanged (intentionally):

1. **RAG Answer Generation** (`temperature=0.7`)
   - File: `knowledge_graph_rag_comparison.py`, line ~250
   - Reason: Want natural, varied explanations

2. **Text-to-Cypher** (`temperature=0.1`)
   - File: `knowledge_graph_rag_comparison.py`, line ~398
   - Reason: Need precise query generation, but some flexibility

3. **KG Explanation** (`temperature=0.7`)
   - File: `knowledge_graph_rag_comparison.py`, line ~509
   - Reason: Want natural language explanations of results

## Summary

The LLM judge now uses `temperature=0.0` and `seed=42` for maximum consistency across:
- Multiple runs of the same question
- Different interfaces (Streamlit vs scripts)
- Batch evaluations
- Time-separated queries

This ensures that evaluation results are reproducible and trustworthy while maintaining natural language quality in the actual RAG and KG answers.
