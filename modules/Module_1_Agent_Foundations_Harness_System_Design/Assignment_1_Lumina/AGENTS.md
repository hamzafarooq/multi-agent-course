# AGENTS.md: non-negotiables for this assignment

You are helping a student complete **Assignment 1: LUMINA** (MERN). Read `README.md` for the
build guide and `PRD.md` for the product. This file is the contract you must satisfy. Do not
relax, reinterpret, or "improve" these requirements. Conform to them.

## What you may and may not touch

- **BUILD:** `backend/gateway/` (Express: CORS, `X-User-Id`, request id, `pino` log, zod validation,
  rate limit, SSE pass-through, serve `web/dist`) and `backend/agent/` (Express: the loop, tools,
  memory, RAG, deep search, the `jobs` worker, run logs).
- **DO NOT EDIT:** `web/`, `packages/contract/`, `benchmark/`, `eval/`, `quality/`, `scripts/`.
  These are the provided UI, the contract, and the grader. If something seems to require editing
  them, you've misread the contract. Editing them is a red line and it is checked.
- **Keep a deliberately failed run in `runs/failing/`, not `runs/`.** Rule A2 grades every run in
  `runs/` and fails one that did not terminate as `done`; rule P1 requires you to keep a failing
  trajectory. The subfolder is how both hold at once — the trajectory rules read `runs/*.json`
  only, and `eval/build-report.mjs` reads both.
- **Write `DESIGN.md` before any code.** It answers the five questions: components,
  responsibilities, communication, state, trade-offs. It is graded as the design section of the
  `/evals` page, so it must survive being read by a stranger.

## Hard requirements (all must hold)

### Contract: match exactly
- Every route, body, SSE event, and status code matches `packages/contract/`. `401` without
  `X-User-Id`; `404` unknown ids; `413` file too large; `429` rate limit or deep-search cap;
  `501` not implemented; `502` any upstream failure.
- `POST /threads/{id}/ask` streams `trace → sources → token → done`, and on a deep search
  `plan` first. `sources` is emitted **before** the first `token`; `plan` is emitted **before any
  retrieval**. Every `[n]` in the text has exactly one matching `n` in `sources`.
- `done` carries `answerId, latencyMs, ttftMs, model, tokens{in,out}, costUsd, searchCached,
  terminated, depth, subQuestions`, all measured server-side.
- `depth` defaults to `"quick"`. The server NEVER upgrades a request to deep on its own.
- The browser talks ONLY to the gateway (`:8787`). The gateway talks to the agent service (`:8000`).
  Provider keys exist only in the agent service.

### The loop
- Tools: `web_search`, `fetch_page`, `search_documents`, `recall_memory`, `save_memory`, and
  — **deep searches only** — `plan_research`. A quick run whose trace contains `plan_research`
  has escalated itself into a run costing several times more: that is a red line, and
  `bench.mjs` checks every quick run for it.
- Hard caps, per gear: **quick** 8 tool calls / 90 s, **deep** 24 tool calls / 240 s. Hitting one
  ends the run with `terminated: "cap"` and an honest partial answer. A provider exception ends it
  with `terminated: "error"` and a `502`.
- **Fail loud.** NEVER wrap a provider call in a `try/catch` that returns a plausible answer, an
  empty-but-successful answer, or "I couldn't find anything" when the real cause was an exception.
  (Precedent: Live Translate, where a dependency mismatch made every call throw, the `except`
  returned the input untouched, and the "translator" served English for weeks.)
- Every step is a `trace` event and is logged. A failed tool call has `ok: false` and a non-empty
  `error` string.
- Every answer writes `runs/<requestId>.json`: `tokens`, `wallClockSec`, `costUsd`, `terminated`,
  `depth`, ordered `toolCalls[{name, ok, error}]`. `node quality/check.mjs .` must be able to read
  it. Without `depth`, nobody can tell an expensive deep run from a quick run that ran away.

### Grounding (this is the point of the assignment)
- A citation that does not resolve to something retrieved **in that request** is an automatic fail.
- Synthesize from fetched page text or indexed chunks, not from search snippets. If you fall back
  to snippets, say so in the trace.
- Empty retrieval → say so and cite nothing. Never invent a URL, a page number, or a document.

### Search
- `SEARCH_PROVIDER=tavily | serpapi`, swappable via env with no code change.
- Two-tier cache: in-process LRU + `searchCache` collection with a TTL index, key = SHA-256 of
  `(normalized query, provider)`. `searchCached: true` only when every search in the request hit.

### Memory
- Thread history persists in `threads` + `messages`.
- Long-term memory is written only by an explicit `save_memory` call, for stable facts and
  preferences. `GET /memory` lists every memory; `DELETE /memory/{id}` removes one, and the effect
  disappears. Nothing is remembered that `/memory` does not show.
- Recall is semantic: Atlas Vector Search on `memories.embedding`, filtered by `userId`.

### RAG (MongoDB Atlas)
- `POST /spaces/{id}/documents` stores the file in GridFS, inserts a `pending` document and a
  `jobs` row, and returns `202` in < 300 ms. Parsing, chunking, embedding, and indexing happen on
  the worker. A synchronous parse-then-respond endpoint fails the assignment even if it works.
- One `chunks` collection, one vector index, `spaceId` as a filter field **inside** `$vectorSearch`.
- Every chunk carries a locator: `{page}` for PDF, `{heading}` or `{line}` for text.
- A document becomes `indexed` only after a **read-your-write probe** returns one of its chunks
  from the vector index. "Upserted" is not "searchable".
- Crash-safe: a worker killed mid-job leaves the row `running` with a stale `claimedAt`; a sweeper
  returns it to `pending`; finished stages are not re-run.

### Deep search (this is where 15 of the 100 points are)
- `depth: "deep"` runs `plan_research` first and streams a `plan` event with 3–6 sub-questions,
  each with a one-line reason, **before any retrieval happens**. A plan emitted after the fetches
  is a rationalisation and scores as one.
- Every `trace` step and every `source` on a deep run carries the `subQuestion` index it served.
  A merged source list nobody can trace back to a sub-question is a pile, not research.
- Merge into ONE citation numbering: dedupe by `url` (or `docId` + locator), number contiguously
  from 1, and every `[n]` in the answer resolves to exactly one entry.
- Deep must actually be deeper. The bench runs the **same question** at both depths and requires
  deep to surface at least `min_deep_source_ratio` (2×) the distinct sources. Longer prose over
  the same two pages fails.
- **Spend gate:** `DEEP_DAILY_CAP` (default 5) per `X-User-Id`, enforced in the agent service
  → `429 {error, resetsAt}`. Not in the gateway: a cap on the edge is a cap you bypass by
  reaching the agent service directly.
- Structure the answer (a direct answer, a section per sub-question, then what is still unknown).
  One long paragraph wastes the decomposition.

### Observability
- `pino` JSON lines: one per request at the gateway (`method, route, status, ms, requestId, userId`),
  one per answer at the agent (`requestId, toolCalls, terminated, tokens, costUsd, searchCached,
  ttftMs, latencyMs`).
- `X-Request-Id`: reuse inbound, else generate at the gateway; forward; log in both. One request is
  greppable end to end.
- `/health` names LLM model, search provider, vector backend, and Mongo status. `/stats` reconciles
  with the logs and reports `deepToday` / `deepDailyCap`.

### Hygiene
- Secrets from `.env` only, read server-side. No key, connection string, or token is ever bundled
  into client JavaScript or returned by an endpoint. `.env`, `node_modules/`, `web/dist/`, `runs/`,
  `reports/` are git-ignored even though the repo is not submitted.

### Evidence
- **The submission is the Vercel URL, not the code.** `GET /evals/report.json` on the gateway serves
  the eval skill's output and the provided UI renders it at `/evals`. Never hand-edit that file, and
  never write a number into it that a run did not produce.
- Numbers on `/evals` come from a real `node benchmark/bench.mjs` run and a real
  `node quality/check.mjs .` run against the **deployed** gateway. Name the one successful and one
  failing trajectory you read end to end. If you cannot produce a failing one, kill the search key
  and run again.
