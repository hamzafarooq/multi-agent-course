---
name: fde-lumina-eval
description: Run the six LUMINA gates against a deployed (or local) gateway and write the report.json that the provided UI renders at /evals. Use when the student says they are ready to submit, wants to run the eval, asks for their score, or says "eval my LUMINA".
---

# LUMINA — Product Evaluation

Your job: produce **`report.json`** in the `EvalsReport` shape from `packages/contract`, from a
real run against the student's **deployed** gateway, and get it served at
`GET /evals/report.json` so the provided UI renders it at `/evals`. That page is the whole
submission (`SUBMISSION.md`).

**The one rule: never write a number a run did not produce.** You do not score anything by
reading code or by judging an answer. `benchmark/bench.mjs` measures, `quality/check.mjs`
applies the rules, `eval/build-report.mjs` assembles. You orchestrate, ask the student for
the three things only they can supply, and tell them the truth about what failed.

If a gate fails, **stop and report it**. A partial report from a passing run beats a
complete one from a run that did not happen.

## Step 0 — What you need from the student

Ask once, in one message, for whatever is missing:

1. **Their name** as it should appear on the page.
2. **The deployed gateway URL** (`https://…`). Confirm `curl -sf <url>/health` returns 200
   and names a model, a search provider, and a vector store. If they only have it running
   locally, say plainly that a local run cannot be submitted, then continue locally so they
   can see where they stand.
3. **The video URL** (60 to 90 s, YouTube or Loom). If they have not recorded it, tell them
   what it must show — a quick question streaming with citations, the *same* question on Deep
   with the plan appearing first and merged citations at the end, a memory carrying into a new
   thread, a document question citing a page, and `/stats` showing the deep run's cost and the
   remaining daily allowance — and carry on without it; the page renders and the row stays open.
4. **`DESIGN.md`** with the five questions answered. If it is missing, do not write it for
   them: it is graded as their own words. Point them at `DESIGN.template.md`.

## Step 1 — Run the gates, in order

```bash
node eval/eval.mjs --deploy-url <gateway-url>
```

This runs all six in order and stops at the first failure: STATIC, CONTRACT, RUN (smoke),
TRAJECTORY, EVAL (full bench), HUMAN. It writes `reports/gates.json`, and the bench writes
`reports/bench.json` plus `reports/eval.json`.

If a gate fails, read its output, explain in one sentence what broke and which rule it maps
to, and hand back the smallest next action. Do not proceed to Step 3 with a failed gate;
the student can re-run once it is fixed.

Deployed instances write their run logs to Mongo rather than to disk, so if `runs/` is empty:

```bash
node scripts/export-runs.mjs        # pulls the runs collection into runs/
node quality/check.mjs .            # then the trajectory rules have something to read
```

## Step 2 — The two manual rows

Two rows need a person, and you are not that person: you set them up and report honestly.

**Deep search quality (5 pts).** Ask one question at both depths against the deployed app and put
the answers side by side for the student:

```bash
T=$(curl -s -X POST <gateway>/threads -H 'x-user-id: <them>' | jq -r .threadId)
curl -N -X POST <gateway>/threads/$T/ask -H 'x-user-id: <them>' -H 'content-type: application/json' \
  -d '{"query":"<their question>","mode":"web","depth":"quick"}'
curl -N -X POST <gateway>/threads/$T/ask -H 'x-user-id: <them>' -H 'content-type: application/json' \
  -d '{"query":"<their question>","mode":"web","depth":"deep"}'
```

Then ask them the question a grader will ask: is the deep answer *better*, or just longer? Are
those sub-questions ones a person would have asked? Report their answer; do not supply it, and
do not let a model grade prose that a human is supposed to grade (rule E3).

## Step 3 — The human gate (P1), which is the point

Gate 5 cannot be automated and you must not simulate it. Do this properly:

1. List the run logs in `runs/` with their `terminated` value and tool sequence.
2. Pick **one successful** run and **one failing** run and print each trajectory in full —
   every step, in order, with the error strings.
3. Walk the student through both and ask what each taught them. Their answer, in their
   words, becomes the `notes` on the page.

If there is no failing run, tell them to make one: unset the search provider key and ask a
question. A student who cannot produce a failing trajectory does not yet know their failure
surface, and that is the finding, not an inconvenience.

## Step 4 — Assemble the report

```bash
node eval/build-report.mjs \
  --student "<name>" \
  --video "<url>" \
  --design DESIGN.md \
  --successful <requestId> --failing <requestId> \
  --successful-notes "<their words>" --failing-notes "<their words>" \
  --notes "<model · search provider · Atlas tier>" \
  --out reports/report.json
```

It prints the scorecard and exits non-zero if a red line was crossed. Automated rows are
scored from the measurements; the three manual rows stay open for a grader — that is
correct, not a bug, so do not "help" by filling them in.

## Step 5 — Serve it and check the page

The gateway must serve the file at `GET /evals/report.json`. How is the student's choice
(a static route, a Mongo document, a bundled asset). Then:

```bash
curl -sf <gateway-url>/evals/report.json | head -c 400   # valid JSON, this run's numbers
```

Redeploy, open `<vercel-url>/evals`, and confirm it renders: the score, the gates, the SLA
table, the quality rules, the design section, both trajectories, the embedded video. If the
UI shows a schema error, the report does not match `EvalsReport` — re-run the builder rather
than hand-editing the file.

## Step 6 — Report back

Tell the student, briefly:

- the automated score and which rows are partial or failed, each with its one line of evidence;
- any red line crossed, in the first sentence, because it is an automatic fail;
- the three manual rows a grader still has to award (deep-search quality, the human gate, deploy);
- the single highest-value fix, in one sentence.

Then remind them the submission is the Vercel URL and nothing else: no repo, no zip, no code.

## Do not

- Do not edit `web/`, `packages/contract/`, `benchmark/`, `eval/`, `quality/` or `scripts/`
  to make a gate pass. That is a red line, and it is checked.
- Do not hand-edit `report.json`, ever.
- Do not lower a threshold in `benchmark/sla.json` or `expectations.json`. A threshold set
  after seeing the score is not a threshold, and rule E2's whole job is to notice. In particular,
  `min_deep_source_ratio` and `min_deep_sub_questions` are the two numbers that stop "deep search"
  from meaning "the same search, slower". If they fail, the fix is the planner, not the number.
- Do not ask a model whether an answer is good and put the answer in an error-severity row.
  A judge may report at `warn`; it may never block (rule E3).
