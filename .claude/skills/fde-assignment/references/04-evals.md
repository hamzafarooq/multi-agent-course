# Stage 4: evals and quality assurance, or how "done" is proven

A thing that ran is not a thing that worked. A streamed answer with a green `done` proves the
process did not crash; grounding, recall, budget and termination are what prove it worked.
This stage decides how every number from stage 3 is measured, by what, against what, and in
what order. It is the part students most often leave to "we will test it", and the part
LUMINA got most wrong until the grader was actually run.

## The four laws (SPEC §13, verbatim in every assignment)

1. **A thing that ran is not a thing that worked.**
2. **Assert from declared numbers, never from detection.** Every gating threshold is
   arithmetic against a run log or an eval report. An LLM judge may *report* at `warn`; it
   may never block (rule E3). Precedent: three colour-threshold face detectors all returned
   confident wrong answers; the fix was to stop detecting and assert against declared numbers.
3. **Every rule cites the failure that created it.** Rule ids come from `quality/rules.json`.
4. **Gates run in order, and each one blocks.**

## Decide what measures each number

For every row in `sla.json` and every automated rubric row, name the instrument:

| Kind | Instrument | Example from LUMINA |
|---|---|---|
| Latency, cost, error rate | the bench, timed client-side through the gateway, per mode | `ttft_p95_ms` per gear, never blended |
| Grounding | arithmetic: re-fetch the page or chunk, normalize, require ~12 consecutive matching tokens; a page the bench cannot fetch is *unverifiable* and excluded, a dangling `[n]` is a fabrication and fatal | `min_citation_grounding` |
| Retrieval quality | a **gold set** of at least 30 items over a **provided corpus** with stable anchors (rule E1: under 30 it is an anecdote) | 39 questions, 4 CC-BY documents, 2 rendered to PDF so page numbers are stable, plus a validator |
| The lesson | one check that runs the *same input* through both modes and compares | `min_deep_source_ratio`: same question, quick and deep, deep must surface 2x the distinct sources |
| Ordering rules from the contract | the bench reads the event stream and asserts order | `sources` before first `token`; `plan` before any retrieval |
| Budgets and trajectory hygiene | `quality/check.mjs` over `runs/*.json` | A1 errors surface, A2 terminated done, A3 no thrash, B1-B3 budgets |
| Conditional rules the kit cannot express | the bench, where per-run context exists | no quick run calls `plan_research` (R2, asserted per run by depth) |
| Things only a person can judge | a manual rubric row, few, named as such | "is the deep answer better or merely longer", the P1 trajectory read, deploy |

If a Must requirement has no instrument in this table, it is not a Must. Demote it or find
the arithmetic.

## The gold set

Build it before the bench, because the bench cannot measure recall without it. Rules: a
provided corpus students cannot see the answers to in advance, anchors that do not move
(render Markdown to PDF so `page` is stable), a builder script and a validator that re-checks
every anchor, a permissive licence recorded in the folder. Declare `goldSetPath` in
`expectations.json` so E1 checks it exists and is non-trivial.

## The six gates, in order, each one blocking

| Gate | Name | What runs | Blocks on |
|---|---|---|---|
| 0 | STATIC | lint and typecheck clean (tolerate a missing script); `git status` has no `.env`, `runs/`, `reports/` | any finding |
| 1 | CONTRACT | `check.mjs` C1 over `expectations.json`: budgets positive, ratios 0..1, gold path exists, no tool both required and forbidden | C1 fail |
| 2 | RUN | `bench --smoke`: a handful of requests complete inside budget with `terminated: "done"` | any over budget or not done |
| 3 | TRAJECTORY | `check.mjs` over `runs/`: A1, A2, A3, R1/R2 | any error-severity fail |
| 4 | EVAL | full bench -> `reports/eval.json` -> E1, E2 + the SLA percentiles | any threshold missed |
| 5 | HUMAN | P1: one successful and one failing trajectory, read end to end and named | cannot be automated or removed |

Exit codes: `0` pass, `1` warnings only, `2` at least one error. CI fails on `2`; `1` stays
visible. P2 warns while rules still carry `TODO` precedents; that nag is intentional.

## The run log is the seam

Everything in gates 3 and 4 reads `runs/<requestId>.json`, so its shape is fixed in the
contract and the student writes it in ten lines of adapter:

```json
{ "tokens": 18240, "wallClockSec": 6.4, "costUsd": 0.021, "terminated": "done", "depth": "quick",
  "toolCalls": [ { "name": "web_search", "ok": true }, { "name": "fetch_page", "ok": false, "error": "403 from publisher" } ] }
```

`terminated` is set explicitly at the call site because no SDK gives it to you. A failed call
carries a non-empty `error` (A1). The mode field is what lets a reader tell an expensive
legitimate run from a cheap run that ran away.

## The human gate is the point, not a formality

Before sign-off the student reads one complete successful trajectory and one complete failing
one, every step, and names both on the `/evals` page with what each taught them. Checklist:
each tool call was the one you would have made; every error surfaced as `ok: false` plus a
string, and to the user as a `502` or a marked partial; the loop stopped because it finished;
numbers match `expectations.json` by arithmetic; every citation traces to a retrieval in the
same run. **If they cannot produce a failing trajectory, they do not understand the failure
surface yet**: kill the search key and run again. Deliberate failures live in `runs/failing/`.

## The evidence page

The submission is one URL. The eval skill (`/fde-<codename>-eval`) runs the gates against the
**deployed** app, walks the student through the two manual rows and the trajectory read, and
calls the report builder, which assembles `report.json` from `reports/` so that no number is
retyped. The builder refuses a smoke run and exits non-zero on a red line. The provided UI
renders it at `/evals`. Never hand-edit the file; never write a number a run did not produce.

## Run the grader against a stub before anyone sees it

Write a throwaway backend that fakes the contract (a couple of hundred lines), run every gate
against it, and keep it out of the repo (it is an answer key). LUMINA's grader had eight bugs
until this was done, two of which would have failed every correct submission; both
rule-interaction traps in `03-gates.md` were found this way. A grader nobody has run is a
grader that does not work.

## Checklist

- [ ] Every automated rubric row and every SLA row names its instrument.
- [ ] Grounding is arithmetic with an unverifiable category; no error-severity check asks a model.
- [ ] Gold set: >= 30 items, provided corpus, stable anchors, validator, licence.
- [ ] One check runs the same input through both modes.
- [ ] Six gates in order; exit codes stated; run-log shape fixed.
- [ ] P1 human gate present and un-automatable; `runs/failing/` convention stated.
- [ ] The eval skill and report builder are in the staff build list; numbers on `/evals` come only from a run.
- [ ] The stub run is scheduled, and the summary says it has not happened until it has.
