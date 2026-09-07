# PRD, Assignment 1: LUMINA (Perplexity-style AI search)

| | |
|---|---|
| **Project** | 01 · LUMINA, a Perplexity clone: it searches, searches *deeply* when a question has parts, remembers you, and reads your documents |
| **Track** | FDE Agent Engineering Bootcamp, cohort 2026-03 |
| **Kicks off** | Week 1 (Agent Foundations, Harness & System Design) · due end of Week 2 |
| **Owner** | Hamza Farooq |
| **Status** | Draft v0.3, 2026-09-07 (two-gear revision: deep search in, deck and image out) |
| **Stack** | **MERN**: MongoDB Atlas (documents, memory, cache, jobs, and vectors via Atlas Vector Search) · Express (two Node services) · React (the provided UI) · Node end to end, including the bench, the eval, and the quality checker |
| **Lives in** | `modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/`: the Week 1 project ships with the Week 1 module |
| **Replaces** | FDE Assignment 1, Live Translate (see Open Questions) |

> **One line:** ask a question, get a streamed, cited answer built from live web search and your own documents; ask a harder one and it decomposes the question, researches each part, and merges the citations; it remembers you across sessions. Two Express services, one MongoDB, one fixed contract, one deploy, one benchmark that must pass.

> **Two gears.** `depth: "quick"` is the default: one pass, a couple of searches, a cited answer in seconds. `depth: "deep"` is Perplexity's Pro Search: plan sub-questions, research each, merge everything into one citation numbering. Quick is what keeps the product economic; deep is what makes it worth using on a real question. Building both is the assignment, and *knowing which one a question deserves* is the lesson.

---

## 1 · Problem

Perplexity is the clearest example of what a production agent loop looks like from the outside: a query goes in, the system *decides* what to search, reads, and answers with citations you can click. Learners in Week 1 are taught that loop. LUMINA makes them ship it, as a product, not a notebook.

It also front-loads four capabilities every later project depends on:

| Capability | Where it comes back |
|---|---|
| Tool-using agent loop with a trace | Every project; the harness is the course |
| Web search as a tool the agent chooses | ARGUS (retrieval decisions), EPYHIA (research) |
| Memory (thread + long-term) | Module 2 memory; VOXA conversation state |
| RAG over user documents with page-level citations | ARGUS extends exactly this contract |
| Query decomposition and merged citations (deep search) | Module 3 Pro-search & re-ranking; EPYHIA research |

Same FDE shape as before: a fixed contract, a provided UI that is the acceptance test, two backend services you own, an SLA you prove with a benchmark, a real deploy. New this cohort: the whole thing is **one language**. React in front, Express behind, MongoDB underneath, and Node for the bench, the eval, and the quality checker, so a learner never context-switches between a JS frontend and a Python backend to debug one request.

## 2 · Goals

1. **Ship a working answer engine in two weeks.** Fresh clone → follow README → provided UI lights up against the learner's backend, locally and on Fly.io.
2. **Every claim is grounded.** ≥ 95 % of inline citations resolve to a source the system actually retrieved in that request. Fabricated sources are an automatic fail.
3. **Prove it by arithmetic.** `benchmark/bench.mjs` exits 0 against declared numbers in `sla.json`; no threshold is judged by a model.
4. **Make cost visible and gated.** Every answer logs tokens, latency, and USD; `/stats` reports the day's spend; deep search — several times the price of quick — sits behind a per-user daily cap enforced server-side.
5. **Teach the two gears.** Most questions do not need six sub-questions and twelve fetched pages. A product that answers every question as though it did is slow and uneconomic; one that never digs is useless on a real question. Learners ship both and have to defend the default.
6. **Teach the async pattern early.** Document ingestion is a `202`-then-worker path, so ARGUS's queue is not the first time learners meet it.

## 3 · Non-goals

- No user accounts, OAuth, or billing. Identity is a dev header (`X-User-Id`); the gateway rejects requests without it.
- No browsing agent that clicks or fills forms. Search + fetch + read only.
- No voice (VOXA), no video ingestion (ARGUS), no autonomous side effects such as sending or publishing (EPYHIA).
- No fine-tuning, no self-hosted models required. Provider-swappable via env is enough.
- No answer caching. Search *results* are cached with a TTL; answers are always regenerated so freshness is never served stale.
- **No artifact generation.** No slide decks, no image generation. They were 20 points of thin API-call-behind-a-cap in an earlier draft and they crowded out the loop; deep search took the room. EPYHIA can generate things.
- No multi-agent split *required*. Deep search may run its sub-questions sequentially in one context; doing it as parallel isolated subagents is the Week 2 stretch goal.

## 4 · Users & scenarios

**Learner** (builds it), **grader** (runs the eval), **end user** (the person typing questions, in the demo, the learner).

*Scenario A, fresh question.* Alex types "What changed in the EU AI Act's GPAI obligations this summer?" LUMINA plans two searches, fetches four pages, streams a five-sentence answer with `[1]`–`[4]`, and shows the sources rail. Alex clicks `[2]` and lands on the cited paragraph.

*Scenario B, memory.* A week earlier Alex told LUMINA "I build in TypeScript and want code examples, not prose." Today, in a new thread, "how do I call Tavily?" returns a TypeScript snippet first. Alex opens the Memory panel, sees that stored preference, and deletes it.

*Scenario C, own documents.* Alex uploads three PDFs into a Space called "Q3 board pack" and asks "what did we commit to on churn?" The router chooses documents over web, and the answer cites `board-deck.pdf, p. 14`. Alex then asks "and what does the market say?", the router now blends web and docs, citations of both kinds appear.

*Scenario D, deep search.* Alex asks "should we move our RAG stack off Atlas Vector Search onto a dedicated vector DB?" — a question with at least four parts. Alex flips the toggle to **Deep**. Within two seconds the Plan panel lists five sub-questions (cost at our scale, page-level citation support, operational burden of a second store, migration cost, what changes at 10× the corpus), each with a one-line reason. Alex disagrees with the fifth, but the search is already running: trace steps stream in tagged `3`, `3`, `1`, `4`, sources accumulate with the sub-question that found them, and fifty seconds later a structured answer arrives citing `[1]`–`[14]`, every number resolving. `/stats` shows the run cost $0.21 and that Alex has four deep searches left today.

*Scenario E, the cheap gear is the default.* Alex asks "what port does mongod listen on?" and leaves the toggle on Quick. One search, one fetch, one sentence, $0.004, under two seconds. Nobody decomposed anything. This scenario is in the PRD on purpose: a system that runs Scenario D's machinery on Scenario E's question has failed at the thing this assignment teaches.

## 5 · Requirements

Grouped by the four capabilities plus the loop that ties them together. **Must** rows are graded; **Should** rows are expected of a strong submission; **Could** rows are stretch.

### 5.1 The agent loop (the harness)

| Pri | Requirement |
|---|---|
| Must | One loop: plan → choose tool → observe → repeat → answer. Tools: `web_search`, `fetch_page`, `search_documents`, `recall_memory`, `save_memory`, and — **deep only** — `plan_research`. A quick search that calls `plan_research` has escalated itself into a run costing several times more, which is the spend failure this separation exists to prevent. |
| Must | Bounded, per gear: **quick** 8 tool calls / 90 s, **deep** 24 tool calls / 240 s. Hitting a cap returns an honest partial answer with `terminated: "cap"` in the `done` event, never a fabricated complete one. A provider exception ends the run with `terminated: "error"` and a `502`. |
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
| Must | **Thread memory:** every thread persists its messages, citations, and (for a deep search) the plan it ran; a follow-up question sees the whole thread. |
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
| Must | Meets `min_recall_at_5` on the provided gold set (39 questions over the provided corpus, see §9). |
| Should | Router blends web and documents in one answer when both are relevant, with mixed `kind` in `sources`. |
| Could | Re-index on document replace; delete a document and prove its chunks are gone. |

### 5.5 Deep search (Perplexity's Pro Search)

The second gear, and where 15 of the 100 points now live. Everything in 5.1 to 5.4 still
applies to a deep search; this section is only what deep adds.

| Pri | Requirement |
|---|---|
| Must | `POST /threads/{id}/ask {depth: "deep"}`. `depth` defaults to `"quick"`, and the server never upgrades a request on its own: deep is opted into, never drifted into. |
| Must | `plan_research` decomposes the question into `DEEP_SUB_QUESTIONS_MIN`–`MAX` (default 3–6) sub-questions, each with a one-line reason. A plan of two sub-questions is a quick search with extra steps and is scored as one. |
| Must | The `plan` SSE event is emitted **before any retrieval happens**. It is deep search's real first paint — `deep_plan_p95_ms` ≤ 4 000 — and a plan streamed after the fetches is a rationalisation, not a plan. |
| Must | Each sub-question is researched with the same tools as a quick search. Every `trace` step carries the `subQuestion` index it is serving, so a reader can follow one thread of the research through the log. |
| Must | Results are merged into **one citation numbering** across all sub-questions: duplicates deduped by URL (or `docId` + locator), numbering contiguous from 1, and every `[n]` in the answer resolving to exactly one entry. Each source carries the `subQuestion` that found it. |
| Must | A deep answer retrieves at least `min_deep_source_ratio` (2×) the distinct sources of the *same question* answered quick. Deep that reads no more than quick is only slower, and the bench measures exactly this by running both. |
| Must | **Spend gate:** `DEEP_DAILY_CAP` (default 5) per `X-User-Id`, enforced in the agent service; over cap → `429 {error, resetsAt}`. Deep is allowed to cost about 7× quick (`max_cost_per_deep_answer_usd` $0.35) and is not allowed to be unbounded. |
| Must | `done` carries `depth` and `subQuestions`, and the run log carries `depth`, so a legitimately expensive deep run is distinguishable from a quick run that ran away with the budget. |
| Should | The answer is *structured* — a short direct answer, then a section per sub-question, then what is still unknown. Deep search that returns one long paragraph has wasted the decomposition. |
| Should | Sub-questions are researched in parallel, bounded by a concurrency limit, so wall clock is not the sum of the parts. |
| Could | A follow-up that narrows to one sub-question reuses that sub-question's already-fetched pages instead of re-fetching. |
| Could | Show the plan *before* running and let the user edit or drop a sub-question — Perplexity does not do this and it is obviously better. |

**Why this replaced the deck and the image.** Those were two API calls behind a cap: they
taught the async pattern (which document ingestion already teaches) and the spend gate (which
deep search now carries), and cost 20 points that were not buying loop skill. Deep search is the
same 20 points spent on query decomposition, fan-out, result merging, and citation bookkeeping —
the things that actually distinguish an answer engine from a search box, and the things Module 3
builds on.

## 6 · Architecture

Same split as every FDE project: the browser only ever talks to the gateway; provider keys live only in the agent service. Both services are Express on Node 20 with TypeScript; one MongoDB Atlas cluster holds everything, including the vectors.

```
  ┌──────────────────────────────┐
  │  Web UI  (web/)              │  ← PROVIDED · React 18 + Vite · the acceptance test
  │  query · quick/deep toggle   │     types imported from packages/contract
  │  stream · citations · plan   │
  │  memory panel · spaces       │
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
  │  loop · router · depth gear  │
  │  planner · fan-out · merge   │
  │  memory · RAG · jobs worker  │
  └───┬──────┬──────────┬────────┘
      ▼      ▼          ▼
   Search   LLM +    MongoDB Atlas ─────────────────────────────────────────────
  (Tavily/  embed    threads · messages · memories(vector idx) · spaces · documents
  SerpApi) (env-     chunks(vector idx + text idx) · searchCache(TTL idx) · jobs
            swap)    requests · runs · GridFS (uploads)
```

**Why MERN here.** Three reasons, and none is "it's popular":
1. **One request, one language.** The trace a learner reads in the UI and the loop that produced it are both TypeScript. Debugging a citation from chip to `$vectorSearch` never crosses a language boundary.
2. **One database, including vectors.** Atlas Vector Search puts embeddings in the same collection as the chunk text and its locator, so a citation is one document, not a join across a vector store and a relational table. The `spaceId` filter is a plain query predicate.
3. **The quality kit is already Node.** `check.mjs` reads `runs/*.json`; the agent service writes them natively. The bench and eval are `.mjs` too, so the six gates run with `node` and nothing else installed.

**Why the gateway still matters.** SSE pass-through, per-user rate limiting, and contract validation are the concerns you want on the edge, away from the keys. (The deep-search cap is deliberately *not* here: it is a spend gate on a provider call, so it belongs next to the spending, in the agent service. A cap on the edge is a cap you can bypass by reaching the agent service directly.) It is also where you learn that Express buffers SSE by default unless you flush and disable compression.

**Async inside one service, backed by MongoDB.** Document indexing is a row in a `jobs` collection. (Deep search is *not*: it streams over the same SSE channel as a quick answer, because someone waiting on a minute of research wants to watch it work, not poll a job id.) The API inserts `{kind, status: "pending", payload}` and returns `202`. A worker loop in the agent service claims work with an atomic `findOneAndUpdate({status: "pending"}, {$set: {status: "running", claimedAt, workerId}})`, does the job, and only then flips the target document's status. Crash mid-job and the row stays `running` with a stale `claimedAt`; a sweeper returns it to `pending`. No Redis, no broker. ARGUS swaps Prefect in against the same contract.

## 7 · API contract (fixed: the UI speaks this)

All routes on the gateway; the gateway forwards the same shapes to the AI service. `X-User-Id` required on every route except `/health`.

```jsonc
POST /threads                       → 201 { "threadId": "thr_…" }
GET  /threads/{id}                  → 200 { "messages": [ { "role", "content", "sources": [...], "answerId"?, "subQuestions"? } ] }

POST /threads/{id}/ask              // body: { "query": "…", "mode": "auto" | "web" | "docs",
                                    //          "depth": "quick" | "deep",   // default "quick"
                                    //          "spaceId": "spc_…"? }
  → 200 text/event-stream
  // `plan` is DEEP ONLY, arrives first, and must precede any retrieval:
  event: plan     data: { "subQuestions": [ { "i": 1, "question": "…", "reason": "…" }, … ],
                          "reason": "…" }
  event: trace    data: { "step": 1, "tool": "web_search", "input": {...}, "ok": true, "ms": 812,
                          "reason": "…", "subQuestion": 1 }        // subQuestion on deep runs
  event: sources  data: [ { "n": 1, "kind": "web", "title": "…", "url": "…", "snippet": "…", "subQuestion": 1 },
                          { "n": 2, "kind": "doc", "docId": "doc_…", "title": "board-deck.pdf", "locator": { "page": 14 }, "snippet": "…" } ]
  event: token    data: { "text": "…" }
  event: done     data: { "answerId": "ans_…", "latencyMs": 6410, "ttftMs": 1830, "model": "…",
                          "tokens": { "in": 9120, "out": 410 }, "costUsd": 0.021,
                          "searchCached": false, "terminated": "done" | "cap" | "error",
                          "depth": "quick" | "deep", "subQuestions": 0 }
  event: error    data: { "status": 502, "error": "search provider 503" }

GET    /memory                      → 200 { "memories": [ { "id", "text", "sourceThread", "createdAt" } ] }
DELETE /memory/{id}                 → 204

POST /spaces                        → 201 { "spaceId": "spc_…", "name": "…" }
POST /spaces/{id}/documents         // multipart file   → 202 { "docId": "doc_…", "status": "pending" }
GET  /spaces/{id}/documents         → 200 { "documents": [ { "docId", "title", "status", "pct", "pages"? , "error"? } ] }

GET  /health                        → 200 { "status": "ok", "model": "…", "searchProvider": "tavily", "vectorStore": "atlas-vector-search", "db": "ok", "ai": { "status": "ok" } }
GET  /evals/report.json             → 200 { "assignment", "student", "repo", "video", "deployedAt", "rubric", "bench", "quality", "trajectories" }  // written by the eval skill, rendered by the UI at /evals
GET  /stats                         → 200 { "requests": 412, "answers": 130, "searchCacheHitRatePct": 58.1, "ttftP95Ms": 1910,
                                            "costUsdToday": 3.12, "deepToday": 2, "deepDailyCap": 5 }
```

**Status codes:** `400` invalid input · `401` missing `X-User-Id` · `404` unknown thread/space/document · `413` file too large · `429` rate limit or deep-search cap · `501` not implemented · `502` upstream (LLM, search) failure.

**Contract rules that matter**
- Every `[n]` in streamed text has a matching `n` in `sources` for that answer. Extra or missing → grounding failure.
- `sources` is sent **before** the first `token`, so the UI can render chips as text arrives.
- On a deep search, `plan` is sent **before any retrieval**, and every `trace` step and `source` carries the `subQuestion` it served.
- `depth` defaults to `"quick"`. The server reports in `done` which gear it actually ran, and it never upgrades a request by itself.
- `202` endpoints return in < 300 ms; the work happens after.
- `latencyMs`, `ttftMs`, `costUsd` are measured server-side.

## 8 · Data model (MongoDB)

One database, `lumina`. Every document carries `userId` (from `X-User-Id`) and `createdAt`. Ids are prefixed strings (`thr_`, `ans_`, `doc_`, `art_`) generated in the app so they are readable in logs and URLs.

| Collection | Key fields | Indexes |
|---|---|---|
| `threads` | `_id, userId, title, createdAt` | `{userId: 1, createdAt: -1}` |
| `messages` | `_id, threadId, role, content, sources[], done{}, subQuestions[]?, createdAt` | `{threadId: 1, createdAt: 1}` |
| `memories` | `_id, userId, text, embedding[1536], sourceThread, createdAt` | **vector** on `embedding` (cosine) with `userId` as a filter field |
| `spaces` | `_id, userId, name, createdAt` | `{userId: 1}` |
| `documents` | `_id, spaceId, userId, title, status, pct, pages, error, fileId (GridFS), createdAt` | `{spaceId: 1}` |
| `chunks` | `_id, docId, spaceId, text, locator{page \| heading \| line}, embedding[1536]` | **vector** on `embedding` with `spaceId` filter; **search** (BM25) on `text` |
| `searchCache` | `_id (sha256 of query+provider), provider, results[], expiresAt` | `{expiresAt: 1}` **TTL** `expireAfterSeconds: 0` |
| `jobs` | `_id, kind (index_document), status, payload, claimedAt, workerId, attempts, error` | `{status: 1, createdAt: 1}`, `{status: 1, claimedAt: 1}` |
| `requests` | `requestId, userId, route, status, ms, tokensIn, tokensOut, costUsd, toolCalls, terminated, depth, createdAt` | `{createdAt: -1}`, `{requestId: 1}` |
| `runs` | the exact `runs/<requestId>.json` shape from §13, plus `requestId` | `{createdAt: -1}` |
| GridFS `uploads` | raw uploaded PDFs / MD / TXT | default |

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
| Deep search: time to plan, p95 | ≤ 4 000 ms | deep's real first paint; a minute of silence reads as broken |
| Deep search: full answer, p95 | ≤ 90 s | Perplexity-class research takes a minute, not five |
| Deep search: sub-questions (min) | ≥ 3 | two is a quick search with extra steps |
| Deep / quick distinct-source ratio (min) | ≥ 2.0× | the same question, both gears. Deep that reads no more is only slower |
| Error rate | ≤ 1 % | |
| Cost per answer, quick (mean) | ≤ $0.05 | placeholder price table in `sla.json`; learners set provider rates |
| Cost per answer, deep (mean) | ≤ $0.35 | ~7× quick, and capped per user per day on top |

`bench.mjs` reports latency percentiles **per gear**, grounding rate, recall, cache hit rate, cost per quick and per deep answer, and projected monthly cost at the volume and deep fraction declared in `sla.json`. Averaging the two gears together is exactly how a slow quick search hides behind a fast deep one, so it does not.

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
6. **Indexing is async.** `202` in < 300 ms; the work runs from the `jobs` collection; status transitions are committed only after the work succeeds, and `indexed` only after the read-your-write probe.
7. **Deep spend is gated and opted into.** `DEEP_DAILY_CAP` enforced server-side in the agent service → `429 {error, resetsAt}`; cost logged per run; a quick search never calls `plan_research`. The server does not upgrade a request's depth on its own.
8. **Secrets from env, never committed.** `.env`, `node_modules/`, `web/dist/`, `runs/`, `reports/` are git-ignored. The Atlas connection string is a secret.
9. **Evidence over vibes.** Numbers in `PRODUCT_EVAL.md` come from a real `bench.mjs` run against the deployed app.

## 12 · Grading (100 pts): `eval/rubric.json`

| Area | Pts | Type | What earns them | Rules |
|---|---|---|---|---|
| UI lights up & contract | 10 | auto | Fresh clone → README → UI streams an answer through the gateway; all routes return the declared shapes and status codes | C1 |
| Search & cited answers | 20 | auto | Grounding ≥ 95 %; `sources` precedes tokens; pages fetched not just snippets; `searchCached` true on repeat | E2 (`citationGrounding`, `retrievalRate`) |
| Memory | 10 | auto | Preference saved in thread A observably changes thread B; `/memory` lists it; `DELETE` removes it and the effect disappears |, |
| RAG over documents | 15 | auto | Upload → `202` → `indexed`; doc citation with `page` locator; router picks docs when relevant; recall@5 ≥ 0.70 | E1, E2 (`recallAt5`) |
| Deep search | 15 | auto | `plan` before any retrieval with ≥ 3 sub-questions; every step and source tagged with its `subQuestion`; merged numbering contiguous and fully resolving; ≥ 2× the distinct sources of the same query run quick; inside the deep budget; cap + 1 → `429` with `resetsAt`; no quick run calls `plan_research` | E2, B3, R2 |
| Deep search quality | 5 | manual | A grader asks one question at both depths and reads both answers. Deep must be *better*, not merely longer: coverage, sources quick missed, sub-questions a person would have asked, no padding | E3 (human, not model, judges it) |
| Performance & SLA | 10 | auto | `bench.mjs` exits 0 | B1, B2, B3, A2, A3 |
| Observability | 5 | auto | Request id correlates both logs; `/stats` reconciles with the log; trace explains citations | A1 |
| Human gate & answer quality | 5 | manual | Learner names one successful and one failing trajectory they read end to end (P1) and what each taught them; grader reads five sampled answers: concise, on-question, honest when retrieval is thin | P1 |
| Deploy & docs | 5 | manual | Both services on Fly.io against an Atlas cluster; UI works against the public gateway; `npm run dev` brings everything up locally; `.env.example`; run notes |, |

**Red lines (auto-flagged):** secrets committed · provided `web/` or `benchmark/` edited · any fabricated citation in the bench sample (E2) · a `2xx` answer served on a provider exception (A1) · a run that hit a cap reported as `done` (A2) · `plan_research` called from a quick search (R2).

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

  // check.mjs applies ONE budget to every run log, so these are the DEEP envelope: the
  // widest a legitimate run may get. The tighter quick envelope is enforced per run by
  // bench.mjs, which can read `depth` off the run. Two tools, two jobs, nothing unenforced.
  "budget": {
    "maxTokensPerRun": 180000,     // B1, a deep run: plan + ~12 fetched pages + synthesis
    "maxToolCalls": 24,            // deep's hard cap (§5.1); quick's 8 is checked by bench.mjs
    "maxWallClockSec": 240,        // B2, deep's hard cap; the p95 SLAs live in sla.json
    "maxCostUsd": 0.35             // B3, per deep answer, at the provider rates in sla.json
  },

  "trajectory": {
    "mustCallTools": [],           // retrieval is asserted by retrievalRate below (web OR docs)
    "mustNotCallTools": [],        // see below: the one forbidden tool is forbidden per-depth
    "maxConsecutiveSameTool": 4,   // A3, thrash guard; deep legitimately fetches a few in a row
    "mustTerminate": true          // A2, terminated must be "done"
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
{ "tokens": 18240, "wallClockSec": 6.4, "costUsd": 0.021, "terminated": "done", "depth": "quick",
  "toolCalls": [ { "name": "web_search", "ok": true }, { "name": "fetch_page", "ok": true },
                 { "name": "fetch_page", "ok": false, "error": "403 from publisher" }, { "name": "fetch_page", "ok": true } ] }
```

A failed call **must** carry a non-empty `error` (A1). `terminated` is `"done"`, `"cap"`, or `"error"`: set explicitly at the call site, because no SDK gives it to you. `depth` is what lets a reader — and `bench.mjs` — tell a legitimately expensive deep run from a quick run that ran away.

**Why `mustNotCallTools` is empty.** The one forbidden tool, `plan_research`, is forbidden only to *quick* runs, and this file has no way to say "only quick". So R2's job is done by `bench.mjs`, which checks every quick run's trace for a `plan_research` step and fails the deep-search row and the red line if it finds one. Declaring `plan_research` globally forbidden would fail every legitimate deep search; declaring nothing and checking nothing would be worse. This is the honest third option, and it is the kind of gap you should expect to find and close in your own gates.

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

**Week 2, documents, deep search, proof, deploy**
7. Spaces + the `jobs` worker: upload → GridFS → `pending` → parse (`pdfjs-dist`) → chunk → embed → `chunks` upsert → read-your-write probe → `indexed`. Router `auto`.
8. Hybrid retrieval: `$vectorSearch` + `$search` fused with RRF; page locators in citations.
9. Deep search, part one: `plan_research` and the `plan` event. Stream it before you retrieve anything and read three plans out loud — if the sub-questions are not ones you would have asked, fix the prompt before you build the fan-out on top of it.
10. Deep search, part two: research each sub-question, merge into one citation numbering (dedupe by URL / `docId`+locator, renumber contiguously), tag every step and source with its `subQuestion`, synthesise a structured answer. Then the spend gate: `DEEP_DAILY_CAP` → `429`, and make sure a quick search cannot reach `plan_research`.
11. Write `expectations.json` **before** running the bench. Then `node benchmark/bench.mjs` green against `sla.json` and `check.mjs` exit ≤ 1; fix what they catch. A first run that passes everything usually means the thresholds were set after seeing the scores.
12. Deploy both services to Fly.io (`fly launch` per service, secrets via `fly secrets set`); Atlas stays where it is; point the UI at the public gateway.
13. Run `/fde-lumina-eval` against the deployed gateway → `report.json` at `/evals/report.json`; record the 60–90 s demo.

## 15 · Provided vs. built (what the course must ship before Week 1)

| Component | Status | Path |
|---|---|---|
| Workspace scaffold: root `package.json` with npm workspaces, `npm run dev`, `docker-compose.yml` (local `mongod`), `.env.example`, lint + typecheck config | ✅ **Built** | repo root |
| `packages/contract/`: zod schemas + TypeScript types for every route, SSE event, and collection document in §7 and §8 | ✅ **Built** | `packages/contract/` |
| Web UI (React 18 + Vite, imports the contract types): query, quick/deep toggle, streaming answer with citation chips, sources rail with sub-question attribution, plan panel, trace panel, thread list, memory panel, Spaces upload, `/evals` | ✅ **Built** | `web/` |
| Empty Express skeletons for both services with `/health` returning `501` on everything else, so the UI's "not implemented yet" state is the learner's progress bar | ✅ **Built** | `backend/gateway/`, `backend/agent/` |
| `scripts/create-indexes.mjs` (2 vector + 1 text + TTL from one JSON, `--status` to watch them build) and `scripts/export-runs.mjs` | ✅ **Built** | `scripts/` |
| `benchmark/sla.json` (declared targets, cost model, workload) | ✅ Written | `benchmark/sla.json` |
| `benchmark/bench.mjs` (per-gear latency, grounding, recall, cache, deep-vs-quick source ratio, decoupling, cost; reads `sla.json`) | ✅ **Built** | `benchmark/` |
| RAG gold set: 39 questions + a 4-document CC BY corpus (2 rendered to PDF with stable page numbers), a builder and a validator | ✅ **Built** | `eval/gold/` |
| `eval/rubric.json` (FDE schema: automated / manual / stretch_bonus / red_lines, mapped to rule ids) and `expectations.json` (§13) | ✅ Written | `eval/rubric.json`, `expectations.json` |
| `eval/eval.mjs` (six gates in order), `eval/build-report.mjs` (assembles `report.json` from run artifacts), and the `/fde-lumina-eval` skill | ✅ **Built** | `eval/`, `.claude/skills/` |
| Public copy of the quality kit (`check.mjs`, `rules.json` with A1's precedent filled from the Live Translate incident, `expectations.example.json`) | ✅ **Built** | `quality/` |
| `AGENTS.md` (non-negotiables) and `README.md` (the build guide in the FDE house structure) | ✅ Written; add the track's reading-assignment tripwire if you want it | assignment root |
| Express gateway: CORS, auth header, request id, logging, validation, rate limit, SSE pass-through | 🔨 Learner | `backend/gateway/` |
| Express agent service: the quick loop, deep search (planner, fan-out, merge), tools, memory, RAG, `jobs` worker, run logs | 🔨 Learner | `backend/agent/` |

**Reference app note.** Alex, the Perplexity-style reference app in this module, is FastAPI + vanilla JS. It is the reference for *behavior* (the four levels, the trace panel, grounded citations), not for stack. Read it to learn what LUMINA should feel like; build LUMINA in MERN.

## 16 · Risks & assumptions

| Risk | Mitigation |
|---|---|
| Fetching full pages hits paywalls, robots, JS-rendered sites | Tavily `extract` as the default reader; fall back to snippet-only with the trace marking it, scored lower not failed |
| Deep search is where a learner's bill runs away: six sub-questions × four fetches × a large context, on every request | Three defences, all required: the wider-but-finite cap (24 calls / 240 s), the per-user daily cap (`DEEP_DAILY_CAP` → `429`), and quick as the default with no server-side upgrade. The bench measures cost per gear separately so a deep-search blowout cannot hide in a blended average |
| A "deep" search that is only slower: same two searches, longer prose | `min_deep_source_ratio` — the bench runs the *same question* at both depths and requires deep to surface ≥ 2× the distinct sources. It is the one number that cannot be talked around |
| The planner writes sub-questions that are restatements of the question | `min_deep_sub_questions` (≥ 3) is necessary but not sufficient, so the human row (5 pts) is a grader reading one plan and asking whether a person would have asked those questions. Build order §14 step 9 makes the learner read three plans before building the fan-out |
| Search API cost across 40 learners × bench runs | Cache is mandatory and the bench workload is 50 % repeats by design; Tavily free tier covers a learner's two weeks |
| Grounding check by verbatim snippet match is brittle to whitespace/quotes | Normalize (case, whitespace, punctuation) before matching; require ≥ 12 consecutive matching tokens rather than exact snippet equality |
| Two weeks is tight for four capabilities | Deck and image generation were cut for exactly this reason: 20 points that bought two API calls. RAG is the biggest lift and gets Week 2's first three days; deep search reuses the quick loop's tools, so it is a fan-out and a merge rather than a new subsystem |
| Learners hard-code one provider | `/health` must name provider and store; the eval flips `SEARCH_PROVIDER` for one call |
| Atlas Search indexes are eventually consistent; a document marked `indexed` is not yet searchable | The read-your-write probe in §5.4 is a Must; the bench queries a freshly indexed document and fails the run if it is invisible |
| Free-tier Atlas (M0) allows 3 search indexes and 512 MB | LUMINA needs exactly 3 (memories vector, chunks vector, chunks text); the gold corpus is small; document the limit and how to upgrade |
| Express buffers SSE through `compression` and some proxies | The scaffold ships the gateway with compression disabled on `/threads/*/ask` and `X-Accel-Buffering: no`; the bench measures TTFT through the gateway so buffering shows up as a failed SLA, not a mystery |
| Node's single thread stalls the SSE stream while the worker parses a large PDF | The worker runs in a `worker_threads` pool or a second process (`npm run worker`); the bench's decoupling check (search p95 during ingest) catches a blocking implementation |
| Mongoose schemas drift from the zod contract | zod is the source of truth; the UI compiles against the same types, so drift fails `npm run typecheck` before it fails a learner |

**Assumptions:** learners have an LLM key, a Tavily or SerpApi key, and an OpenAI key for embeddings; a free Atlas M0 cluster per learner is enough for two weeks; Fly.io free tier suffices for two small Node services. The provided UI, contract package, scaffold, gold set and grader **are built** (§15) and were exercised end to end against a stub backend before Week 1.

## 17 · Open questions

1. **Live Translate's slot.** LUMINA replaces it as Assignment 1. Move `Assignment_1_Live_Translate` to a bonus, or retire it? *(Owner: Hamza)*
2. **Provide the UI or have learners build it?** This PRD provides it, matching A1's "the widget is the acceptance test." The FDE pitch says "you build the frontend." Building it is a natural stretch goal; decide before the UI work starts. *(Owner: Hamza)*
3. **Atlas Vector Search vs. a separate vector store.** This PRD picks Atlas so MERN stays literally MERN and a citation is one document. ARGUS uses Qdrant, so learners meet a dedicated vector DB in Week 3 anyway. Confirm, or allow Qdrant as a named alternative in `/health`.
4. **Deep-search concurrency.** Parallel sub-question research is a *Should*, not a *Must*, so a sequential implementation can still pass `deep_answer_p95_s` ≤ 90 s with four sub-questions. Tighten the p95 to force parallelism, or leave it as the natural pull toward the subagent stretch goal? *(Owner: Hamza)*
5. **Should the user be able to edit the plan before it runs?** Listed as a *Could*. It is obviously better product design and it is a second round-trip and a UI state the provided UI does not have. Cohort 2 material?
6. **Quality kit distribution.** Learners need `check.mjs` and `rules.json` in the assignment, but the cohort copy lives in a local-only folder and its precedents may name clients and costs. Promote a scrubbed copy into `quality/` before Week 1. *(Owner: Hamza)*
7. **TypeScript or JavaScript?** The scaffold is TypeScript because the contract types are the point. Learners who insist on plain JS can, but they lose the typecheck gate. Recommendation: TypeScript required for `packages/contract`, optional elsewhere.
8. **Gold corpus content.** Which 3–5 public PDFs? Suggest arXiv RAG papers so the Space demo overlaps Module 3.

## 18 · Stretch goals

- **Subagent split** (Week 2 material): run deep search's sub-questions as parallel isolated subagents rather than sequentially in one context; show the trace tree and the wall-clock drop.
- **Semantic answer cache with freshness guard** (Module 3's semantic cache): cached answers for non-time-sensitive repeats, with `answerCached: true`.
- **Learner-built UI** replacing `web/`, still passing the contract.
- **Own search:** SearXNG behind the same `web_search` tool.
- **Share links** for a thread; export a thread to Markdown.
- **Dockerize** both services with `docker compose up`; GitHub Action running `node benchmark/bench.mjs` and `fly deploy` on green.
- **Learner-built UI in Next.js** on Vercel, still passing the contract, with the gateway as its API route target.
- **Change streams** on `documents` to push indexing status to the UI over the existing SSE channel instead of polling.

## 19 · Submission

One **Vercel URL**, per [`SUBMISSION.md`](../../../SUBMISSION.md). The UI deploys to Vercel; the services run on Fly.io or Vercel against Atlas.

1. The `/fde-lumina-eval` skill runs the six gates (`check.mjs`, `bench.mjs`, `eval.mjs`) against the **deployed** gateway, collects the video link and the two trajectories read for P1, and writes `report.json`, served at `GET /evals/report.json`. The provided UI renders it at `/evals`.
2. The **60 to 90 s recording** embedded there shows: a quick question streams with citations; the same question run **deep**, with the plan appearing first and the merged citations at the end; a memory carrying into a new thread; a document question citing a page; and `/stats` showing the deep run's cost and the remaining daily allowance.
3. **No code is submitted.** `DESIGN.md` (the five questions, written before the build) and the "How I ran it" notes (LLM, search provider, Atlas tier) go into the eval config and render on `/evals` alongside both full trajectories.
