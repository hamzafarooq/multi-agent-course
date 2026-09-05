# PRD, Assignment 1: LUMINA (Perplexity-style AI search)

| | |
|---|---|
| **Project** | 01 · LUMINA, a Perplexity clone that searches, remembers, reads your documents, makes the deck, and draws the picture |
| **Track** | FDE Agent Engineering Bootcamp, cohort 2026-03 |
| **Kicks off** | Week 1 (Agent Foundations, Harness & System Design) · due end of Week 2 |
| **Owner** | Hamza Farooq |
| **Status** | Draft v0.2, 2026-09-05 (MERN revision) |
| **Stack** | **MERN**: MongoDB Atlas (documents, memory, cache, jobs, and vectors via Atlas Vector Search) · Express (two Node services) · React (the provided UI) · Node end to end, including the bench, the eval, and the quality checker |
| **Lives in** | `modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/`: the Week 1 project ships with the Week 1 module |
| **Replaces** | FDE Assignment 1, Live Translate (see Open Questions) |

> **One line:** ask a question, get a streamed, cited answer built from live web search and your own documents; the system remembers you across sessions; any answer can become a slide deck or an image on demand. Two Express services, one MongoDB, one fixed contract, one deploy, one benchmark that must pass.

---

## 1 · Problem

Perplexity is the clearest example of what a production agent loop looks like from the outside: a query goes in, the system *decides* what to search, reads, and answers with citations you can click. Learners in Week 1 are taught that loop. LUMINA makes them ship it, as a product, not a notebook.

It also front-loads five capabilities every later project depends on:

| Capability | Where it comes back |
|---|---|
| Tool-using agent loop with a trace | Every project; the harness is the course |
| Web search as a tool the agent chooses | ARGUS (retrieval decisions), EPYHIA (research) |
| Memory (thread + long-term) | Module 2 memory; VOXA conversation state |
| RAG over user documents with page-level citations | ARGUS extends exactly this contract |
| Artifacts (deck, image) as **async, cost-bearing actions** | A3 async queue, A4 action gate |

Same FDE shape as before: a fixed contract, a provided UI that is the acceptance test, two backend services you own, an SLA you prove with a benchmark, a real deploy. New this cohort: the whole thing is **one language**. React in front, Express behind, MongoDB underneath, and Node for the bench, the eval, and the quality checker, so a learner never context-switches between a JS frontend and a Python backend to debug one request.

## 2 · Goals

1. **Ship a working answer engine in two weeks.** Fresh clone → follow README → provided UI lights up against the learner's backend, locally and on Fly.io.
2. **Every claim is grounded.** ≥ 95 % of inline citations resolve to a source the system actually retrieved in that request. Fabricated sources are an automatic fail.
3. **Prove it by arithmetic.** `benchmark/bench.mjs` exits 0 against declared numbers in `sla.json`; no threshold is judged by a model.
4. **Make cost visible.** Every answer and every artifact logs tokens, latency, and USD; `/stats` reports the day's spend.
5. **Teach the async pattern early.** Deck and image generation are `202`-then-poll artifacts, so A3's queue is not the first time learners meet it.

## 3 · Non-goals

- No user accounts, OAuth, or billing. Identity is a dev header (`X-User-Id`); the gateway rejects requests without it.
- No browsing agent that clicks or fills forms. Search + fetch + read only.
- No voice (VOXA), no video ingestion (ARGUS), no autonomous side effects such as sending or publishing (EPYHIA).
- No fine-tuning, no self-hosted models required. Provider-swappable via env is enough.
- No answer caching. Search *results* are cached with a TTL; answers are always regenerated so freshness is never served stale.
- No multi-agent split in the required build. Planner/researcher/writer subagents are a stretch goal, taught in Week 2.

## 4 · Users & scenarios

**Learner** (builds it), **grader** (runs the eval), **end user** (the person typing questions, in the demo, the learner).

*Scenario A, fresh question.* Alex types "What changed in the EU AI Act's GPAI obligations this summer?" LUMINA plans two searches, fetches four pages, streams a five-sentence answer with `[1]`–`[4]`, and shows the sources rail. Alex clicks `[2]` and lands on the cited paragraph.

*Scenario B, memory.* A week earlier Alex told LUMINA "I build in TypeScript and want code examples, not prose." Today, in a new thread, "how do I call Tavily?" returns a TypeScript snippet first. Alex opens the Memory panel, sees that stored preference, and deletes it.

*Scenario C, own documents.* Alex uploads three PDFs into a Space called "Q3 board pack" and asks "what did we commit to on churn?" The router chooses documents over web, and the answer cites `board-deck.pdf, p. 14`. Alex then asks "and what does the market say?", the router now blends web and docs, citations of both kinds appear.

*Scenario D, artifacts.* Alex clicks **Make a deck** on that answer. LUMINA returns `202`, the UI polls, and forty seconds later a `.pptx` with eight slides is downloadable; each slide's claims trace back to the thread's citations. Alex then types "generate a hero image for the churn slide" and gets a `gpt-image-1` image, with its cost logged and the daily image cap decremented.

## 5 · Requirements

Grouped by the five capabilities plus the loop that ties them together. **Must** rows are graded; **Should** rows are expected of a strong submission; **Could** rows are stretch.

### 5.1 The agent loop (the harness)

| Pri | Requirement |
|---|---|
| Must | One loop: plan → choose tool → observe → repeat → answer. Tools: `web_search`, `fetch_page`, `search_documents`, `recall_memory`, `save_memory`. Artifact tools (`make_presentation`, `generate_image`) exist only behind `POST /artifacts`; the ask loop **never** calls them, so a question can never spend on an image by itself. |
| Must | Bounded: max 8 tool calls and 90 s per request; hitting a cap returns an honest partial answer with `terminated: "cap"` in the `done` event, never a fabricated complete one. A provider exception ends the run with `terminated: "error"` and a `502`. |
| Must | Every step is emitted as a `trace` SSE event *before* the answer streams, and logged with the request id. |
| Must | Every ask writes a **run log** `runs/<requestId>.json` in the quality kit's shape (§13): `tokens`, `wallClockSec`, `costUsd`, `terminated`, ordered `toolCalls[{name, ok, error}]`. Ten lines of adapter; it is what the gates read. |
| Must | Tool errors surface. A failed search or fetch is a visible `trace` step with `ok: false` and an error string. A provider outage returns `502`; the service never returns "I couldn't find anything" as a successful answer when the real cause was an exception. |
| Should | Router mode `auto` decides web vs. documents vs. both from the query and the Space's contents; the decision and its reason appear in the trace. |
| Could | Query decomposition for multi-part questions (Module 3's Pro-search shape). |

### 5.2 Internet search (SerpApi or Tavily)

| Pri | Requirement |
|---|---|
| Must | `SEARCH_PROVIDER=tavily \| serpapi`, swappable via env with no code change; the key comes from `.env`. |
| Must | Search results are **cached** in two tiers, an in-process LRU and a MongoDB `searchCache` collection with a TTL index on `expiresAt`, keyed by a SHA-256 of `(normalized query, provider)`, TTL default 6 h, `searchCached: true` in the `done` event when every search in the request was a hit. |
| Must | Page content is fetched and read (Tavily `extract`, or `@mozilla/readability` + `jsdom` for SerpApi results); the answer is synthesized from fetched text, not from search snippets alone. Snippet-only synthesis is visible in the trace and scored down. |
| Must | Each inline `[n]` maps to exactly one entry in the `sources` event, with `title`, `url`, `snippet` (the passage the claim rests on). |
| Should | Time-sensitive queries (contains "today", "latest", a year ≥ current) bypass the search cache. |
| Could | A second provider as automatic fallback on `5xx`. |

### 5.3 Memory

| Pri | Requirement |
|---|---|
| Must | **Thread memory:** every thread persists its messages, citations, and artifacts; a follow-up question sees the whole thread. |
| Must | **Long-term memory:** durable facts and preferences per `X-User-Id`, stored in the `memories` collection, each document `{_id, userId, text, embedding, sourceThread, createdAt}`. |
| Must | Writes are explicit and inspectable: the agent calls `save_memory` only for stable facts/preferences (not for trivia from a single answer), the trace shows the write, and `GET /memory` lists every row. `DELETE /memory/{id}` removes one. |
| Must | Recall is demonstrable across threads: a preference saved in thread A changes the answer in thread B, and the trace shows `recall_memory` returning it. |
| Should | Memory recall is semantic: an Atlas Vector Search index on `memories.embedding`, filtered by `userId`, not "inject all rows". Cap injected memory at ~10 documents / 1 000 tokens. |
| Could | A "why did you remember that?" link from a memory row to the originating message. |

### 5.4 RAG over user documents

| Pri | Requirement |
|---|---|
| Must | **Spaces:** `POST /spaces` creates a collection; `POST /spaces/{id}/documents` accepts PDF, Markdown, and plain text (≤ 25 MB), stores the file in GridFS, inserts a `pending` document and a `jobs` row, and returns `202 {docId, status: "pending"}`; parsing (`pdfjs-dist`, page-aware), chunking, embedding, and indexing happen on the worker, never in the request path. `GET /spaces/{id}/documents` shows `pending → parsing → embedding → indexed \| failed` with `pct`. |
| Must | Chunks carry a **locator**: `{page}` for PDF, `{heading}` or `{line}` for text. Document citations render as `filename, p. N`. Same locator shape ARGUS extends later. |
| Must | One `chunks` collection for all Spaces with **one Atlas Vector Search index** on `embedding` and a `spaceId` filter in every `$vectorSearch`. No second database: the vectors live next to the documents they came from. `/health` names the store (`atlas-vector-search`, or `mongo-cosine-scan` for the documented local-dev fallback). |
| Must | Hybrid retrieval: `$vectorSearch` (dense) plus an Atlas Search text index on `chunks.text` (BM25), fused with reciprocal rank fusion, with a re-rank step **or** a documented reason for skipping it; top-k and thresholds declared in config, not hard-coded. |
| Must | A document reaches `indexed` only after a **read-your-write probe**: the worker queries the vector index for one of the chunks it just wrote and gets it back. Atlas Search indexes are eventually consistent; "upserted" is not "searchable". |
| Must | Empty retrieval → the answer says so and cites nothing. Citing a chunk that is not in the index is an automatic fail. |
| Must | Meets `recall_at_5_min` on the provided gold set (30 questions over the provided corpus, see §9). |
| Should | Router blends web and documents in one answer when both are relevant, with mixed `kind` in `sources`. |
| Could | Re-index on document replace; delete a document and prove its chunks are gone. |

### 5.5 Presentation generation

| Pri | Requirement |
|---|---|
| Must | `POST /artifacts {kind: "deck", threadId, answerId}` → `202 {artifactId, status: "pending"}`; the UI polls `GET /artifacts/{id}` until `ready` and downloads a `.pptx`. |
| Must | Pipeline: answer + its sources → a structured outline (JSON: title, 6–10 slides, each with bullets and the citation numbers it rests on) → rendered with `pptxgenjs`. The outline JSON is stored on the artifact document and returned by the API so grading can check grounding by arithmetic: every citation number on every slide must exist in the answer's `sources`. |
| Must | Opens in PowerPoint, Keynote, and Google Slides without repair prompts; a final "Sources" slide lists every cited URL/document. |
| Must | p95 generation time ≤ 60 s; failure sets `status: "failed"` with an `error` string, never a half-written file marked ready. |
| Should | A speaker-notes field per slide carrying the supporting snippet. |
| Could | An HTML (reveal.js) preview rendered in the UI before download. |

### 5.6 Image generation (`gpt-image-1`)

| Pri | Requirement |
|---|---|
| Must | `POST /artifacts {kind: "image", threadId, prompt?}` → `202`, generated with OpenAI Images (`gpt-image-1`); if `prompt` is omitted the agent writes one from the thread context and stores the prompt it used. |
| Must | The stored artifact record carries `{model, size, costUsd, promptUsed}`; the file lives in GridFS (default, zero extra infra) or an S3-compatible bucket; never committed. |
| Must | **Cost gate:** a per-user daily cap (`IMAGE_DAILY_CAP`, default 10) enforced in the agent service; over cap → `429 {error, resetsAt}`. `DRY_RUN=true` returns a placeholder image with `costUsd: 0` so the whole flow is testable without spend. |
| Must | Provider errors (content policy, quota) surface as `failed` with the provider's message, not as a silent retry loop. |
| Should | One-click "Illustrate this slide" from a deck slide's context. |
| Could | Image edit / variation of a previous artifact. |

## 6 · Architecture

Same split as every FDE project: the browser only ever talks to the gateway; provider keys live only in the agent service. Both services are Express on Node 20 with TypeScript; one MongoDB Atlas cluster holds everything, including the vectors.

```
  ┌──────────────────────────────┐
  │  Web UI  (web/)              │  ← PROVIDED · React 18 + Vite · the acceptance test
  │  query · stream · citations  │     types imported from packages/contract
  │  memory panel · spaces       │
  │  deck / image actions        │
  └──────────────┬───────────────┘
                 │  HTTP + SSE  (X-User-Id, X-Request-Id)
                 ▼
  ┌──────────────────────────────┐
  │  Express gateway  :8787      │  ← YOU · CORS · zod-validate the contract · rate-limit (429)
  │  request log · request id    │        serve web/dist · proxy · SSE pass-through (no buffering)
  └──────────────┬───────────────┘
                 │  same contract, same zod schemas
                 ▼
  ┌──────────────────────────────┐
  │  Express agent service :8000 │  ← YOU · the loop and its tools · the worker
  │  loop · router · tools       │
  │  memory · RAG · artifacts    │
  │  jobs worker (in-process)    │
  └───┬──────┬──────────┬────────┘
      ▼      ▼          ▼
   Search   LLM +    MongoDB Atlas ─────────────────────────────────────────────
  (Tavily/  embed    threads · messages · memories(vector idx) · spaces · documents
  SerpApi) (env-     chunks(vector idx + text idx) · searchCache(TTL idx) · jobs
            swap)    artifacts · requests · runs · GridFS (uploads, decks, images)
```

**Why MERN here.** Three reasons, and none is "it's popular":
1. **One request, one language.** The trace a learner reads in the UI and the loop that produced it are both TypeScript. Debugging a citation from chip to `$vectorSearch` never crosses a language boundary.
2. **One database, including vectors.** Atlas Vector Search puts embeddings in the same collection as the chunk text and its locator, so a citation is one document, not a join across a vector store and a relational table. The `spaceId` filter is a plain query predicate.
3. **The quality kit is already Node.** `check.mjs` reads `runs/*.json`; the agent service writes them natively. The bench and eval are `.mjs` too, so the six gates run with `node` and nothing else installed.

**Why the gateway still matters.** SSE pass-through, per-user rate limiting, contract validation, and the image cost gate are the concerns you want on the edge, away from the keys. It is also where you learn that Express buffers SSE by default unless you flush and disable compression.

**Async inside one service, backed by MongoDB.** Document indexing and artifact generation are rows in a `jobs` collection. The API inserts `{kind, status: "pending", payload}` and returns `202`. A worker loop in the agent service claims work with an atomic `findOneAndUpdate({status: "pending"}, {$set: {status: "running", claimedAt, workerId}})`, does the job, and only then flips the target document's status. Crash mid-job and the row stays `running` with a stale `claimedAt`; a sweeper returns it to `pending`. No Redis, no broker. ARGUS swaps Prefect in against the same contract.

## 7 · API contract (fixed: the UI speaks this)

All routes on the gateway; the gateway forwards the same shapes to the AI service. `X-User-Id` required on every route except `/health`.

```jsonc
POST /threads                       → 201 { "threadId": "thr_…" }
GET  /threads/{id}                  → 200 { "messages": [ { "role", "content", "sources": [...], "artifacts": [...] } ] }

POST /threads/{id}/ask              // body: { "query": "…", "mode": "auto" | "web" | "docs", "spaceId": "spc_…"? }
  → 200 text/event-stream
  event: trace    data: { "step": 1, "tool": "web_search", "input": {...}, "ok": true, "ms": 812, "reason": "…" }
  event: sources  data: [ { "n": 1, "kind": "web", "title": "…", "url": "…", "snippet": "…" },
                          { "n": 2, "kind": "doc", "docId": "doc_…", "title": "board-deck.pdf", "locator": { "page": 14 }, "snippet": "…" } ]
  event: token    data: { "text": "…" }
  event: done     data: { "answerId": "ans_…", "latencyMs": 6410, "ttftMs": 1830, "model": "…",
                          "tokens": { "in": 9120, "out": 410 }, "costUsd": 0.021,
                          "searchCached": false, "terminated": "done" | "cap" }
  event: error    data: { "status": 502, "error": "search provider 503" }

GET    /memory                      → 200 { "memories": [ { "id", "text", "sourceThread", "createdAt" } ] }
DELETE /memory/{id}                 → 204

POST /spaces                        → 201 { "spaceId": "spc_…", "name": "…" }
POST /spaces/{id}/documents         // multipart file   → 202 { "docId": "doc_…", "status": "pending" }
GET  /spaces/{id}/documents         → 200 { "documents": [ { "docId", "title", "status", "pct", "pages"? , "error"? } ] }

POST /artifacts                     // { "kind": "deck" | "image", "threadId", "answerId"?, "prompt"? }
                                    → 202 { "artifactId": "art_…", "kind": "deck", "status": "pending" }
GET  /artifacts/{id}                → 200 { "status": "pending" | "ready" | "failed", "url"?: "/artifacts/{id}/file",
                                            "outline"?: {...}, "promptUsed"?: "…", "model"?: "…", "costUsd"?: 0.04, "error"?: "…" }
GET  /artifacts/{id}/file           → 200 (application/vnd.openxmlformats-officedocument.presentationml.presentation | image/png)

GET  /health                        → 200 { "status": "ok", "model": "…", "searchProvider": "tavily", "vectorStore": "atlas-vector-search", "db": "ok", "ai": { "status": "ok" } }
GET  /evals/report.json             → 200 { "assignment", "student", "repo", "video", "deployedAt", "rubric", "bench", "quality", "trajectories" }  // written by the eval skill, rendered by the UI at /evals
GET  /stats                         → 200 { "requests": 412, "answers": 130, "searchCacheHitRatePct": 58.1, "ttftP95Ms": 1910,
                                            "costUsdToday": 3.12, "imagesToday": 4, "imageDailyCap": 10 }
```

**Status codes:** `400` invalid input · `401` missing `X-User-Id` · `404` unknown thread/space/artifact · `413` file too large · `429` rate limit or image cap · `501` not implemented · `502` upstream (LLM, search, image) failure.

**Contract rules that matter**
- Every `[n]` in streamed text has a matching `n` in `sources` for that answer. Extra or missing → grounding failure.
- `sources` is sent **before** the first `token`, so the UI can render chips as text arrives.
- `202` endpoints return in < 300 ms; the work happens after.
- `latencyMs`, `ttftMs`, `costUsd` are measured server-side.

## 8 · Data model (MongoDB)

One database, `lumina`. Every document carries `userId` (from `X-User-Id`) and `createdAt`. Ids are prefixed strings (`thr_`, `ans_`, `doc_`, `art_`) generated in the app so they are readable in logs and URLs.

| Collection | Key fields | Indexes |
|---|---|---|
| `threads` | `_id, userId, title, createdAt` | `{userId: 1, createdAt: -1}` |
| `messages` | `_id, threadId, role, content, sources[], done{}, artifactIds[], createdAt` | `{threadId: 1, createdAt: 1}` |
| `memories` | `_id, userId, text, embedding[1536], sourceThread, createdAt` | **vector** on `embedding` (cosine) with `userId` as a filter field |
| `spaces` | `_id, userId, name, createdAt` | `{userId: 1}` |
| `documents` | `_id, spaceId, userId, title, status, pct, pages, error, fileId (GridFS), createdAt` | `{spaceId: 1}` |
| `chunks` | `_id, docId, spaceId, text, locator{page \| heading \| line}, embedding[1536]` | **vector** on `embedding` with `spaceId` filter; **search** (BM25) on `text` |
| `searchCache` | `_id (sha256 of query+provider), provider, results[], expiresAt` | `{expiresAt: 1}` **TTL** `expireAfterSeconds: 0` |
| `jobs` | `_id, kind (index_document \| make_deck \| make_image), status, payload, claimedAt, workerId, attempts, error` | `{status: 1, createdAt: 1}` |
| `artifacts` | `_id, userId, threadId, answerId, kind, status, fileId (GridFS), outline, promptUsed, model, costUsd, error, createdAt` | `{userId: 1, createdAt: -1}` |
| `requests` | `requestId, userId, route, status, ms, tokensIn, tokensOut, costUsd, toolCalls, terminated, createdAt` | `{createdAt: -1}`, `{requestId: 1}` |
| `runs` | the exact `runs/<requestId>.json` shape from §13, plus `requestId` | `{createdAt: -1}` |
| GridFS `uploads`, `files` | raw PDFs/MD/TXT; rendered `.pptx` and `.png` | default |

**Schema lives in code.** `packages/contract/` exports zod schemas for every request, response, SSE event, and collection document. The gateway validates inbound bodies with them, the agent service validates outbound events with them, and the provided React UI imports the types. Mongoose is allowed but not required; the zod schema is the contract, the ODM is an implementation detail.

**Local development without Atlas.** `docker compose up mongo` gives you a plain `mongod`, which has no Vector Search. `VECTOR_BACKEND=mongo-cosine-scan` makes `search_documents` pull a Space's chunks and score cosine in Node. Fine to 5 000 chunks, useless beyond, and `/health` must say which backend is live so the grader knows.

## 9 · Performance, SLA & cost (`benchmark/sla.json`)

Declared before the first run. `bench.mjs` exits non-zero on any miss; the grader runs it against the live deploy.

| Metric | Target | Why |
|---|---|---|
| Time to first token, p95 | ≤ 2 500 ms | the "it's thinking" window a user tolerates |
| Full answer, p95 | ≤ 12 000 ms | plan + 2 searches + 4 fetches + synthesis |
| `202` accept latency, p95 | ≤ 300 ms | proves work is off the request path |
| Citation grounding | ≥ 95 % | share of `[n]` whose `snippet` is found verbatim (normalized) in the fetched page or indexed chunk, arithmetic, no judge |
| RAG recall@5 on gold set | ≥ 0.70 | 30 Q/A pairs over the provided corpus |
| Search cache hit rate (bench workload) | ≥ 50 % | repeated/near-duplicate queries in the workload |
| Deck generation, p95 | ≤ 60 s | |
| Image generation, p95 | ≤ 45 s | |
| Error rate | ≤ 1 % | |
| Cost per answer (mean) | ≤ $0.05 | placeholder price table in `sla.json`; learners set provider rates |

`bench.mjs` reports latency percentiles, grounding rate, recall, hit rate, cost per answer and per artifact, and projected monthly cost at the volume declared in `sla.json`, with and without the search cache.

## 10 · Observability

- One structured log line per request in the gateway (`method, route, status, ms, request_id, user_id`) and one per answer in the agent service (`requestId, toolCalls, terminated, tokens, costUsd, searchCached, ttftMs, latencyMs`), both as JSON lines via `pino`.
- `X-Request-Id` reused if inbound, else generated at the gateway, forwarded, logged by both; one request greppable end to end.
- `trace` events are the debugging surface: a grader must be able to reconstruct *why* an answer cited what it cited from the stream alone.
- `/stats` numbers reconcile with the log (the bench cross-checks `answers` and `costUsdToday`).

## 11 · Non-negotiables (becomes `AGENTS.md`)

1. **The provided UI works unmodified.** It is the acceptance test.
2. **Grounded or nothing.** A citation that does not resolve to something retrieved in that request is an automatic fail. Empty retrieval → say so.
3. **Errors surface, never swallowed.** Provider failure → `502` + log. No `try/catch` that returns a plausible answer.
4. **The loop is bounded and honest.** Caps exist; hitting one is reported as `terminated: "cap"`.
5. **Memory is visible and deletable.** Nothing is remembered that `/memory` does not show.
6. **Indexing and artifacts are async.** `202` in < 300 ms; the work runs from the `jobs` collection; status transitions are committed only after the work succeeds, and `indexed` only after the read-your-write probe.
7. **Image spend is gated.** Daily cap enforced server-side; `DRY_RUN` exists; cost logged per image.
8. **Secrets from env, never committed.** `.env`, `node_modules/`, `web/dist/`, `runs/`, `reports/` are git-ignored. The Atlas connection string is a secret.
9. **Evidence over vibes.** Numbers in `PRODUCT_EVAL.md` come from a real `bench.mjs` run against the deployed app.

## 12 · Grading (100 pts): `eval/rubric.json`

| Area | Pts | Type | What earns them | Rules |
|---|---|---|---|---|
| UI lights up & contract | 10 | auto | Fresh clone → README → UI streams an answer through the gateway; all routes return the declared shapes and status codes | C1 |
| Search & cited answers | 20 | auto | Grounding ≥ 95 %; `sources` precedes tokens; pages fetched not just snippets; `searchCached` true on repeat | E2 (`citationGrounding`, `retrievalRate`) |
| Memory | 10 | auto | Preference saved in thread A observably changes thread B; `/memory` lists it; `DELETE` removes it and the effect disappears |, |
| RAG over documents | 15 | auto | Upload → `202` → `indexed`; doc citation with `page` locator; router picks docs when relevant; recall@5 ≥ 0.70 | E1, E2 (`recallAt5`) |
| Presentation | 10 | 5 auto / 5 manual | `.pptx` downloadable; every slide citation exists in the answer's sources (auto); opens cleanly and reads like a real deck (manual) | E3 (human, not model, judges the deck) |
| Image generation | 10 | auto | `gpt-image-1` artifact ready with `costUsd` and `promptUsed`; cap → `429`; `DRY_RUN` path works | R2, B3 |
| Performance & SLA | 10 | auto | `bench.mjs` exits 0 | B1, B2, B3, A2, A3 |
| Observability | 5 | auto | Request id correlates both logs; `/stats` reconciles with the log; trace explains citations | A1 |
| Human gate & answer quality | 5 | manual | Learner names one successful and one failing trajectory they read end to end (P1) and what each taught them; grader reads five sampled answers: concise, on-question, honest when retrieval is thin | P1 |
| Deploy & docs | 5 | manual | Both services on Fly.io against an Atlas cluster; UI works against the public gateway; `npm run dev` brings everything up locally; `.env.example`; run notes |, |

**Red lines (auto-flagged):** secrets committed · provided `web/` or `benchmark/` edited · any fabricated citation in the bench sample (E2) · a `2xx` answer served on a provider exception (A1) · a run that hit a cap reported as `done` (A2) · `generate_image` called from the ask path (R2).

**Bonus (+5):** the learner hits a failure the rules do not yet cover and submits it as a new rule, one executable sentence, the real incident as precedent, a self-check question, to the cohort's `rules.json`. This is the highest-value exercise in the assignment because it is the actual job.

## 13 · Quality bar: how "done" is proven

This assignment is graded under the cohort's quality bar (`QUALITY_BAR.md`). Four laws, applied to LUMINA:

1. **A thing that ran is not a thing that worked.** A streamed answer with a green `done` proves the process did not crash. Grounding, recall, budget, and termination are what prove it worked.
2. **Assert from declared numbers, never from detection.** Every gating threshold in this PRD is arithmetic against a run log or an eval report. No error-severity check asks a model for its opinion. An LLM judge may *report* on tone or helpfulness at `warn`; it may never block.
3. **Every rule cites the failure that created it.** Rule IDs below refer to the cohort `rules.json`. One real precedent this assignment already owns: the Live Translate silent-fallback bug recorded in `FDE-01-assignments/Assignment_1_Live_Translate/AGENTS.md` (a dependency mismatch made every LLM call throw, the `except` returned the input untouched, and the "translator" served English for weeks). That is rule **A1**'s precedent and should replace its `TODO`. Do not invent others.
4. **Gates run in order, and each one blocks.** `eval.mjs` runs the gates below top to bottom and stops at the first failure.

### Declared expectations (write these before the first run)

`expectations.json` at the assignment root, in the checker's schema. Numbers set after seeing a score are not thresholds.

```jsonc
{
  "$comment": "LUMINA, declared before the first run. Asserted by arithmetic via quality/check.mjs.",
  "project": "LUMINA",
  "quality": { "rules": true, "budget": true },

  "budget": {
    "maxTokensPerRun": 40000,      // B1, one answer: plan + ≤4 fetched pages + synthesis
    "maxToolCalls": 8,             // the loop's hard cap (§5.1)
    "maxWallClockSec": 90,         // B2, the loop's hard cap; the p95 SLA of 12 s lives in sla.json
    "maxCostUsd": 0.05             // B3, per answer, at the provider rates in sla.json
  },

  "trajectory": {
    "mustCallTools": [],                                    // retrieval is asserted by retrievalRate below (web OR docs)
    "mustNotCallTools": ["generate_image", "make_presentation"],  // R2, the ask path never spends on artifacts
    "maxConsecutiveSameTool": 3,                            // A3, thrash guard
    "mustTerminate": true                                   // A2, terminated must be "done"
  },

  "eval": {
    "goldSetPath": "eval/gold/rag_gold.jsonl",   // E1, ≥ 30 items, provided
    "minCitationGrounding": 0.95,                // E2, share of [n] whose snippet is found in the fetched page / indexed chunk
    "minRecallAt5": 0.70,                        // E2, over the gold set
    "minRetrievalRate": 1.0,                     // E2, share of answers whose run called web_search or search_documents at least once
    "maxErrorRate": 0.01                         // E2, 5xx share across the bench workload
  }
}
```

`bench.mjs` writes `reports/eval.json` with exactly those metric names (`citationGrounding`, `recallAt5`, `retrievalRate`, `errorRate`), and the agent service writes one `runs/<requestId>.json` per answer (`npm run export:runs` also dumps the `runs` collection into that folder for a deployed instance):

```json
{ "tokens": 18240, "wallClockSec": 6.4, "costUsd": 0.021, "terminated": "done",
  "toolCalls": [ { "name": "web_search", "ok": true }, { "name": "fetch_page", "ok": true },
                 { "name": "fetch_page", "ok": false, "error": "403 from publisher" }, { "name": "fetch_page", "ok": true } ] }
```

A failed call **must** carry a non-empty `error` (A1). `terminated` is `"done"`, `"cap"`, or `"error"`: set explicitly at the call site, because no SDK gives it to you.

### The gates

| Gate | Name | What runs | Blocks on |
|---|---|---|---|
| 0 | STATIC | `npm run lint && npm run typecheck` clean; `git status` has no `.env`, `runs/`, or `reports/` | any finding |
| 1 | CONTRACT | `node quality/check.mjs .` → **C1**: budgets positive, ratios in 0..1, gold set path exists, no tool both required and forbidden | C1 fail |
| 2 | RUN | `node benchmark/bench.mjs --smoke`: five queries complete inside `budget` with `terminated: "done"` | any run over budget or not done |
| 3 | TRAJECTORY | `check.mjs` over `runs/` → **A1, A2, A3, R2** | any error-severity fail |
| 4 | EVAL | full `node benchmark/bench.mjs` → `reports/eval.json` → **E1, E2** (grounding, recall, retrieval rate, error rate) + SLA percentiles in `sla.json` | any threshold missed |
| 5 | HUMAN | **P1**: the learner reads one complete successful trajectory and one complete failing trajectory, every step, and names both in `PRODUCT_EVAL.md` | cannot be automated or removed |

Exit codes follow the kit: `0` pass or not opted in, `1` warnings only, `2` at least one error. CI fails on `2`; `1` stays visible. **P2** (rules still carrying `TODO` precedents) will warn until the cohort fills them, that nag is intentional.

### Read the trajectory, not the answer

Before sign-off, for one successful and one failing run:

- [ ] Each tool call was the one you would have made.
- [ ] Every error in the log surfaced to the model as an error (`ok: false` + `error`), and to the user as `502` or a marked partial.
- [ ] The loop terminated because it was done, not because it hit a cap.
- [ ] Token, latency, and cost match `expectations.json`, checked against the numbers, not eyeballed.
- [ ] Every citation in the answer traces to a `fetch_page` or `search_documents` result in the same run.

If you cannot produce a failing trajectory, you do not understand the failure surface yet. Kill the search provider's key and run again.

## 14 · Build order: two weeks

**Day 0, scaffold (provided).** `npm install` at the root installs the workspace: `web/`, `backend/gateway/`, `backend/agent/`, `packages/contract/`, `benchmark/`, `eval/`, `quality/`. `npm run dev` starts both services and the UI with hot reload against the Atlas URI in `.env`.

**Week 1, the loop, search, streaming, memory**
1. Agent service skeleton: `/health` (reports Mongo ping and vector backend), the loop with `web_search` + `fetch_page`, SSE `trace → sources → token → done`. Test with `curl -N`. Confirm you disabled compression and flush after every event.
2. Search cache: in-process LRU in front of `searchCache` with its TTL index; `searchCached` in `done`.
3. Gateway: CORS, `X-User-Id`, request id, `pino` request log, zod validation from `packages/contract`, SSE pass-through, serve `web/dist`.
4. `threads` + `messages` persisted; follow-ups work.
5. Long-term memory: `save_memory` / `recall_memory` over the `memories` vector index; `/memory` list + delete.
6. **Checkpoint demo:** cited streamed answer in the UI; a preference carries across threads; one `runs/*.json` exists and `node quality/check.mjs .` reads it.

**Week 2, documents, artifacts, proof, deploy**
7. Spaces + the `jobs` worker: upload → GridFS → `pending` → parse (`pdfjs-dist`) → chunk → embed → `chunks` upsert → read-your-write probe → `indexed`. Router `auto`.
8. Hybrid retrieval: `$vectorSearch` + `$search` fused with RRF; page locators in citations.
9. Deck artifact: outline JSON → `pptxgenjs`; grounding check on slide citations.
10. Image artifact with `gpt-image-1`, daily cap, `DRY_RUN`.
11. Write `expectations.json` **before** running the bench. Then `node benchmark/bench.mjs` green against `sla.json` and `check.mjs` exit ≤ 1; fix what they catch. A first run that passes everything usually means the thresholds were set after seeing the scores.
12. Deploy both services to Fly.io (`fly launch` per service, secrets via `fly secrets set`); Atlas stays where it is; point the UI at the public gateway.
13. Run the eval skill → `PRODUCT_EVAL.md`; record the 60–90 s demo.

## 15 · Provided vs. built (what the course must ship before Week 1)

| Component | Status | Path |
|---|---|---|
| Workspace scaffold: root `package.json` with npm workspaces, `npm run dev`, `docker-compose.yml` (local `mongod`), `.env.example`, lint + typecheck config | ✅ Provided, **to be built by course staff** | repo root |
| `packages/contract/`: zod schemas + TypeScript types for every route, SSE event, and collection document in §7 and §8 | ✅ Provided, **to be built** | `packages/contract/` |
| Web UI (React 18 + Vite, imports the contract types): query, streaming answer with citation chips, sources rail, thread list, memory panel, Spaces upload, deck/image actions with polling | ✅ Provided, **to be built** | `web/` |
| Empty Express skeletons for both services with `/health` returning `501` on everything else, so the UI's "not implemented yet" state is the learner's progress bar | ✅ Provided, **to be built** | `backend/gateway/`, `backend/agent/` |
| Atlas setup guide + `scripts/create-indexes.mjs` that creates the vector, search, and TTL indexes from one JSON definition | ✅ Provided, **to be built** | `scripts/` |
| `benchmark/sla.json` (declared targets, cost model, workload) | ✅ Written | `benchmark/sla.json` |
| `benchmark/bench.mjs` (latency, grounding, recall, cache, cost; reads `sla.json`) | ✅ Provided, **to be built** | `benchmark/` |
| RAG gold set: a 30-question JSONL + a small corpus (3–5 PDFs, CC-licensed) | ✅ Provided, **to be built** | `eval/gold/` |
| `eval/rubric.json` (FDE schema: automated / manual / stretch_bonus / red_lines, mapped to rule ids) and `expectations.json` (§13) | ✅ Written | `eval/rubric.json`, `expectations.json` |
| `eval/eval.mjs` + the `/fde-lumina-eval` skill, running the six gates in order | ✅ Provided, **to be built** | `eval/`, `.claude/skills/` |
| Public copy of the quality kit (`check.mjs`, `rules.json` with only publishable precedents, `expectations.example.json`) | ✅ Provided, **to be promoted from the cohort folder** | `quality/` |
| `AGENTS.md` (non-negotiables) and `README.md` (the build guide in the FDE house structure) | ✅ Written; add the track's reading-assignment tripwire if you want it | assignment root |
| Express gateway: CORS, auth header, request id, logging, validation, rate limit, SSE pass-through | 🔨 Learner | `backend/gateway/` |
| Express agent service: loop, tools, memory, RAG, `jobs` worker, artifacts, run logs | 🔨 Learner | `backend/agent/` |

**Reference app note.** Alex, the Perplexity-style reference app in this module, is FastAPI + vanilla JS. It is the reference for *behavior* (the four levels, the trace panel, grounded citations), not for stack. Read it to learn what LUMINA should feel like; build LUMINA in MERN.

## 16 · Risks & assumptions

| Risk | Mitigation |
|---|---|
| Fetching full pages hits paywalls, robots, JS-rendered sites | Tavily `extract` as the default reader; fall back to snippet-only with the trace marking it, scored lower not failed |
| `gpt-image-1` requires organization verification on OpenAI; some learners blocked | `DRY_RUN` path is graded as pass for the flow; real generation earns the cost-logging points; allow an alternative image API if named in `/health` |
| Search API cost across 40 learners × bench runs | Cache is mandatory and the bench workload is 50 % repeats by design; Tavily free tier covers a learner's two weeks |
| Grounding check by verbatim snippet match is brittle to whitespace/quotes | Normalize (case, whitespace, punctuation) before matching; require ≥ 12 consecutive matching tokens rather than exact snippet equality |
| Two weeks is tight for five capabilities | Deck and image are thin by design (one outline → one renderer; one API call behind a gate); RAG is the biggest lift and gets Week 2's first three days |
| Learners hard-code one provider | `/health` must name provider and store; the eval flips `SEARCH_PROVIDER` for one call |
| Atlas Search indexes are eventually consistent; a document marked `indexed` is not yet searchable | The read-your-write probe in §5.4 is a Must; the bench queries a freshly indexed document and fails the run if it is invisible |
| Free-tier Atlas (M0) allows 3 search indexes and 512 MB | LUMINA needs exactly 3 (memories vector, chunks vector, chunks text); the gold corpus is small; document the limit and how to upgrade |
| Express buffers SSE through `compression` and some proxies | The scaffold ships the gateway with compression disabled on `/threads/*/ask` and `X-Accel-Buffering: no`; the bench measures TTFT through the gateway so buffering shows up as a failed SLA, not a mystery |
| Node's single thread stalls the SSE stream while the worker parses a large PDF | The worker runs in a `worker_threads` pool or a second process (`npm run worker`); the bench's decoupling check (search p95 during ingest) catches a blocking implementation |
| Mongoose schemas drift from the zod contract | zod is the source of truth; the UI compiles against the same types, so drift fails `npm run typecheck` before it fails a learner |

**Assumptions:** learners have an LLM key, a Tavily or SerpApi key, and an OpenAI key for embeddings and images; a free Atlas M0 cluster per learner is enough for two weeks; Fly.io free tier suffices for two small Node services; the provided UI, contract package, and scaffold can be built by staff in one week from this PRD.

## 17 · Open questions

1. **Live Translate's slot.** LUMINA replaces it as Assignment 1. Move `Assignment_1_Live_Translate` to a bonus, or retire it? *(Owner: Hamza)*
2. **Provide the UI or have learners build it?** This PRD provides it, matching A1's "the widget is the acceptance test." The FDE pitch says "you build the frontend." Building it is a natural stretch goal; decide before the UI work starts. *(Owner: Hamza)*
3. **Atlas Vector Search vs. a separate vector store.** This PRD picks Atlas so MERN stays literally MERN and a citation is one document. ARGUS uses Qdrant, so learners meet a dedicated vector DB in Week 3 anyway. Confirm, or allow Qdrant as a named alternative in `/health`.
4. **Image alternative** if `gpt-image-1` access is a blocker for many: allow Gemini image generation as a named alternative?
5. **Deck format:** `.pptx` only, or also an HTML deck the UI can preview? PRD says `.pptx` required, HTML stretch.
6. **Quality kit distribution.** Learners need `check.mjs` and `rules.json` in the assignment, but the cohort copy lives in a local-only folder and its precedents may name clients and costs. Promote a scrubbed copy into `quality/` before Week 1. *(Owner: Hamza)*
7. **TypeScript or JavaScript?** The scaffold is TypeScript because the contract types are the point. Learners who insist on plain JS can, but they lose the typecheck gate. Recommendation: TypeScript required for `packages/contract`, optional elsewhere.
8. **Gold corpus content.** Which 3–5 public PDFs? Suggest arXiv RAG papers so the Space demo overlaps Module 3.

## 18 · Stretch goals

- **Subagent split** (Week 2 material): planner → researcher(s) in parallel → writer, with isolated contexts; show the trace tree.
- **Pro search:** query decomposition + per-sub-question retrieval + merged citations.
- **Semantic answer cache with freshness guard** (Module 3's semantic cache): cached answers for non-time-sensitive repeats, with `answerCached: true`.
- **Learner-built UI** replacing `web/`, still passing the contract.
- **Own search:** SearXNG behind the same `web_search` tool.
- **Share links** for a thread; export a thread to Markdown.
- **Dockerize** both services with `docker compose up`; GitHub Action running `node benchmark/bench.mjs` and `fly deploy` on green.
- **Learner-built UI in Next.js** on Vercel, still passing the contract, with the gateway as its API route target.
- **Change streams** on `artifacts` to push status to the UI over the existing SSE channel instead of polling.

## 19 · Submission

One **Vercel URL**, per [`SUBMISSION.md`](../../../SUBMISSION.md). The UI deploys to Vercel; the services run on Fly.io or Vercel against Atlas.

1. The `/fde-lumina-eval` skill runs the six gates (`check.mjs`, `bench.mjs`, `eval.mjs`) against the **deployed** gateway, collects the video link and the two trajectories read for P1, and writes `report.json`, served at `GET /evals/report.json`. The provided UI renders it at `/evals`.
2. The **60 to 90 s recording** embedded there shows: a fresh question streams with citations; a memory carries into a new thread; a document question cites a page; the deck downloads and opens; an image generates and `/stats` shows its cost.
3. The repo is public, first commit `DESIGN.md`, no `.env`, `node_modules/`, `runs/`, or `reports/`; a short "How I ran it" notes the LLM, search provider, and Atlas tier.
