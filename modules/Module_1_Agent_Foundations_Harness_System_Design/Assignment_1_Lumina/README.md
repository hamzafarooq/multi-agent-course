# Assignment 1: LUMINA

> Ship a Perplexity-style AI search engine: ask a question, get a streamed, cited answer built
> from live web search and your own documents. It remembers you across sessions. Any answer can
> become a slide deck or an image on demand. **MERN**: MongoDB Atlas, Express, React, Node.

You are given a **working React UI** and a **typed API contract**. Your job is to build the two
Express services the UI talks to. When your backend works, the UI lights up. That's the whole game.

This is the first assignment of the **FDE Agent Engineering Bootcamp**. It's deliberately shaped
like real forward-deployed work: you don't get to change the contract, the UI is the acceptance
test, and "it works on my machine" is not a grade. The full product thinking lives in
[`PRD.md`](PRD.md). This file is how you build and prove it.

> **Read this yourself.** This is a *reading* assignment first. The PRD's five system-design
> questions (components, responsibilities, communication, state, trade-offs) are the rubric every
> later project is graded against. Answer them in your `DESIGN.md` before you open an editor.

---

## Why this assignment

An FDE takes a capability and stands it up end to end where it's needed. LUMINA compresses that
into two weeks:

- **Own a real agent loop**, not a framework's. Plan, choose a tool, observe, repeat, stop.
- **Respect a contract** the frontend already speaks. You conform to it; you don't get to change it.
- **Separate concerns**: an Express gateway on the edge, an Express agent service holding the keys.
- **Make retrieval a decision**: web, your documents, or both, with a citation that resolves.
- **Make spend visible and gated**: every answer logs tokens and dollars; images sit behind a cap.
- **Prove it with numbers**: a benchmark that exits 0, a checker that reads your run logs, and a
  human who read a full trajectory.

---

## Architecture

Three moving parts. The **UI is done**. You build the **two Express services**. One MongoDB Atlas
cluster holds everything, vectors included.

```
   ┌──────────────────────────────┐
   │  Web UI  (web/)              │   ← PROVIDED · React 18 + Vite
   │  query · stream · citations  │      types from packages/contract
   └──────────────┬───────────────┘
                  │  HTTP + SSE   (X-User-Id, X-Request-Id)
                  ▼
   ┌──────────────────────────────┐
   │  Express gateway   :8787     │   ← YOU (software backend)
   │  CORS · zod-validate · log   │      rate-limit · serve web/dist · SSE pass-through
   └──────────────┬───────────────┘
                  │  same contract
                  ▼
   ┌──────────────────────────────┐
   │  Express agent service :8000 │   ← YOU (AI backend): the real work
   │  loop · tools · memory · RAG │      jobs worker · artifacts · run logs
   └───┬──────┬──────────┬────────┘
       ▼      ▼          ▼
    Search   LLM +    MongoDB Atlas: threads · messages · memories (vector idx)
   (Tavily/  embed    chunks (vector + text idx) · searchCache (TTL) · jobs
   SerpApi) (env)     artifacts · requests · runs · GridFS files
```

**Why two services?** Browser-facing concerns (CORS, validation, rate limiting, request logs,
serving the UI) are different from AI concerns (prompts, tools, keys, cost). Splitting them is the
FDE habit: each deploys and fails on its own, and your API keys never live on the edge the browser
can reach.

**Why one database?** Atlas Vector Search puts the embedding in the same document as the chunk text
and its page locator, so a citation is one document and `spaceId` is a plain filter. No second
store to keep in sync.

---

## What's provided vs. what you build

| Component | Status | Path |
|-----------|--------|------|
| React UI (query, streaming, citation chips, memory panel, Spaces, deck/image actions) | ✅ Provided | `web/` |
| API contract as zod schemas + TypeScript types | ✅ Provided | `packages/contract/` |
| Express skeletons returning `501` everywhere but `/health` | ✅ Provided | `backend/gateway/`, `backend/agent/` |
| Atlas index script (vector, text, TTL indexes from one JSON) | ✅ Provided | `scripts/create-indexes.mjs` |
| Benchmark + SLA | ✅ Provided | `benchmark/bench.mjs`, `benchmark/sla.json` |
| RAG gold set + small CC-licensed corpus | ✅ Provided | `eval/gold/` |
| Rubric + eval + quality checker | ✅ Provided | `eval/`, `quality/` |
| **Express gateway** | 🔨 **You** | `backend/gateway/` |
| **Express agent service** (loop, tools, memory, RAG, jobs worker, artifacts, run logs) | 🔨 **You** | `backend/agent/` |

You should not need to edit `web/`, `packages/contract/`, `benchmark/`, or `eval/`. Read them to
understand the contract, then build a backend that satisfies it.

---

## The API contract (do not change it)

The full contract, with every SSE event and status code, is in [`PRD.md` §7](PRD.md#7--api-contract-fixed-the-ui-speaks-this) and enforced by `packages/contract/`. The rules that matter:

- `POST /threads/{id}/ask` streams `trace → sources → token → done`. **`sources` arrives before the first `token`.**
- Every `[n]` in the answer has exactly one matching `n` in `sources`. Extra or missing is a grounding failure.
- `done` carries `latencyMs`, `ttftMs`, `tokens`, `costUsd`, `searchCached`, and `terminated: "done" | "cap" | "error"`, all measured server-side.
- `POST /spaces/{id}/documents` and `POST /artifacts` return `202` in < 300 ms. The work happens on the `jobs` worker.
- `X-User-Id` is required on every route except `/health` (`401` without it). `429` for rate limit or image cap. `502` for any upstream failure.
- `GET /health` names the LLM, search provider, and vector backend. `GET /stats` reconciles with your logs.

---

## Build it: recommended order

Build the agent service first (test it with `curl -N`, no browser needed), then the gateway, then load the UI.

### Part 0: scaffold
```bash
npm install                       # workspace: web, backend/*, packages/contract, benchmark, eval, quality
cp .env.example .env              # MONGODB_URI, LLM key, SEARCH_PROVIDER + key, OPENAI_API_KEY (embeddings, images)
node scripts/create-indexes.mjs   # vector + text + TTL indexes on your Atlas cluster
npm run dev                       # gateway :8787, agent :8000, UI with hot reload
```

### Part 1: the agent service (the real work), `backend/agent/`
1. `/health`, then the loop with `web_search` + `fetch_page` and the SSE stream. Disable compression, flush after every event.
2. Search cache: in-process LRU over the `searchCache` collection (TTL index). `searchCached` in `done`.
3. `threads` + `messages`; follow-ups see the thread.
4. Memory: `save_memory` / `recall_memory` over the `memories` vector index; `GET /memory`, `DELETE /memory/{id}`.
5. Run log: one `runs/<requestId>.json` per answer (shape in `PRD.md` §13). Ten lines. The gates read it.
6. Spaces + the `jobs` worker: upload → GridFS → parse (`pdfjs-dist`) → chunk → embed → upsert → **read-your-write probe** → `indexed`.
7. Hybrid retrieval: `$vectorSearch` + `$search` fused with RRF. Page locators in citations.
8. Artifacts: deck (`pptxgenjs`, outline JSON stored on the artifact) and image (`gpt-image-1`, daily cap, `DRY_RUN`).

Test it in isolation:
```bash
curl -s -X POST localhost:8000/threads -H 'x-user-id: dev' | tee /tmp/t.json
curl -N -X POST localhost:8000/threads/$(jq -r .threadId /tmp/t.json)/ask -H 'x-user-id: dev' \
  -H 'content-type: application/json' -d '{"query":"What is Tavily?","mode":"web"}'   # watch trace → sources → token → done
```

### Part 2: the gateway (software backend), `backend/gateway/`
CORS · `X-User-Id` check · `X-Request-Id` (reuse inbound or generate) · `pino` request log · zod validation from `packages/contract` · per-user rate limit · SSE pass-through · serve `web/dist`.

### Part 3: see it live
`npm run dev`, open the UI, ask a question, click a citation. Save a preference, open a new thread, watch it apply. Upload a PDF to a Space, ask about it, see `filename, p. N`. Make a deck. Generate an image with `DRY_RUN=true` first.

### Part 4: ship it on Fly.io
```bash
cd backend/agent   && fly launch --no-deploy && fly secrets set MONGODB_URI=... ANTHROPIC_API_KEY=... TAVILY_API_KEY=... OPENAI_API_KEY=... && fly deploy
cd ../gateway      && fly launch --no-deploy && fly secrets set AGENT_URL=https://<your-agent>.fly.dev && fly deploy
```
Atlas stays where it is. Keep the agent service private (Fly private networking) so only the gateway reaches it. Your eval must pass against the **deployed** gateway.

---

## Performance, SLA & cost

Correct but slow or expensive fails in production. Every target lives in
[`benchmark/sla.json`](benchmark/sla.json), declared **before** you run, and `bench.mjs` exits
non-zero on any miss.

| Metric | Target | Why |
|--------|--------|-----|
| Time to first token, p95 | ≤ 2 500 ms | the "it's thinking" window a user tolerates |
| Full answer, p95 | ≤ 12 000 ms | plan + 2 searches + 4 fetches + synthesis |
| `202` accept latency, p95 | ≤ 300 ms | proves work is off the request path |
| Search p95 during a large ingest | ≤ 1.3 × idle | ingestion never starves answers |
| Citation grounding | ≥ 95 % | arithmetic on snippets, no judge |
| RAG recall@5 on the gold set | ≥ 0.70 | 30 questions, provided corpus |
| Search cache hit rate (bench workload) | ≥ 50 % | repeats are free |
| Deck p95 / image p95 | ≤ 60 s / ≤ 45 s | |
| Error rate | ≤ 1 % | |
| Cost per answer (mean) | ≤ $0.05 | prices in `sla.json` are placeholders; set yours |

```bash
node benchmark/bench.mjs                 # end to end through the gateway
node benchmark/bench.mjs --smoke         # five queries, Gate 2
node benchmark/bench.mjs --json out.json # machine-readable
```

---

## Requirements checklist

- [ ] **Loop**: bounded (8 tool calls, 90 s); `terminated` honest; every step a `trace` event; tool failures visible with an error string.
- [ ] **Search**: provider swappable via `SEARCH_PROVIDER`; pages fetched and read, not snippets; two-tier cache with TTL; `searchCached` accurate.
- [ ] **Citations**: every `[n]` resolves to a source retrieved in that request; empty retrieval says so.
- [ ] **Memory**: thread history persists; long-term memory saved explicitly, recalled semantically, listed and deletable at `/memory`; a preference provably crosses threads.
- [ ] **RAG**: `202` upload; async indexing on the `jobs` worker; page locators; one vector index filtered by `spaceId`; read-your-write probe before `indexed`; recall@5 ≥ 0.70.
- [ ] **Deck**: `.pptx` via `pptxgenjs`; outline JSON stored; every slide citation exists in the answer's sources; opens cleanly.
- [ ] **Image**: `gpt-image-1`; `costUsd` and `promptUsed` stored; `IMAGE_DAILY_CAP` → `429`; `DRY_RUN` works.
- [ ] **Observability**: `pino` JSON lines in both services; one `X-Request-Id` correlates a request end to end; `/stats` reconciles with the log.
- [ ] **Run logs**: `runs/<requestId>.json` per answer; `node quality/check.mjs .` exits ≤ 1.
- [ ] **Performance**: `node benchmark/bench.mjs` exits 0.
- [ ] **Deploy**: both services on Fly.io against Atlas; the UI works against the public gateway.
- [ ] **Product evaluation**: `PRODUCT_EVAL.md` from `/fde-lumina-eval`, naming the two trajectories you read.

---

## Definition of Done: non-negotiables

> Written for your coding agent as much as for you. The same list lives in [`AGENTS.md`](AGENTS.md).
> Self-verify every box with the commands below before claiming done. Inspection is not verification.

**Contract**: shapes and status codes match `packages/contract` exactly; the provided UI works unmodified; `sources` precedes `token`.

**Loop**: caps exist and are reported (`terminated: "cap"`); provider exceptions → `502` and `terminated: "error"`; **never** a plausible answer on an exception; the ask path never calls `make_presentation` or `generate_image`.

**Grounding**: a citation that does not resolve to something retrieved in that request is an automatic fail.

**Memory**: nothing is remembered that `GET /memory` does not show.

**Async**: `202` in < 300 ms; status flips only after the work succeeds; `indexed` only after the probe.

**Spend**: image cap enforced server-side; cost logged per answer and per artifact; `DRY_RUN` exists.

**Hygiene**: `.env`, `node_modules/`, `web/dist/`, `runs/`, `reports/` git-ignored; the Atlas URI is a secret.

**Self-verify (all must pass)**
```bash
curl -sf localhost:8000/health && curl -sf localhost:8787/health                  # 1. both up, health nests the agent
T=$(curl -s -X POST localhost:8787/threads -H 'x-user-id: dev' | jq -r .threadId)
curl -N -X POST localhost:8787/threads/$T/ask -H 'x-user-id: dev' -H 'content-type: application/json' \
  -d '{"query":"latest on EU AI Act GPAI obligations","mode":"web"}' | grep -m1 '^event: sources'   # 2. sources before tokens
curl -s -o /dev/null -w '%{http_code}\n' -X POST localhost:8787/threads/$T/ask -d '{}'          # 3. 401 without X-User-Id
ls runs/*.json | head -1 && node quality/check.mjs .                                            # 4. run log exists, gates read it
node benchmark/bench.mjs                                                                       # 5. exit 0
git status --porcelain | grep -E '\.env$|node_modules|^runs/|^reports/' && echo "FAIL: unstage" || echo clean   # 6.
curl -sf https://<your-gateway>.fly.dev/health                                                 # 7. deployed for real
```

---

## Grading (100 pts)

| Area | Pts | What we look for | Rules |
|------|-----|------------------|-------|
| UI lights up & contract | 10 | Fresh clone → README → UI streams a cited answer through the gateway; shapes and status codes match | C1 |
| Search & cited answers | 20 | Grounding ≥ 95 %; `sources` before tokens; pages fetched; `searchCached` true on repeat | E2 |
| Memory | 10 | Preference in thread A changes thread B; listed; deletable, and the effect disappears | |
| RAG over documents | 15 | `202` → `indexed` via the worker; page locator; router picks docs; recall@5 ≥ 0.70 | E1, E2 |
| Presentation | 10 | `.pptx` downloads; slide citations exist in sources (auto); opens, reads like a real deck (manual) | E3 |
| Image generation | 10 | `gpt-image-1` artifact with `costUsd`, `promptUsed`; cap → `429`; `DRY_RUN` works | R2, B3 |
| Performance & SLA | 10 | `node benchmark/bench.mjs` exits 0 | B1–B3, A2, A3 |
| Observability | 5 | One request id across both logs; `/stats` reconciles; trace explains citations | A1 |
| Human gate & answer quality | 5 | You name one successful and one failing trajectory you read end to end; grader samples five answers | P1 |
| Deploy & docs | 5 | Fly.io + Atlas; UI on the public gateway; `npm run dev` works; `.env.example`; run notes | |

**Red lines (auto-flagged):** secrets committed · provided `web/`, `packages/contract/`, `benchmark/`, `eval/` edited · any fabricated citation in the bench sample (E2) · a `2xx` answer on a provider exception (A1) · a capped run reported as `done` (A2) · an artifact tool called from the ask path (R2).

**Bonus (+5):** you hit a failure the rules don't cover and submit it as a new rule with its real precedent.

### Sample scorecard

Illustrative only. Your numbers come from your own run; fabricating them is an automatic fail.

> **Assignment 1: LUMINA · Priya Nair · 91 / 100**

| Criterion | Pts | Awarded | Status | Evidence |
|-----------|-----|---------|--------|----------|
| UI lights up & contract | 10 | 10 | ✅ Pass | All routes match; `sources` event lands 1.6 s before first token |
| Search & cited answers | 20 | 19 | ✅ Pass | Grounding 97.3 % over 60 answers; 1 snippet-only synthesis flagged in trace |
| Memory | 10 | 10 | ✅ Pass | "prefer TypeScript" saved in thr_1, applied in thr_2; deleted → plain prose again |
| RAG over documents | 15 | 15 | ✅ Pass | 3 PDFs indexed via worker; `p. 14` citation; recall@5 0.77 |
| Presentation | 10 | 8 | ⚠️ Partial | 8-slide deck, all citations resolve; two slides read like bullet dumps |
| Image generation | 10 | 10 | ✅ Pass | `gpt-image-1` 1024², $0.04 logged; 11th image → `429` with `resetsAt` |
| Performance & SLA | 10 | 10 | ✅ Pass | TTFT p95 1.9 s; full p95 8.4 s; cache hit 58 %; $0.031/answer |
| Observability | 5 | 5 | ✅ Pass | `req_7f3a` greppable in both logs; `/stats.answers` = log count |
| Human gate & answer quality | 5 | 4 | ⚠️ Partial | Two trajectories named and annotated; one sampled answer padded |
| Deploy & docs | 5 | 0 | ❌ Fail | Deployed, but the agent service was publicly reachable and `.env.example` missing `IMAGE_DAILY_CAP` |
| **Total** | **100** | **91** | | Auto: 79/80 · Manual: 12/20 |

**Red-line checks:** ✅ no secrets · ✅ provided folders untouched · ✅ no fabricated citation · ✅ no `2xx` on exception

---

## Stretch goals (bonus)

- **Subagent split**: planner → parallel researchers → writer, with isolated contexts and a trace tree (Week 2 material).
- **Pro search**: query decomposition with per-sub-question retrieval and merged citations.
- **Semantic answer cache** with a freshness guard, `answerCached: true` (Module 3).
- **Change streams** on `artifacts` pushed over the existing SSE channel instead of polling.
- **Your own UI** (Next.js on Vercel) replacing `web/`, still passing the contract.
- **Docker Compose** for both services; a GitHub Action running the bench and `fly deploy` on green.

---

## Submit

1. **Generate the evaluation with the skill.** In Claude Code run **`/fde-lumina-eval`**. It runs the six gates (`quality/check.mjs`, `benchmark/bench.mjs`, `eval/eval.mjs`) against your **deployed** gateway and writes `PRODUCT_EVAL.md`, attaching `reports/quality.json` and `reports/eval.json` and the two trajectories you read.
2. **Submit `PRODUCT_EVAL.md` (or PDF)** and a **60–90 s recording**: a fresh question streams with citations; a memory carries into a new thread; a document question cites a page; the deck downloads and opens; an image generates and `/stats` shows its cost.
3. Push your repo with both `backend/` services implemented and a short **"How I ran it"** noting your LLM, search provider, and Atlas tier. Do **not** commit `.env`, `node_modules/`, `runs/`, or `reports/`.

---

## Troubleshooting

- **Tokens arrive all at once at the end** → something is buffering. Disable `compression` on the ask route, call `res.flushHeaders()`, and flush after each `res.write`. Set `X-Accel-Buffering: no`.
- **`indexed` but the question finds nothing** → Atlas Search indexes are eventually consistent. Your read-your-write probe is missing or too early.
- **`$vectorSearch` returns results from another Space** → the filter must be inside `$vectorSearch`, not a later `$match`, and `spaceId` must be declared as a filter field in the index definition.
- **Uploads stall the answer stream** → your worker is running on the main thread. Move it to `worker_threads` or `npm run worker`.
- **`429` on your first image** → `IMAGE_DAILY_CAP` is per `X-User-Id`; the bench uses its own id. Check `/stats.imagesToday`.
- **UI shows "not implemented yet"** → expected until you finish that route. That message *is* your progress bar.
