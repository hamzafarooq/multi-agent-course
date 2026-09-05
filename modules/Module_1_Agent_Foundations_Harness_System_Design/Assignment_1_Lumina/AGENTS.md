# AGENTS.md: non-negotiables for this assignment

You are helping a student complete **Assignment 1: LUMINA** (MERN). Read `README.md` for the
build guide and `PRD.md` for the product. This file is the contract you must satisfy. Do not
relax, reinterpret, or "improve" these requirements. Conform to them.

## What you may and may not touch

- **BUILD:** `backend/gateway/` (Express: CORS, `X-User-Id`, request id, `pino` log, zod validation,
  rate limit, SSE pass-through, serve `web/dist`) and `backend/agent/` (Express: the loop, tools,
  memory, RAG, `jobs` worker, artifacts, run logs).
- **DO NOT EDIT:** `web/`, `packages/contract/`, `benchmark/`, `eval/`, `quality/`, `scripts/`.
  These are the provided UI, the contract, and the grader. If something seems to require editing
  them, you've misread the contract.
- **First commit is `DESIGN.md`, no code.** It answers the five questions: components,
  responsibilities, communication, state, trade-offs.

## Hard requirements (all must hold)

### Contract: match exactly
- Every route, body, SSE event, and status code matches `packages/contract/`. `401` without
  `X-User-Id`; `404` unknown ids; `413` file too large; `429` rate limit or image cap; `501` not
  implemented; `502` any upstream failure.
- `POST /threads/{id}/ask` streams `trace → sources → token → done`. `sources` is emitted
  **before** the first `token`. Every `[n]` in the text has exactly one matching `n` in `sources`.
- `done` carries `answerId, latencyMs, ttftMs, model, tokens{in,out}, costUsd, searchCached,
  terminated`, all measured server-side.
- The browser talks ONLY to the gateway (`:8787`). The gateway talks to the agent service (`:8000`).
  Provider keys exist only in the agent service.

### The loop
- Tools available to the ask loop: `web_search`, `fetch_page`, `search_documents`,
  `recall_memory`, `save_memory`. **Never** `make_presentation` or `generate_image` from the ask
  path. Those run only via `POST /artifacts`.
- Hard caps: 8 tool calls, 90 s. Hitting one ends the run with `terminated: "cap"` and an honest
  partial answer. A provider exception ends it with `terminated: "error"` and a `502`.
- **Fail loud.** NEVER wrap a provider call in a `try/catch` that returns a plausible answer, an
  empty-but-successful answer, or "I couldn't find anything" when the real cause was an exception.
  (Precedent: Live Translate, where a dependency mismatch made every call throw, the `except`
  returned the input untouched, and the "translator" served English for weeks.)
- Every step is a `trace` event and is logged. A failed tool call has `ok: false` and a non-empty
  `error` string.
- Every answer writes `runs/<requestId>.json`: `tokens`, `wallClockSec`, `costUsd`, `terminated`,
  ordered `toolCalls[{name, ok, error}]`. `node quality/check.mjs .` must be able to read it.

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

### Artifacts
- `POST /artifacts` → `202` → `GET /artifacts/{id}` polls `pending | ready | failed`. `failed`
  carries the provider's error; a half-written file is never marked `ready`.
- Deck: outline JSON (title, 6–10 slides, bullets, citation numbers) stored on the artifact and
  rendered with `pptxgenjs`. Every citation number on every slide exists in the answer's `sources`.
- Image: `gpt-image-1`. Store `model`, `size`, `costUsd`, `promptUsed`. `IMAGE_DAILY_CAP` (default
  10) enforced per `X-User-Id` in the agent service → `429 {error, resetsAt}`. `DRY_RUN=true`
  returns a placeholder with `costUsd: 0`.

### Observability
- `pino` JSON lines: one per request at the gateway (`method, route, status, ms, requestId, userId`),
  one per answer at the agent (`requestId, toolCalls, terminated, tokens, costUsd, searchCached,
  ttftMs, latencyMs`).
- `X-Request-Id`: reuse inbound, else generate at the gateway; forward; log in both. One request is
  greppable end to end.
- `/health` names LLM model, search provider, vector backend, and Mongo status. `/stats` reconciles
  with the logs.

### Hygiene
- Secrets from `.env` only. `.env`, `node_modules/`, `web/dist/`, `runs/`, `reports/` are
  git-ignored. The Atlas connection string is a secret.

### Evidence
- Numbers in `PRODUCT_EVAL.md` come from a real `node benchmark/bench.mjs` run and a real
  `node quality/check.mjs .` run against the **deployed** gateway. Name the one successful and one
  failing trajectory you read end to end. If you cannot produce a failing one, kill the search key
  and run again.
