# eval/: the grader

Provided. Do not edit (`eval/integrity.json` holds a hash of every file here). These are the
same tools the grader runs, so a passing number here is a passing number there.

| Command | What it answers | Writes |
|---|---|---|
| `python scripts/status.py` | Where am I? The thirteen TODOs, the outputs, the tools | nothing |
| `python eval/run_all.py` | Does the whole pipeline hold? Contract schemas, every verifier and builder, the four QA checks, the golden thread, planted errors, teamwork, cost | `reports/system.md`, `reports/system.json` |
| `python eval/planted/plant_errors.py` | Do my checks catch seven known mistakes? (fast loop for TODO #12) | `reports/planted.json` |
| `python eval/skill/run_eval.py --runs 3` | Is `/extract-rules` right, and consistently right? Fresh sessions against `skill/answer-key.csv` | `eval/skill/runs/run-N/` |
| `python eval/export_runs.py` | What did each agent actually do? Transcripts → run logs | `runs/*.json` |
| `node quality/check.mjs .` | Did every run stay inside its budget and terminate? (course quality kit) | `reports/quality.json` |
| `python eval/build_report.py --student "…" --video …` | The score. Runs the three above, does the rubric arithmetic, reads DESIGN.md and trajectories.md | `reports/report.json` |
| `python eval/subagents/run_eval.py`, `python eval/team/run_eval.py` | Optional: an AI judge reviews each agent against `subagents/rubric.md` / `team/rubric.md`. Advisory, no points | `*/judgements/` |
| `python eval/grade_url.py <url>` | The grader: re-derives every number from your deployment's `/data` and compares | `reports/grade-<host>.md` |

## The four laws

1. **Arithmetic decides; a judge never does.** Every automated point comes from a script's
   exit code or count. The AI judges report; they never score.
2. **Declared before the first run.** The bars are in `benchmark/sla.json` and
   `expectations.json`. They do not move.
3. **A thing that ran is not a thing that worked.** The checks verify outputs against the
   sources: the PDF, the workbooks, the analytics.
4. **The URL proves itself.** `grade_url.py` rebuilds your project from the course's own
   provided files plus what your deployment published, and re-runs everything. A number it
   cannot reproduce is fabricated.

## What the reference build scored

A finished build of this system (the instructors' reference) was evaluated with these tools.
Use its numbers to calibrate, not as a target: two of its own rows fall short of the bars.

| | Reference |
|---|---|
| `/extract-rules`, weakest of three runs | found 82%, not invented 100%, fields right 97% (bar: 90 / 90 / 85) |
| Pipeline checks | 15 of 15 pass |
| Golden thread | 562 of 562 sampled payments trace to a verified quote and an approved risk |
| Planted errors | 7 of 7 caught |
| Challenges | 12 raised, 11 resolved, 1 for the auditor |
| Agent time | 75 minutes across 7 agent runs; peak context 263k tokens (the challenger) |
| Automated score | 68 / 80 measured from its published outputs, without its transcripts: the skill row at 10 of 15, teamwork 0 and two hygiene items unscored for lack of transcripts. Its own teamwork evaluation, from its transcripts, scored 2 of 3 (the challenger used Bash and Edit beyond its definition), which is 3 of 5 points here |

## Windows

Every script re-runs itself in Python's UTF-8 mode on Windows, so the £ signs and curly
quotes in the data print correctly. If you run Python another way and see a
`UnicodeEncodeError`, set `PYTHONUTF8=1`.
