# Semantic Cache

> Part of **[Module 3: Agentic RAG](../README.md)** — the "make retrieval *fast*" track.

This folder builds a **semantic cache from scratch** — no high-level caching library — so you can
see exactly how vector-based answer reuse works under the hood. The idea: if a new question is
*semantically similar* to one you've already answered, return the stored answer in ~0.1 s instead of
paying for a full RAG call again.

A keyword-based **time-sensitivity guard** sits in front of the cache so live/temporal queries
(*"now"*, *"today"*, *"latest outage"*) are always routed to fresh web search and never served stale.

## Notebook

| Notebook | Open in Colab |
|---|---|
| [`Semantic_cache_from_scratch.ipynb`](Semantic_cache_from_scratch.ipynb) | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/modules/Module_3_Production_Agentic_RAG_AI_Systems/Semantic_Cache/Semantic_cache_from_scratch.ipynb) |

The folder also includes **`Amazon Simple Storage Service - User Guide.pdf`** — the AWS document you
upload into your Traversaal Pro project during setup (see [Setup](#setup)). It becomes the corpus the
hosted RAG answers from on cache misses.

---

## How it works

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

### Routing decision at a glance

| Query type | Backend | Cached? | Typical latency |
|---|---|---|---|
| Temporal keyword detected | SerpApi (live Google) | No | 0.1–1.5 s |
| Stable — FAISS hit (dist ≤ 0.2) | JSON store | Already stored | 0.1–0.2 s |
| Stable — FAISS miss (dist > 0.2) | Traversaal Pro RAG | Stored after call | 6–8 s |

---

## What gets cached

```
cache.json
{
  "questions"    : ["What is S3?", …],
  "embeddings"   : [[0.12, -0.43, …], …],   ← 768-dim Nomic vectors
  "answers"      : [{ full API response }, …],
  "response_text": ["An S3 bucket is …", …]
}
```

The FAISS `IndexFlatL2(768)` is rebuilt in-memory from the JSON file on every load, so the cache
survives notebook restarts. The match threshold is a tunable Euclidean distance
(`euclidean_threshold = 0.2`) — lower is stricter.

---

## External APIs used

| API | Role | Endpoint |
|---|---|---|
| **Traversaal Pro** | Hosted RAG over the AWS doc you upload to your project; queried on cache misses | `POST https://pro-documents.traversaal-api.com/documents/search` |
| **SerpApi** | Real-time Google search for time-sensitive queries | `GET https://serpapi.com/search.json` |

---

## Setup

### Set up the Traversaal Pro project (do this first)

The cache calls a hosted Traversaal Pro RAG project on a miss — but that project starts empty. You
populate it yourself:

1. Sign up at **[pro.traversaal.ai](https://pro.traversaal.ai)** and grab your Bearer token.
2. Create a project and **upload the provided `Amazon Simple Storage Service - User Guide.pdf`**
   (in this folder) into it. Traversaal Pro handles chunking, embedding, retrieval, and generation —
   this PDF becomes the corpus the API answers from.
3. Use that token as `traversaal_pro_api_key` below.

### API keys

| Key | Used for |
|---|---|
| `SERP_API_KEY` | Live Google search for time-sensitive queries |
| `traversaal_pro_api_key` | Auth for your Traversaal Pro project (queried on cache misses) |

**On Colab** — add keys to the Secrets panel (lock icon, left sidebar).
**Locally** — put them in a `.env` file at the module root (`Module_3_Production_Agentic_RAG_AI_Systems/`).

### Install dependencies

```bash
pip install transformers sentence-transformers faiss-cpu \
            torch numpy requests python-dotenv einops
```

## Tech stack

| Category | Library / Tool |
|---|---|
| Embeddings | `transformers`, `sentence_transformers`, `nomic-ai/nomic-embed-text-v1.5` |
| Similarity search / cache | `faiss-cpu` (IndexFlatL2) |
| Web / live search | `requests`, SerpApi, Traversaal Pro |
| Persistence | `json` |

---

This notebook teaches caching in isolation. To see it wrapped around the full three-way agentic RAG
pipeline, head to **[`../Agentic_RAG_with_Semantic_Cache.ipynb`](../Agentic_RAG_with_Semantic_Cache.ipynb)**.
