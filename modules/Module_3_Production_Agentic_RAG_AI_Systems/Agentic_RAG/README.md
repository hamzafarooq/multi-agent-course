# Agentic RAG

> Part of **[Module 3: Agentic RAG](../README.md)** — the "make retrieval *think*" track.

This folder holds the core **agentic RAG** pipeline: a system that **reasons about *where* to
search before it searches**. Instead of pushing every question through one static retriever, an
LLM router inspects the query and dispatches it to the right backend — a vector store of OpenAI
docs, a vector store of SEC 10-K filings, or live web search.

Everything is built **from scratch** — no LangChain, no LlamaIndex.

## Notebooks

| # | Notebook | Open in Colab |
|---|---|---|
| 1 | [`Upload_data_to_Qdrant_Notebook.ipynb`](Upload_data_to_Qdrant_Notebook.ipynb) — build the vector store | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/modules/Module_3_Production_Agentic_RAG_AI_Systems/Agentic_RAG/Upload_data_to_Qdrant_Notebook.ipynb) |
| 2 | [`Agentic_RAG_Notebook.ipynb`](Agentic_RAG_Notebook.ipynb) — the routing + retrieval + generation pipeline | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/modules/Module_3_Production_Agentic_RAG_AI_Systems/Agentic_RAG/Agentic_RAG_Notebook.ipynb) |

> **Start with Notebook 2.** The pre-built `qdrant_data/` directory ships with the repo, so you can
> jump straight into querying. Only run Notebook 1 if you want to rebuild the index or add your own
> documents.

---

## 1. Upload Data to Qdrant

**`Upload_data_to_Qdrant_Notebook.ipynb`** — the document ingestion pipeline that builds the vector
store the agent retrieves from:

- Extract text from PDFs using **PyMuPDF** (`fitz`)
- Chunk documents with `RecursiveCharacterTextSplitter` (2 048-char chunks, 50-char overlap)
- Generate **768-dimensional embeddings** using `nomic-ai/nomic-embed-text-v1.5`
- Upload vectors with metadata to two **Qdrant** collections:
  - `opnai_data` — OpenAI Agents official documentation
  - `10k_data` — Uber 2021 and Lyft 2020–2024 SEC 10-K filings

The output lands in `qdrant_data/collection/`, which is already included in the repo.

---

## 2. Agentic RAG

**`Agentic_RAG_Notebook.ipynb`** — the core of this track. An LLM router classifies each query, then
the matching backend retrieves context and an LLM generates a cited answer.

```
                        User Query
                            │
                            ▼
              ┌─────────────────────────┐
              │   Router LLM (GPT-4o)   │
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

### Key components

| Function | Role |
|---|---|
| `route_query()` | Calls GPT-4o with a router prompt; returns `action`, `reason`, and a short `answer` as JSON |
| `get_text_embeddings()` | Converts a query string to a 768-dim Nomic vector |
| `retrieve_and_response()` | Async — queries Qdrant (top-3 chunks) then calls the RAG generator |
| `rag_formatted_response()` | Passes retrieved context to the LLM and asks it to answer with inline citations |
| `get_internet_content()` | Calls the SerpApi Google Search API for real-time answers |
| `agentic_rag()` | Main orchestrator — ties routing, retrieval, and generation together |

### Data sources

- **OpenAI documentation** — Agents, tools, chat completions, best practices (`opnai_data`)
- **10-K SEC filings** — Uber 2021 and Lyft 2020–2024 financial data (`10k_data`)
- **Live internet** — any query outside the above two domains, via SerpApi

### Assignment

Implement **sub-query division** — split compound questions (e.g. *"What was Uber's and Lyft's
revenue in 2021?"*) into individual sub-queries and process each one through the agentic pipeline
independently.

---

## Setup

### API keys

| Key | Used for |
|---|---|
| `OPENAI_API_KEY` | Query routing and RAG generation |
| `SERP_API_KEY` | Live Google search (`INTERNET_QUERY` route) |

**On Colab** — add keys to the Secrets panel (lock icon, left sidebar).
**Locally** — put them in a `.env` file at the module root (`Module_3_Production_Agentic_RAG_AI_Systems/`).

### Install dependencies

```bash
pip install openai qdrant-client transformers sentence-transformers \
            torch numpy requests python-dotenv \
            langchain-text-splitters pymupdf einops nest_asyncio
```

## Tech stack

| Category | Library / Tool |
|---|---|
| LLM & embeddings | `openai` (GPT-4o), `transformers`, `sentence_transformers`, `nomic-ai/nomic-embed-text-v1.5` |
| Vector database | `qdrant_client` (AsyncQdrantClient) |
| Document processing | `fitz` (PyMuPDF), `langchain_text_splitters` |
| Web / live search | `requests`, SerpApi (Google Search API) |
| Async support | `asyncio`, `nest_asyncio` |

---

Once you understand this pipeline, see **[`../Semantic_Cache/`](../Semantic_Cache/)** to make it
*fast*, and **[`../Agentic_RAG_with_Semantic_Cache.ipynb`](../Agentic_RAG_with_Semantic_Cache.ipynb)**
for the two combined.
