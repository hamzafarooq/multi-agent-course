# Moment RAG — cited answers with the exact source moment

A small, runnable RAG app that answers a **complex question** across a set of long podcast
episodes and returns a **streamed, cited answer** — where every citation deep-links into the
source **YouTube** video at the exact moment, with a synced transcript.

It's the agentic-RAG ideas from this module made tangible on **video**: the intelligence is on
the *query* side (decompose → hybrid retrieve → re-rank), and retrieval resolves to **moments**,
not just documents — which is what you actually cite in a generated answer.

> Companion to the notebooks in this module. Where `Agentic_RAG_Notebook.ipynb` routes a query
> to a backend, this shows the next step: **decompose** one query into facets, retrieve across
> **three fused signals**, **re-rank** to the precise moment, and **stream** a grounded answer.

---

## What it does

- **Ask anything complex.** "Where do these guests most disagree about AI's moat?" — not just keyword lookup.
- **Streamed, cited answer.** Markdown answer with inline `[n]` citations, written as it generates.
- **Click a citation → the moment plays.** A YouTube popup opens the real episode at that timestamp; the transcript scrolls and highlights in sync.
- **See how it was built.** A collapsible trace shows the inferred filters, the sub-questions, the candidate count, and timings.

No video downloads, no ffmpeg — playback uses the YouTube IFrame player. The corpus is 10
episodes of *Lenny's Podcast* (product / growth / AI / leadership).

---

## How it works

```
                         User question
                              │
              ┌───────────────▼────────────────┐
              │  Self-query  (LLM → filters)    │  infer hard metadata filters (topic)
              └───────────────┬────────────────┘
              ┌───────────────▼────────────────┐
              │  Decompose   (LLM → sub-queries)│  one question → 2–4 facets
              └───────────────┬────────────────┘
                              ▼
        ┌──────────── Hybrid retrieval in Qdrant ────────────┐
        │  dense kNN  ·  BM25 sparse  ·  HyDE question vecs   │  three branches per sub-query
        │                fused with RRF                       │
        └───────────────┬────────────────────────────────────┘
              ┌──────────▼───────────┐
              │  Cross-encoder re-rank│  sharpen *which* chunk → which moment
              └──────────┬───────────┘
              ┌──────────▼───────────┐
              │  Cited synthesis      │  streamed markdown with [n] → moments
              └──────────────────────┘
```

**HyDE lives at ingestion, not query time.** Each chunk is pre-tagged with the questions it
answers; those questions are embedded as a third (multi-vector) retrieval branch, so a user's
question can match a stored *question* — not just the raw text. This keeps query latency low.

### Key components

| File | Role |
|---|---|
| `app.py` | FastAPI server. `/ask_stream` (SSE: trace → citations → streamed answer), `/transcript/{id}`, `/videos`, `/` |
| `studio_ui.html` | Single-file UI: streaming answer, citation pills, YouTube popup + synced transcript, trace widget |
| `src/selfbuilt/search.py` | The pipeline orchestrator (`SelfBuiltEngine`) — each stage is independently callable |
| `src/selfbuilt/qdrant_store.py` | Qdrant hybrid index: dense + BM25 sparse + question multi-vector, RRF-fused server-side |
| `src/selfbuilt/query_breakdown.py` | LLM query decomposition into sub-queries |
| `src/selfbuilt/self_query.py` | LLM infers metadata filters from the query (cross-topic disambiguation) |
| `src/selfbuilt/rerank.py` | Cross-encoder (fastembed ONNX) re-ranker over the fused candidates |
| `src/embed.py` | OpenAI `text-embedding-3-large @ 1024` for chunks + questions (cached) |
| `data/` | Pre-built: `chunks/` (enriched), `embeddings/` (vectors), `transcripts/` (timed cues) |

---

## Run it

```bash
cd Moment_RAG
python -m venv .venv && source .venv/bin/activate     # optional
pip install -r requirements.txt
cp .env.example .env        # then add your OPENAI_API_KEY

uvicorn app:app --reload --port 8000
# open http://localhost:8000
```

The index is **pre-built and committed** (`data/embeddings/`), so first run only needs your
OpenAI key. On the first query, fastembed downloads two small CPU models (BM25 + the cross-encoder
re-ranker) — a one-time ~1 min. Each query then makes a few OpenAI calls (embed sub-queries,
decompose, self-query, and the streamed answer).

| Env var | Default | Purpose |
|---|---|---|
| `OPENAI_API_KEY` | — | required |
| `SYNTH_MODEL` | `gpt-4o` | model for the user-facing cited answer (falls back to `LLM_MODEL`) |
| `LLM_MODEL` | `gpt-4o-mini` | cheap internal calls (decompose, self-query) |

---

## Extend it

- **Rebuild the index** (after changing chunking, etc.): `python build_index.py` — re-embeds the
  committed chunks (cheap; no Whisper, no enrichment).
- **Add an episode:** append it to `videos.yaml` (`id`, `url`, `title`, `guest`, `content_labels`),
  drop a timestamped transcript into `data/transcripts/<id>.json` (`{"video_id", "cues":[{speaker,start_ms,end_ms,text}]}`),
  then run the chunk → enrich → embed steps in `src/ingest/` and `build_index.py`.

---

## Try these

- *Across these guests, where is the sharpest disagreement about where AI's durable moat comes from?*
- *Synthesize a 2026 playbook for a PM: what to start, stop, and double down on?*
- *How do the growth and product-craft views actually conflict?*

Each returns a cited answer; click a `[n]` to watch the exact moment.
