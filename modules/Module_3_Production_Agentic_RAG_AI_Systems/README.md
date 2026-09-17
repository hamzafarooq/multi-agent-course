# Module 3 — Production Agentic RAG & AI Systems

This module teaches you how to build intelligent Retrieval-Augmented Generation (RAG) systems that **reason before they retrieve**. Rather than routing every query through a single static pipeline, you'll learn how to give your RAG system *agency* — the ability to choose the right knowledge source, optimize for speed with semantic caching, and handle time-sensitive queries with live web search. You'll also explore **Knowledge Graphs** as a structured retrieval backend and learn when graph-based retrieval beats vector search — the foundation of hybrid memory.

By the end of this module you will have built a full agentic RAG pipeline from scratch, plus a RAG-vs-Knowledge-Graph evaluation framework — all without relying on any external agentic framework (no LangChain, no LlamaIndex).

## Module 3 at a glance

![Module 3 mind map — Agentic RAG, Semantic Cache, Knowledge Graphs, and Moment RAG](module-3-mindmap.png)

Four moves toward **hybrid memory**: make retrieval **think** (Agentic RAG), make it **fast**
(Semantic Cache), make it **structured** (Knowledge Graphs), and make it **land on the exact
moment** (Moment RAG). Each is one folder below. A fifth folder,
[`Evaluation_and_Guardrails/`](Evaluation_and_Guardrails/), is how you **prove** any of it works —
the metrics for LLM, RAG, and agent quality, plus the guardrail layer that keeps it safe in production.

<details><summary>Text version</summary>

```text
MODULE 3 — Production Agentic RAG & AI Systems
│
├─ ① Agentic RAG        router (LLM) → Qdrant search → cited generation
├─ ② Semantic Cache     FAISS answer reuse · time-sensitivity guard · ~0.1s hits
├─ ③ Knowledge Graphs   Neo4j + text-to-Cypher · RAG vs KG · LLM judge
├─ ④ Moment RAG         decompose + HyDE + RRF · cross-encoder re-rank · click-to-play citations
└─ ⑤ Eval & Guardrails  the eval pyramid (LLM → RAG → agent metrics) · Llama Guard
```
</details>

> **✦ Latest addition — [`Moment_RAG/`](Moment_RAG/):** agentic RAG on *video*. Ask a complex question and get a streamed, cited answer where each citation pops up the source YouTube episode at the **exact moment**, with a synced transcript. It's decompose → hybrid retrieve (dense + BM25 + HyDE questions, RRF) → cross-encoder re-rank → cited synthesis. See the [Moment RAG README](Moment_RAG/README.md).

---

## What You'll Learn

- How to use an LLM as a **query router** to dynamically pick the right retrieval backend
- How to build and populate a **vector database** (Qdrant) from raw PDF documents
- How **semantic caching** works and why it dramatically reduces latency and cost
- How to detect and handle **time-sensitive queries** that must never be served from cache
- How to combine document retrieval, vector search, and live web search into one coherent pipeline
- How to build a **Knowledge Graph** in Neo4j and query it with **Text-to-Cypher** instead of vector search
- How to objectively compare RAG vs Knowledge Graph answers with an **LLM-as-judge** evaluation framework
- How to **evaluate and guard** a production system — retrieval metrics (Precision@K, MRR), generation metrics (faithfulness, groundedness), agent metrics (trajectory, termination), and guardrails (Llama Guard)

---

## Module Structure

```
Module_3_Production_Agentic_RAG_AI_Systems/
│
│   ── the teaching sequence, in order ──
├── 001. Agentic Router.ipynb                 # ① router → Qdrant retrieval → cited generation (+ route-level RBAC)
├── 002. Semantic Caching.ipynb               # ② a FAISS semantic cache, built from the ground up
├── 003. Agentic Router_semantic_caching_rbac.ipynb   # ③ the combined system: routing + cache + file-level RBAC
├── rag_helpers.py                            # Shared helpers — all pipeline logic behind notebook 003
│
├── Agentic_RAG/                              # Data + docs for notebook 001
│   ├── Upload_data_to_Qdrant_Notebook.ipynb  # Data pipeline — PDF → embeddings → Qdrant
│   ├── README.md
│   └── qdrant_data/                          # Pre-built vector collections (cloned from repo)
│       └── collection/
│           ├── opnai_data/                   # OpenAI Agents documentation embeddings
│           └── 10k_data/                     # Lyft FY20–22 + Uber FY21 10-K embeddings
│
├── Semantic_Cache/                           # Docs + corpus for notebook 002
│   ├── README.md
│   └── Amazon Simple Storage Service - User Guide.pdf
│
├── Semantic_Chunking/                        # Chunking strategies compared, on real 10-Ks
│   └── Comparison_of_Different_Semantic_Chunking_Techniques.ipynb
│
├── Knowledge_Graphs/                         # Structured retrieval track — RAG vs Knowledge Graph
│   ├── knowledge_graph_neo4j_with_evals.ipynb  # RAG vs KG comparison + LLM-judge evaluation
│   ├── knowledge_graph_rag_comparison.py     # Core implementation (Neo4j + Text-to-Cypher)
│   ├── app.py / streamlit_helper.py          # Streamlit app with interactive graph visualizations
│   ├── setup.py / sample_questions.py        # First-time data load + sample question sets
│   ├── requirements.txt                      # KG-specific dependencies (Neo4j, Pyvis, Streamlit…)
│   └── Knowledge_Graphs/
│       ├── Knowledge_Graphs_Basic_Version.ipynb     # Graph RAG fundamentals (hotel reviews)
│       └── Knowledge_Graphs_Advanced_Version.ipynb  # Graph enrichment + vector indexing
│
├── Moment_RAG/                               # Agentic RAG on video — cited answers at the exact moment
│
├── Evaluation_and_Guardrails/                # How you prove it works
│   └── AI_Eval_Metrics.ipynb                 # Eval pyramid: LLM → RAG → agent metrics (stdlib only)
│
└── .env                                      # API keys (OpenAI, SerpApi, Traversaal Pro, Neo4j)
```

---

## Notebooks

### 1. Upload Data to Qdrant
**`Agentic_RAG/Upload_data_to_Qdrant_Notebook.ipynb`**

Before you can retrieve anything you need to build your vector store. This notebook walks through the full document ingestion pipeline:

- Extract text from PDFs using **PyMuPDF**
- Chunk documents using `RecursiveCharacterTextSplitter` (2 048-char chunks, 50-char overlap)
- Generate **768-dimensional embeddings** using `nomic-ai/nomic-embed-text-v1.5`
- Upload vectors with metadata to two **Qdrant** collections:
  - `opnai_data` — OpenAI Agents official documentation
  - `10k_data` — SEC 10-K filings: Lyft FY2020–2022 and Uber FY2021

> The pre-built `qdrant_data/` directory is already included in the repo so you can skip this step and jump straight into querying. Run this notebook only if you want to rebuild the index or add your own documents.

---

### 2. Agentic RAG
**`001. Agentic Router.ipynb`**

The core of this module. This notebook introduces **agentic decision-making** as the first step in a RAG pipeline — the system thinks before it retrieves.

#### How it works

```
                        User Query
                            │
                            ▼
              ┌─────────────────────────┐
              │  Router LLM (GPT-5.6)   │
              │      route_query()      │
              └────────────┬────────────┘
                           │
         ┌─────────────────┼──────────────────┐
         ▼                 ▼                  ▼
  OPENAI_QUERY     10K_DOCUMENT_QUERY    INTERNET_QUERY
         │                 │                  │
         ▼                 ▼                  ▼
  Qdrant search     Qdrant search        SerpApi
  (opnai_data)      (10k_data)          (live web)
         │                 │                  │
         └────────┬─────────┘                  │
                  ▼                            │
         RAG Response Generator                │
         rag_formatted_response()              │
                  │                            │
                  └──────────────┬─────────────┘
                                 ▼
                          Final Response
```

#### Key components

| Function | Role |
|---|---|
| `route_query()` | Calls GPT-5.6-Luna with a router prompt; returns `action`, `reason`, and a short `answer` as JSON |
| `get_text_embeddings()` | Converts a query string to a 768-dim Nomic vector |
| `retrieve_and_response()` | Async function — queries Qdrant (top-3 chunks) then calls the RAG generator |
| `rag_formatted_response()` | Passes retrieved context to GPT-5.6-Luna and asks it to answer with inline citations |
| `get_internet_content()` | Calls the SerpApi Google Search API for real-time answers |
| `agentic_rag()` | Main orchestrator — ties routing, retrieval, and generation together |
| `secure_agentic_rag()` | Section 6 — the same loop with an RBAC check between routing and retrieval |

#### Data sources
- **OpenAI documentation** — Agents, tools, chat completions, best practices
- **10-K SEC filings** — Lyft FY2020, FY2021, FY2022 and Uber FY2021
- **Live internet** — Any query outside the above two domains via SerpApi

#### Section 6 — Role-Based Access Control

The last section adds an RBAC layer on top of the router. Two roles (`engineer`,
`finance_analyst`) are mapped to the route labels each may reach, and the check sits
between the router's decision and the tool call — so an unauthorized request is rejected
before anything is embedded, searched, or grounded.

| Knowledge source | Route label | `engineer` | `finance_analyst` |
|---|---|---|---|
| OpenAI documentation | `OPENAI_QUERY` | ✅ | ✅ |
| 10-K filings | `10K_DOCUMENT_QUERY` | ❌ | ✅ |
| Live internet search | `INTERNET_QUERY` | ✅ | ❌ |

File-level RBAC — gating individual documents rather than whole sources — is covered in
`003. Agentic Router_semantic_caching_rbac.ipynb`.

#### Assignment

**Required — sub-query division.** Split compound questions (e.g. *"What was Uber's and Lyft's revenue in 2021?"*) into individual sub-queries, route each one independently (they may land on different sources), and synthesise a single composed answer with citations preserved.

**Bonus (optional, ungraded) — RBAC with a semantic cache.** Put a cache behind the Section 6 access gate without leaking across roles: a cache keyed only on the question will happily serve a finance answer to an engineer who was just denied. Learners build a role-partitioned (or permission-tagged) cache and pass a self-check that includes an explicit leak test. Good warm-up for **ARGUS**, where caching and cost-per-source reporting are first-class requirements.

---

### 3. Semantic Cache from Scratch
**`002. Semantic Caching.ipynb`**

Builds a semantic cache without using any high-level caching library. The goal is to understand exactly how vector-based answer reuse works under the hood.

#### How it works

```
                        User Query
                            │
                            ▼
              ┌─────────────────────────────┐
              │    Time-Sensitivity Check    │
              │     is_time_sensitive()      │
              │  "now", "today", "outage"…   │
              └────────────┬────────────────┘
                           │
              YES ──────────┘──────────── NO
               │                          │
               ▼                          ▼
           SerpApi                  Embed Query
        (live search)          nomic-embed-text-v1.5
         NOT cached                      │
                                         ▼
                               ┌──────────────────┐
                               │   FAISS Search   │
                               │ IndexFlatL2      │
                               │ threshold = 0.2  │
                               └────────┬─────────┘
                                        │
                          HIT ──────────┴────────── MISS
                           │                          │
                           ▼                          ▼
                   Return cached           Traversaal Pro RAG
                   answer  ⚡              (AWS Guidebook)
                   ~0.1–0.2 s             Store → Return
                                          ~6–8 s
```

#### What gets cached

```
cache.json
{
  "questions"    : ["What is S3?", …],
  "embeddings"   : [[0.12, -0.43, …], …],   ← 768-dim Nomic vectors
  "answers"      : [{ full API response }, …],
  "response_text": ["An S3 bucket is …", …]
}
```

The FAISS `IndexFlatL2` is rebuilt in-memory from the JSON file on every load, so the cache survives notebook restarts.

#### Routing decision at a glance

| Query type | Backend | Cached? | Typical latency |
|---|---|---|---|
| Temporal keyword detected | SerpApi (live Google) | No | 0.1–1.5 s |
| Stable — FAISS hit (dist ≤ 0.2) | JSON store | Already stored | 0.1–0.2 s |
| Stable — FAISS miss (dist > 0.2) | Traversaal Pro RAG | Stored after call | 6–8 s |

#### External APIs used
- **Traversaal Pro** — hosted RAG over the AWS Guidebook corpus (`POST https://pro-documents.traversaal-api.com/documents/search`)
- **SerpApi** — real-time Google search results (`GET https://serpapi.com/search.json`)

---

### 4. Agentic RAG with Semantic Cache
**`003. Agentic Router_semantic_caching_rbac.ipynb`** + **`rag_helpers.py`**

This notebook combines everything — it wraps the full three-way agentic RAG pipeline from Notebook 2 inside the semantic cache layer from Notebook 3. The result is a system that is both *intelligent* (routes queries to the right source) and *efficient* (avoids redundant calls for similar questions).

All implementation lives in `rag_helpers.py` so the notebook stays minimal and focused on demonstrating system behaviour. After a `git clone` and a single `init_rag()` call, the entire pipeline is available via one function: `agentic_rag_with_cache(query, cache)`.

#### `rag_helpers.py` — what's inside

| Symbol | Type | Purpose |
|---|---|---|
| `init_rag(openai_api_key, serp_api_key, qdrant_path)` | function | One-time setup — loads Nomic model, wires OpenAI client, Qdrant, and SerpApi |
| `SemanticCaching` | class | FAISS-backed cache with time-sensitivity filter, JSON persistence, `check_cache()` / `add_to_cache()` |
| `get_internet_content(query)` | function | Live Google search via SerpApi |
| `route_query(query)` | function | GPT-5.6-Luna router returning `OPENAI_QUERY`, `10K_DOCUMENT_QUERY`, or `INTERNET_QUERY` |
| `agentic_rag_with_cache(query, cache)` | function | **Public entry point** — cache check → route → retrieve → store → return |

#### Full combined pipeline

```
User Query
    │
    ├─ Time-sensitive? ──YES──▶ SerpApi  (not cached)
    │
    └─ NO ──▶ FAISS cache lookup
                  │
                  ├─ HIT  ──▶ return stored answer  ⚡  (~0.1–0.2 s)
                  │
                  └─ MISS ──▶ Agentic RAG router
                                  │
                                  ├─ OPENAI_QUERY       ──▶ Qdrant (opnai_data) ──▶ GPT-5.6 RAG
                                  ├─ 10K_DOCUMENT_QUERY ──▶ Qdrant (10k_data)   ──▶ GPT-5.6 RAG
                                  └─ INTERNET_QUERY     ──▶ SerpApi (live web)
                                  │
                                  └─ Store result in cache ──▶ Return response
```

#### Minimal notebook structure

| # | Section | What it does |
|---|---|---|
| 1 | Setup | `pip install` + `git clone` + `from rag_helpers import ...` |
| 2 | API Keys | Load keys + `init_rag(...)` |
| 3 | Create Cache | `cache = SemanticCaching(clear_on_init=True)` |
| 4 | Pipeline reference | Markdown table pointing to `rag_helpers.py` |
| 5 | Demo | 7 test cells, each a single `agentic_rag_with_cache(query, cache)` call |
| 6 | RBAC | File-level access control — `secure_agentic_rag(user_id, file_id, query)`, 2 roles × 3 files, 6 allow/deny demos |
| 7 | Inspect | Cache state printout |

> **Note on Section 6.** The RBAC gate here is file-scoped and bypasses the cache — it calls the retriever directly. Combining the two safely (a cache that can't serve an answer across a permission boundary) is the bonus exercise in `001. Agentic Router.ipynb`.

---

### 5. Knowledge Graphs

**`Knowledge_Graphs/`**

A parallel track that swaps vector search for **structured graph retrieval**. Where the agentic RAG notebooks embed text and search by similarity, here you build a **Knowledge Graph** in Neo4j and answer questions by generating **Cypher queries** from natural language — then measure which approach wins, query by query.

#### Notebooks

| Notebook | What it covers |
|---|---|
| `knowledge_graph_neo4j_with_evals.ipynb` | The main notebook — builds RAG **and** KG pipelines from scratch, runs them side by side, and uses an **LLM judge** (GPT-4o-mini) to score each answer on accuracy, completeness, and precision. Dataset: researchers / articles / topics. |
| `Knowledge_Graphs/Knowledge_Graphs_Basic_Version.ipynb` | Graph RAG fundamentals — construct a hotel-reviews knowledge graph, migrate it to Neo4j, and build a template-based retriever. |
| `Knowledge_Graphs/Knowledge_Graphs_Advanced_Version.ipynb` | Extends the basic graph with **LLM-driven graph enrichment** (entity/relationship extraction from unstructured text) and **vector indexing** on graph nodes for hybrid structural + semantic retrieval. |

#### Three query methods compared

| Method | How it answers | Best for |
|---|---|---|
| **RAG** | Semantic / keyword search over documents → LLM generation | Explanations, summaries, fuzzy natural-language questions |
| **Knowledge Graph (Text-to-Cypher)** | NL question → Cypher → query Neo4j directly | Precise counts, relationships, aggregations, filtering |
| **LLM Judge** | GPT-4o-mini scores both answers and recommends a winner | Deciding *when to use which* — objectively |

#### Streamlit app

Beyond the notebooks, `Knowledge_Graphs/` ships a runnable Streamlit app (`app.py`) with side-by-side RAG-vs-KG comparison and interactive **Pyvis** graph visualizations (full graph + query-specific subgraph). Run `python setup.py` once to load data, then `streamlit run app.py`. See `Knowledge_Graphs/README.md` for the full walkthrough.

---

## Assignments

Two sets, very different in size. The first is the coursework inside the notebooks. The second
is **ARGUS** — the full-stack project for this module, where you ship the production version of
what these notebooks teach.

### Set 1 — Notebook assignments

In [`001. Agentic Router.ipynb`](001.%20Agentic%20Router.ipynb), at the end.

| | Task | Status |
|---|---|---|
| 1 | **Sub-query division** — split compound questions, route each sub-query independently (they may land on different sources), synthesise one answer with citations preserved | **Required** |
| 2 | **RBAC with a semantic cache** — put a cache behind the Section 6 access gate without leaking across roles, and pass the leak test in the self-check | Bonus |

The bonus assumes the semantic cache material, so attempt it after notebooks 3 and 4.

### Set 2 — ARGUS (full-stack assignment)

**[Moment Search at Scale](../../FDE-01-assignments/Assignment_3_Moment_Search_Scaled/README.md)** — starts Week 3, due before the Week 5 live session.

*Full stack* here means full-stack SWE **and** AI engineering: the frontend, the agent logic, the
ingestion pipeline, the caching, and the deployment — one product, entirely yours.

Take [`traversaal-ai/momentsearch`](https://github.com/traversaal-ai/momentsearch), a working
video-only moment-search product, and turn it into a **multi-source knowledge engine**: ingest
papers and slide decks alongside talks, run them through an **asynchronous work queue**, and
answer one question with cited moments across every source — the video timestamp *and* the paper
page *and* the deck slide. Ends with a Fly.io deploy and a benchmark proving ingestion never
starves search.

It's the production form of this module: routing, hybrid retrieval, caching and cost reporting,
all under real ingestion load. Read the spec yourself before touching any code — it's a reading
assignment first, and it says so.

Submission is a single Vercel URL with a working `/` and a self-proving `/evals` page — see
[`SUBMISSION.md`](../../SUBMISSION.md).

---

## Key Concepts Covered

| Concept | Description |
|---|---|
| **Agentic RAG** | An LLM reasons about *where* to search before it searches |
| **Query routing** | GPT-4o classifies queries into routing categories via a structured JSON prompt |
| **Vector embeddings** | Text is converted to 768-dim dense vectors using Nomic's embedding model |
| **Vector database (Qdrant)** | Embeddings are stored and searched by cosine/L2 similarity |
| **Semantic caching** | Previously seen (or semantically similar) queries are answered from cache instead of hitting the API again |
| **Time-sensitivity detection** | Keyword-based filter routes live queries to a web search API, bypassing the cache entirely |
| **RAG with citations** | Retrieved chunks are passed to an LLM which generates grounded answers with `[1][2]`-style references |
| **Knowledge Graph** | Entities and relationships are modeled as nodes and edges in Neo4j for structured retrieval |
| **Text-to-Cypher** | An LLM translates a natural-language question into a Cypher query executed directly on the graph |
| **Hybrid retrieval** | Combining structural (graph) and semantic (vector) retrieval, and choosing the right one per query |
| **LLM-as-judge evaluation** | An impartial LLM scores RAG vs KG answers on accuracy, completeness, and precision |

---

## Tech Stack

| Category | Library / Tool |
|---|---|
| LLM & Embeddings | `openai` (GPT-4o / GPT-4), `transformers`, `sentence_transformers`, `nomic-ai/nomic-embed-text-v1.5` |
| Vector database | `qdrant_client` (AsyncQdrantClient) |
| Similarity search / cache | `faiss-cpu` (IndexFlatL2) |
| Knowledge graph | `neo4j` (Neo4j Aura), Text-to-Cypher (GPT-4o-mini) |
| Graph visualization / app | `streamlit`, `pyvis`, `plotly` (Knowledge Graphs track) |
| Document processing | `fitz` (PyMuPDF), `langchain_text_splitters` |
| Async support | `asyncio`, `nest_asyncio` |
| Web / live search | `requests`, SerpApi (Google Search API), Traversaal Pro |
| Persistence | `json`, `python-dotenv` |
| Numerics | `numpy`, `torch` |

---

## Setup

### API keys required

| Key | Used in |
|---|---|
| `OPENAI_API_KEY` | Query routing and RAG generation (all notebooks) |
| `SERP_API_KEY` | Live Google search (Agentic RAG, combined, and Semantic Cache notebooks) |
| `traversaal_pro_api_key` | Hosted RAG over AWS Guidebook (Semantic Cache notebook only) |
| `NEO4J_URI` / `NEO4J_USERNAME` / `NEO4J_PASSWORD` | Neo4j Aura connection (Knowledge Graphs track only) |

**On Google Colab** — add keys to the Secrets panel (lock icon in the left sidebar).

**Locally** — create a `.env` file in `Module_3_Production_Agentic_RAG_AI_Systems/`:
```
OPENAI_API_KEY=sk-...
SERP_API_KEY=...
traversaal_pro_api_key=...
```

### Install dependencies

```bash
pip install openai qdrant-client transformers sentence-transformers \
            faiss-cpu torch numpy requests python-dotenv \
            langchain-text-splitters pymupdf einops nest_asyncio
```

> The **Knowledge Graphs** track has its own dependencies (Neo4j, Streamlit, Pyvis, Plotly).
> Install them separately with `pip install -r Knowledge_Graphs/requirements.txt`.

### Recommended notebook order

1. **`001. Agentic Router.ipynb`** — the routing architecture, and route-level RBAC on top of it
2. **`002. Semantic Caching.ipynb`** — caching mechanics in isolation
3. **`003. Agentic Router_semantic_caching_rbac.ipynb`** — the complete combined system: routing + cache + file-level RBAC
4. `Agentic_RAG/Upload_data_to_Qdrant_Notebook.ipynb` — optional, only if you want to rebuild the vector index
5. `Knowledge_Graphs/knowledge_graph_neo4j_with_evals.ipynb` — structured retrieval: RAG vs Knowledge Graph (independent track; needs a Neo4j Aura instance)

---

## Citation

If you use this code, please cite:

```
@misc{2024,
  title   = {Agentic RAG and Semantic Cache from Scratch},
  author  = {Hamza Farooq, Darshil Modi, Kanwal Mehreen, Nazila Shafiei},
  year    = {2024},
  license = {Apache 2.0}
}
```
