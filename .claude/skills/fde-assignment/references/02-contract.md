# Stage 2: the contract

The contract is the thing that is graded. Write it as jsonc in the SPEC (§7 and §8) exactly
the way LUMINA does, and later as executable schemas in `packages/contract/` (stage 6). The
UI compiles against it, the gateway validates inbound with it, the agent validates outbound
with it, and the bench speaks it over HTTP.

## Conventions every FDE contract shares

- **Identity is a dev header.** `X-User-Id` required on every route except `/health`;
  `401` without it. No accounts, no OAuth.
- **Request id.** `X-Request-Id`: reuse inbound, else generate at the gateway, forward, log
  in both services. One request is greppable end to end.
- **Status codes, fixed set:** `400` invalid input · `401` missing identity · `404` unknown
  id · `413` too large · `429` rate limit **or** spend cap · `501` not implemented (the
  skeleton's default, and the student's progress bar) · `502` any upstream failure.
- **Ids are prefixed strings** generated in the app (`thr_`, `ans_`, `doc_`, `req_`), so they
  read in logs and URLs.
- **Streaming is SSE** over `POST`, with a fixed event order that the UI depends on. State the
  order and the rule for each seam: LUMINA's `sources` before the first `token`, `plan` before
  any retrieval. Every ordering rule is a bench check later.
- **Work off the request path returns `202`** fast (`{id, status: "pending"}`), and a status
  route shows the state machine `pending -> ... -> indexed | failed` with `pct`.
- **`done` (or the terminal event) carries the measurements:** `latencyMs`, `ttftMs`,
  `model`, `tokens{in,out}`, `costUsd`, `terminated: "done" | "cap" | "error"`, plus the
  assignment's mode fields (LUMINA: `depth`, `subQuestions`). All measured server-side.
- **`/health` names what is live** as free strings: model, providers, store. Never a closed
  enum, which is a stack lock hiding in a schema. Nested `ai: {status}` so the gateway's
  health includes the agent's.
- **`/stats` reconciles with the logs** and reports today's spend and any per-user cap
  (`deepToday` / `deepDailyCap` shape).
- **`GET /evals/report.json`** serves the eval skill's output; the provided UI renders `/evals`.
  Shape is course-wide, in `SUBMISSION.md`.

## Writing §7 (routes)

```jsonc
POST /things                       -> 201 { "thingId": "thg_..." }
GET  /things/{id}                  -> 200 { ... }
POST /things/{id}/act              // body: { ... , "mode": "a" | "b" }   // default "a"
  -> 200 text/event-stream
  event: trace    data: { "step": 1, "tool": "...", "input": {...}, "ok": true, "ms": 812, "reason": "..." }
  event: ...      // the assignment's ordered events
  event: done     data: { ... }
  event: error    data: { "status": 502, "error": "..." }
GET  /health                       -> 200 { "status": "ok", ...free strings..., "db": "ok", "ai": { "status": "ok" } }
GET  /evals/report.json            -> 200 { ... }
GET  /stats                        -> 200 { ... }
```

Follow with **"Contract rules that matter"**: five to eight bullets, each one an ordering or
invariant the bench will assert (every `[n]` resolves; `202` in under the declared ms;
defaults and "the server never upgrades a request on its own").

## Writing §8 (data model)

One table: collection, key fields, indexes. Mark vector / text / TTL indexes in bold. Every
document carries `userId` and `createdAt`. Include the operational collections, not just the
domain ones: `requests`, `runs` (the run-log shape), `jobs` (`status, claimedAt, workerId,
attempts, error` for the crash-safe claim pattern), a TTL'd cache.

Then the paragraph **"Schema lives in code"**: the contract package exports schemas and
types for every request, response, event and document; the ODM is an implementation detail.

## Design questions to settle here, not in prose later

- Which concern sits at the edge (gateway) and which next to the keys (agent)? Spend caps go
  next to the spending: "a cap on the edge is a cap you bypass by reaching the agent directly".
- Which paths are async (`202` + worker) and which stream? LUMINA: ingestion is a job; deep
  search streams because "someone waiting on a minute of research wants to watch it work".
- What per-mode fields must the terminal event and the run log carry so a grader can tell an
  expensive legitimate run from a cheap run that ran away?
- Which ordering rules encode the lesson? Those become the bench's sharpest checks.

## Checklist

- [ ] Every route has a status code and a body shape; the fixed status-code set is stated once.
- [ ] Event order is written down, with the rule at each seam.
- [ ] `done` carries every number the SLA will measure.
- [ ] `/health` fields are strings, not enums.
- [ ] `runs/<requestId>.json` shape is fixed and matches what `quality/check.mjs` reads:
      `tokens, wallClockSec, costUsd, terminated, toolCalls[{name, ok, error}]` plus mode fields.
- [ ] Every collection has `userId`, `createdAt`, and its indexes named.
