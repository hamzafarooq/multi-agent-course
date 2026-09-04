# AI Evaluation Metrics

> Part of **Module 3 — Production Agentic RAG & AI Systems**: the "how do we know our AI actually works?" track. Evaluation and guardrails come back in Module 4 (observability & debugging for multi-agent systems) and Module 5 (evaluating voice agents).

This notebook is a **plain-English tour of the evaluation metrics** used across every type of AI
system — from a single LLM call all the way up to a multi-agent workflow. It answers one question:
*how do we know if our AI is actually working?*

**No coding experience needed.** Every metric is explained with a real product scenario, and the
code cells just do the arithmetic so you can see the numbers move. The goal is to build the mental
model, not to ship eval infrastructure.

## Notebook

| Notebook | Open in Colab |
|---|---|
| [`AI_Eval_Metrics.ipynb`](AI_Eval_Metrics.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/modules/Module_3_Production_Agentic_RAG_AI_Systems/Evaluation_and_Guardrails/AI_Eval_Metrics.ipynb) |

---

## The eval hierarchy

The metrics stack into a pyramid — each layer builds on the one below it, and a weakness low down
undermines everything above. The notebook is organized around this funnel:

```
   5. Can we trust the system end-to-end?  → Agent Evaluation      ← most complex
   4. Can we trust the generated output?   → RAG Generation
   3. Can we trust the data source?        → RAG Retrieval
   2. Can we trust the reasoning?          → LLM Reasoning
   1. Can we trust the answer?             → LLM Quality           ← foundational
```

Not every product needs all five layers. A simple chatbot lives mostly in layers 1–2; a RAG
assistant adds 3–4; an autonomous agent needs all five.

---

## What's covered

### Section 1 — LLM Evaluation

| Group | Metrics |
|---|---|
| **LLM Quality** — *"is the answer good?"* | Correctness, Hallucination Rate, BLEU, Response Latency, Instruction Following, Completeness, Clarity |
| **LLM Reasoning** — *"is the thinking sound?"* | Chain-of-Thought Faithfulness, Step Accuracy, Tool Selection Accuracy, Decision Latency |
| **Efficiency & Optimization** — *"at what cost?"* | Perplexity, Quantization impact (FP16 / INT8 / INT4), KV Caching impact |

### Section 2 — Retrieval & Generation (RAG)

| Group | Metrics |
|---|---|
| **Retrieval** — *"did we find the right docs?"* | Precision@K, Recall@K, Mean Reciprocal Rank (MRR) |
| **Generation** — *"did we use them well?"* | Faithfulness / Groundedness, Answer Relevance, Context Utilisation |

### Section 3 — Agent Evaluation

| System type | Metrics |
|---|---|
| **Autonomous agent** | Task Success Rate, Tool Use Accuracy, Trajectory Efficiency, Safety & Guardrail Compliance |
| **ReAct agent** | Tool Use Accuracy, Trajectory Efficiency, Step Reasoning Accuracy, Observation Utilization, Loop Termination Correctness |
| **Multi-agent system** | Task Success Rate, Coordination Score, Error Propagation Rate, End-to-End Latency |

The notebook closes with a **summary dashboard** and a **PM decision guide** mapping feature types to
the metrics that matter most for each.

---

## How to read each metric

Every metric in the notebook follows the same template, so you can skim quickly:

- **Plain English** — what it measures in one sentence.
- **Example scenario** — a concrete product situation (medical FAQ bot, refund policy, booking agent…).
- **How it's measured** — the calculation or the judging approach (gold-standard comparison, AI judge, formula).
- **PM caveat** — the trap to watch for (e.g. low perplexity ≠ factual correctness).
- **Best used for** — the feature types where the metric earns its keep.

---

## Setup

There's nothing to install. The notebook uses only the Python standard library
(`math`, `collections`, `random`, `time`) to illustrate the math — no API keys, no model downloads,
no external services. Open it in Colab (badge above) or run it locally with any Python 3 kernel.

---

This notebook teaches the *vocabulary* of evaluation. For the safety layer that sits in front of a
production system — classifying inputs and outputs against a policy — see the Guardrails material
(Llama Guard) referenced in the module.
