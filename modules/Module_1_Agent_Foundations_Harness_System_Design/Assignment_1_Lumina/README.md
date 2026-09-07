# Assignment 1: LUMINA

> Build a Perplexity-style AI search engine. Ask a question, get a streamed answer with
> citations you can click, built from a live web search and from your own documents. Ask a
> harder one and it plans sub-questions, researches each, and merges the citations.

You are given a **working React UI** and a **typed API contract**. You build the two backend
services they talk to. When your backend works, the UI lights up. That's the whole game.

---

## Start here

```bash
npm install
cp .env.example .env      # fill in MONGODB_URI and your provider keys
npm run dev               # UI on :5173, gateway on :8787, agent on :8000
```

Open <http://localhost:5173> and click everything. Every panel says
`501 not implemented yet`, which is correct: that message is your progress bar, and each
route you finish lights one up.

## Then read, in this order

| # | Read | Why |
|---|---|---|
| 1 | [`PRD.md`](PRD.md) | What the product is and the four rules that decide your grade. ~15 min. |
| 2 | `packages/contract/src/` | The contract, as zod schemas rather than prose — the literal answer to "what do I return?". Start with `sse.ts`, then `http.ts`. Best half hour you can spend. |
| 3 | [`DESIGN.template.md`](DESIGN.template.md) | Copy to `DESIGN.md` and answer the five questions **before you write code**. It is graded. |
| 4 | `benchmark/sla.json`, `expectations.json`, `eval/rubric.json` | The targets, the budgets, the points. Declared before you run, on purpose. |
| 5 | [`TECHNICAL.md`](TECHNICAL.md) | The build guide: architecture, commands, checklists, troubleshooting. |

Your coding agent should read [`AGENTS.md`](AGENTS.md) and [`SPEC.md`](SPEC.md) instead —
the first is the non-negotiables, the second is every requirement stated explicitly.

## What you build

| | |
|---|---|
| ✅ **Provided** | The UI, the API contract, `501` skeletons for both services, the Atlas index script, the benchmark, the gold set and corpus, the grader, and the eval skill. |
| 🔨 **Yours** | `backend/gateway/` — the edge: CORS, the `X-User-Id` check, request ids, logging, validation, rate limits, SSE pass-through. |
| 🔨 **Yours** | `backend/agent/` — the work: the agent loop, its tools, memory, RAG, deep search, the jobs worker, run logs. Provider keys live only here. |

Do not edit `web/`, `packages/contract/`, `benchmark/`, `eval/`, `quality/` or `scripts/`.
Those are the UI, the contract and the grader; editing them is a red line and it is checked.
Read them, then build a backend that satisfies them.

## The build, in one screen

Build the agent service first — you can drive it entirely with `curl -N`, no browser needed.
Then the gateway. Then load the UI and watch it light up.

1. `/health`, then the **quick loop** with `web_search` + `fetch_page`, streaming
   `trace → sources → token → done`. Sources before the first token.
2. The **search cache**: in-process LRU over a TTL'd Mongo collection.
3. **Threads and messages**, so a follow-up sees the conversation.
4. **Memory**: `save_memory` / `recall_memory`, listed and deletable at `/memory`.
5. The **run log** — one file per answer. Ten lines of adapter, and the gates read it.
6. **Spaces and the jobs worker**: upload → `202` → parse → chunk → embed → probe → indexed.
7. **Hybrid retrieval**: vector + text, fused, with page locators in the citations.
8. **Deep search**: plan sub-questions, research each, merge into one citation numbering.
9. The **gateway**, then the **deploy**.

Each step is a section in [`TECHNICAL.md`](TECHNICAL.md) with the commands and the gotchas.

## How you prove it

```bash
node benchmark/bench.mjs      # the SLA: latency, grounding, recall, cache, cost. Exits 0 or tells you why.
node quality/check.mjs .      # the rules, over your run logs
node eval/eval.mjs            # all six gates, in order, stopping at the first failure
```

Correct but slow, expensive, or ungrounded fails. The targets are in
`benchmark/sla.json`, declared before your first run — [`TECHNICAL.md`](TECHNICAL.md)
explains what each one measures and how the grounding check works.

## How you submit

**One URL**: your deployed app, with `/` working for a stranger and `/evals` rendering the
evaluation your run produced. No repo, no zip, no code.

In Claude Code, run `/fde-lumina-eval --deploy-url https://<your-gateway>`. It runs the
gates against the deployed app, walks you through your two trajectories, and writes the
`report.json` the provided UI renders at `/evals`.

Full flow, the deploy table, and the 60–90 second video checklist:
[`TECHNICAL.md`](TECHNICAL.md#submit) · course-wide rules:
[`SUBMISSION.md`](../../../SUBMISSION.md).

## Stuck?

[`TECHNICAL.md`](TECHNICAL.md#troubleshooting) covers the failures that cost people the most
time: tokens arriving all at once, a document that indexes but cannot be found, retrieval
that leaks across Spaces, uploads that stall the answer stream, and a "deep" search that is
only slower.
