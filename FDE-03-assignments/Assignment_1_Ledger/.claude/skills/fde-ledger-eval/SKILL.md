---
name: fde-ledger-eval
description: Evaluate the student's Ledger harness from a real run and produce the reports/report.json their deployed /evals page renders, then confirm the deployment reproduces it. Use when the student says they are ready to submit, wants to run the eval, asks for their score, or says "eval my Ledger".
---

# Ledger: product evaluation

Your job: get **`reports/report.json`** built from a real run, published at
`/evals/report.json` on the student's Vercel deployment, and **confirmed by the grader's own
tool against that deployment**. That page is the submission (`SUBMISSION.md` at the course root).

**The one rule: never write a number a run did not produce.** You score nothing by reading
files or judging prose. `eval/run_all.py` runs the checks, `eval/build_report.py` does the
arithmetic, `eval/grade_url.py` re-derives it from the deployment. You orchestrate, ask the
student for the things only they can supply, and tell them the truth about what failed.

If a step fails, **stop and report it** in one sentence, name the rubric row it costs, and
give the smallest next action. A partial report from a real run beats a complete one from a
run that did not happen.

## Step 0: what you need from the student

Ask once, in one message, for whatever is missing:

1. **Their name** as it should appear on the page.
2. **The video URL** (60 to 90 s, YouTube or Loom). If it is not recorded yet, tell them what
   it must show (`eval/rubric.json` → `video_demo`) and carry on; the row stays open.
3. **`DESIGN.md`**, the five headings answered. If it is missing or still the template, do
   **not** write it: it is graded as their own words. Point them at `DESIGN.template.md`.
4. **The deployed URL**, if they have deployed. If not, Step 5 deploys.

Then run `python scripts/status.py`. If any of TODOs #1 to #13 is still open, say which and
stop: an evaluation of an unfinished harness is a progress check, not a submission. Offer to
continue as a progress check if they want one.

## Step 1: the skill runs

The `rules_extracted` row needs **three** fresh-session runs of `/extract-rules`:

```bash
ls eval/skill/runs/                      # how many exist
python eval/skill/run_eval.py --runs 3   # several minutes per run; restores outputs/rules.json after
```

Run only as many as are missing. If a run fails to produce `rules.json`, show its
`session.log` tail and stop.

### Step 1b: the live test (rules the key does not cover)

The answer key scores 30 clauses, and the student can see it. The live test is the part
they cannot tune for. The student copies `references/live-test-template.md` (in this
skill's folder) to `live-test.md` and checks **five or more** rules from clauses that are NOT
in `eval/skill/answer-key.csv` against the PDF: a mix of prose clauses and appendix rows.
You may list which `rule_id`s in `outputs/rules.json` fall outside the key, and open the PDF
page for them. The verdicts are theirs.

## Step 2: the two trajectories (the human gate on the harness, rule P1)

```bash
python eval/export_runs.py
```

Show the student the table. Ask them to pick **one successful run and one failing run** (a
run with errored calls, a run whose output a verifier rejected, or a run before a fix).
They copy `trajectories.template.md` to `trajectories.md`, put the two run ids in the
headings, read each run's steps (`runs/<id>.json`) **end to end**, and write in their own
words what it taught them and what they changed in a skill or agent file because of it.

You may open a run and walk through its steps with them. You may not write their notes.
If they ask you to, decline plainly and explain that P1 is the one row a model must not do.

### Step 2b: the design interview

Read `DESIGN.md` and the harness files, then follow `references/design-interview.md`: five
questions, one per heading, each made specific to what the student wrote, asked one at a
time. Record every answer verbatim in `design-interview.md`. You ask and record; you never
answer, hint or score. A person grades the `design` row with it.

## Step 3: the evaluation

```bash
python eval/build_report.py --student "<name>" --video "<url>" [--url "<deployed url>"]
```

It exports runs, runs `eval/run_all.py` (a few minutes), the quality kit, and the
arithmetic, then prints the automated score and the first thing to fix. It writes
`reports/report.json` (what `/evals` renders) and **`reports/PRODUCT_EVAL.md`**, the
human-readable evaluation report (shape: `references/product-eval-template.md`). Report
the table as printed. If `First thing to fix` names a row, explain which file or TODO that
row rests on, in one or two sentences. Do not re-run hoping for a different number.

The AI judges (`eval/subagents/run_eval.py`, `eval/team/run_eval.py`) are optional, score
no points and use Claude Code usage. Do not run them unless the student asks.

## Step 4: red lines, before anything is published

From `reports/report.json`:

Read `red_lines` in `reports/report.json`:

- `integrity.ok` is false → provided files were changed. Name them and stop; they must be
  restored (`git checkout -- <file>`), not explained.
- Gate `Register` or `Pack (rendered)` says a file differs from a fresh build → a rendered
  file was edited by hand. Rebuild it with its builder; never edit it back by hand.
- Gate `Language` lists lines → show each to the student. If a line accuses a supplier,
  officer or service, the owning agent's output must be regenerated. A fair citation (an
  "anti-fraud plan" in the history) is fine, but the student decides, not you.
- `harness.todo_files` not empty → a TODO is unfinished.

## Step 5: publish and confirm

```bash
node viewer/collect.mjs        # builds viewer/dist; fails on any supplier-name leak
```

Then commit and push (`outputs/`, `eval/skill/runs/`, `runs/`, `reports/report.json`,
`reports/PRODUCT_EVAL.md`, `DESIGN.md`, `trajectories.md`, `live-test.md` and
`design-interview.md` must all be committed, because Vercel builds from the repo),
and let Vercel deploy (TECHNICAL.md, "Deploy"). When it is live:

```bash
python eval/grade_url.py https://<their-app>.vercel.app
```

This is the grader's own tool. Report its verdict word for word. `every re-derivable number
reproduced` is the bar. Anything marked FABRICATED means the deployment and the report
disagree: usually a stale `reports/report.json` or an un-pushed `outputs/` change. Fix by
re-running Step 3 and redeploying, never by editing the JSON.

## Step 6: the handover

Tell the student, in under 200 words: the automated score, which manual rows a person will
score and what each needs from them (`eval/rubric.json` → `manual`), anything still open
(video, DESIGN.md, the interview, the live test, trajectories, sign-off), and what to submit:
**the URL**. Its `/evals` page carries the evaluation report (also at
`/evals/PRODUCT_EVAL.md`) and the embedded video. Nothing else.

## Not this skill's job

- Fixing their harness. Point at the TODO and the SPEC section; they fix it.
- Writing DESIGN.md, trajectory notes, gate decisions or the sign-off.
- Scoring the manual rows.
