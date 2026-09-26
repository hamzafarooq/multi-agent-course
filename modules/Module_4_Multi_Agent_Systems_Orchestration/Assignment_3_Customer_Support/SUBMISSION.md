# SUBMISSION

Submit one message to the course channel containing three links, before the deadline in
`PRD.md`'s byline.

## 1. Your repo

A GitHub repo (public, or shared with the instructor) containing:

| Must contain | Must not contain |
|---|---|
| Your code, `tools.yaml`, `db/seed.sql`, your run script | `.env` or any key (red line) |
| `DESIGN.md` and `BUILD_LOG.md`, in your own words | `runs/` or `reports/` beyond the files below |
| `reports/eval.json` from your final run, written by your runner | A hand-edited report (red line) |
| `runs/failing/` with your deliberate failing turn | |
| The provided Markdown files, **unchanged** | |

Before you push, run the Definition of Done in `TECHNICAL.md` §6, all twelve lines.

## 2. Your eval report

Link to `reports/eval.json` in the repo, plus the terminal output of the run that produced
it (a gist or a file in the repo). The grader re-computes pass/fail from the report's values
against `THRESHOLDS.md`; a report whose values don't match its own items fails.

## 3. A video, at most five minutes

Screen recording with your voice. Shot list:

1. `./run.sh status`: everything up.
2. **Scenario A** in the web UI: the steps appear as they happen. Open the trace in Phoenix
   and name each span in the tree.
3. **Scenario B**: Alice asks about order 5. Show the reply, then show the SQL line that made
   it safe.
4. **Scenario C**: the injection, blocked. Show where in the trace it stopped.
5. **Scenario D**: plant, wait, ask. Show the recall list and its scores.
6. **Scenario E**: the cheap path, and its latency in the trace.
7. Stop the Judge and send a message. Show the error, and explain why it's an error and not
   an answer.
8. The CLI, with the same message as scenario A, so both front ends are shown.
9. Thirty seconds: the one false block and the one false pass you found in your own build,
   and what you changed.

## What the grader does

Runs nothing of yours: they read your report, your two Markdown files and your video, and
spot-check three items from the report against the traces you name. A number that no run
produced, a secret in the repo, or edited provided files each cap the grade (THRESHOLDS §8).
