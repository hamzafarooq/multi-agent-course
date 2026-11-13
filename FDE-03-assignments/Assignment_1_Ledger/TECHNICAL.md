# TECHNICAL.md: building Ledger

The build guide: setup, then one part per lesson, each with what to build, a prompt to start
from, how to prove it, and what goes wrong. Requirements are in [`SPEC.md`](SPEC.md) (cited as
§n); file shapes in [`contract/`](contract/files.md). Keep `python scripts/status.py` open in a
second terminal: it is your progress bar.

**Contents:** [Architecture](#architecture) · [Setup](#setup) · [Part 1: Skills](#part-1-skills-todo-1) ·
[Part 2: Sub-agents](#part-2-sub-agents-todos-2-5) · [Part 3: The human gate](#part-3-the-human-gate-todo-6) ·
[Part 4: The agent team](#part-4-the-agent-team-todos-7-12) · [Part 5: Sign-off](#part-5-sign-off-todo-13) ·
[Evaluate](#evaluate) · [Time and cost](#time-and-cost) · [Deploy](#deploy) · [Grading](#grading-100-points) ·
[Stretch goals](#stretch-goals) · [Submit](#submit) · [Troubleshooting](#troubleshooting)

---

## Architecture

```
                     PROVIDED                                   YOU (TODO #n)
 ┌──────────────────────────────────────────┐   ┌──────────────────────────────────────────┐
 │ data/  the council's PDFs, workbooks, CSV │   │ #1  extract-rules SKILL.md               │
 │ contract/  schemas + file formats + the   │   │ #2  spend-analyst      (sub-agent)       │
 │            team's message protocol        │   │ #3  findings-analyst   (sub-agent)       │
 │ verify_quotes.py   verify_history.py      │   │ #4  risk-assessment SKILL.md (method)    │
 │ build_register.py  build_pack.py          │◄──┤ #5  risk-assessor      (sub-agent)       │
 │ checks: quotes, numbers, samples          │   │ #6  YOUR gate decisions                  │
 │ scripts/pdftext.py   scripts/status.py    │   │ #7  agent teams on + the lead's procedure│
 │ eval/ (the grader)  quality/ (the kit)    │   │ #8  audit-program SKILL.md (method)      │
 │ viewer/ (the site)  vercel.json           │   │ #9-#11 planner, challenger, qa-reviewer  │
 └──────────────────────────────────────────┘   │ #12 checks/check_trace.py                │
                                                 │ #13 YOUR sign-off                        │
                                                 └──────────────────────────────────────────┘
```

The guardrails on the left are deterministic: they decide pass or fail. What you write on the
right is judgment: what a model should read, decide, cite and refuse. The lesson of the
assignment sits where the two meet. Your skill can be clever, but `verify_quotes.py` decides
whether the quotes are real. Your planner can be ingenious, but `build_pack.py` draws the samples.

## Setup

**You need:** VS Code (or any editor), [Claude Code](https://code.claude.com/docs) signed in,
Python 3.11+, Node 18+, Git, a GitHub account and a Vercel account (free tier).

1. **Make it your own repository.** Copy this folder (`Assignment_1_Ledger/`) to a new, private
   GitHub repository and open **that folder** in VS Code, so it is the project root. Claude Code
   reads `CLAUDE.md` from the folder you open, and the eval finds your agents' transcripts by
   that folder's path.
2. **Python environment.**

   ```bash
   python3 -m venv .venv
   .venv/bin/pip install -r requirements.txt        # macOS / Linux
   .venv\Scripts\pip install -r requirements.txt    # Windows
   ```

   Then activate it (`source .venv/bin/activate`, or `.venv\Scripts\activate` on Windows) so
   that `python` below means the venv's.
3. **Poppler's `pdftotext`.** macOS `brew install poppler`; Debian/Ubuntu
   `sudo apt install poppler-utils`; Windows `winget install oschwartz10612.Poppler` (or
   `choco install poppler`), then open a new terminal. **Windows users: Git for Windows ships a
   different `pdftotext` (Xpdf), and Claude Code's Bash tool finds it first.** Its tables come
   out differently, so quotes copied from it fail verification. `scripts/pdftext.py` and both
   verifiers search for the poppler build and refuse Xpdf; `python scripts/pdftext.py --which`
   shows which one you have.
4. **Check.** `python scripts/status.py` shows 0 of 13 done and every tool `ok`. Then
   `node viewer/collect.mjs` and open `viewer/dist/index.html` through any static server
   (`python -m http.server -d viewer/dist`): every panel says **Not built yet**. Those panels
   light up as you build.
5. **Study the data before you brief an agent about it.** In Claude Code:

   ```
   Read CLAUDE.md, SPEC.md §4 and data/SOURCES.md. Then inspect data/ with .head(), .info()
   and aggregates only, never whole tables: for each spend workbook the sheet name, which row
   holds the header, the date type, the row count; how many contracts.csv rows belong to the
   council and under which spellings. Report every mismatch with SPEC.md §4. Change no file.
   ```

## Part 1: Skills (TODO #1)

**What.** `.claude/skills/extract-rules/SKILL.md` (SPEC §6). A skill is a procedure in a file:
Claude Code loads it when you type `/extract-rules` and follows it in the main session, where
you can watch.

**Start from.**

```
Read SPEC.md §6, contract/rules.schema.json and the stub .claude/skills/extract-rules/SKILL.md.
Write the skill. It must extract text with scripts/pdftext.py, account for every clause and
table row, and loop on verify_quotes.py until ALL CHECKS PASSED. Before you write, tell me how
the skill will decide "testable" versus "excluded"; that is the part I want to review.
```

Review that decision rule yourself. It is where recall and precision are won.

**Prove it.** Run `/extract-rules` in a fresh session. Then:
`python .claude/skills/extract-rules/verify_quotes.py outputs/rules.json data/contract-rules.pdf`
→ `ALL CHECKS PASSED`. Spot-check three quotes against the PDF yourself. Then measure the skill:
`python eval/skill/run_eval.py --runs 3` (several minutes per run). Its report lists the answer-key
clauses each run missed. **Improve the skill's instructions, not the key**: the key is the
grader's (and editing it is a red line).

**Goes wrong.** Quotes "not found" → copied from layout text, or across a page footer. IDs not
sequential → the verifier wants `CPR-01`, `CPR-02`, … in document order. Statutory thresholds
filled in → they must be `parameters` with `value: null`.

## Part 2: Sub-agents (TODOs #2-#5)

A sub-agent runs in its own context window with its own tools and hands back a summary and
files. Use one when the work is long, noisy, or needs isolation. The main session stays clean
and you get a report.

### #2 spend-analyst (SPEC §7)

The biggest brief. Ask Claude Code to draft it from SPEC §7 and `contract/files.md`, then read it
against the checklist in the stub. Decide its `tools:` line yourself: it must write and run
Python; what else? **Run:** "run the spend-analyst". **Prove:** `status.py` shows
`analytics.json` valid and `spend-clean.csv` present; `analytics-full/selfcheck.json` has one
passing item per test that ran. Open one `row_id` from the self-check in the workbook yourself.
**Goes wrong:** a threshold typed into a script (the evaluation lists it as a note on `analytics_reproducible`); the
whole dataframe printed into context (slow, expensive, and visible in the transcript);
`spend-clean.csv` without `supplier_norm` or `row_id` (the pack builder will fail later, so check now).

### #3 findings-analyst (SPEC §8)

Records, never judges. **Prove:** `python scripts/verify_history.py outputs/history.json data/committee`
→ `ALL CHECKS PASSED`. Check that `scoring_method` matches the strategy's matrix, and that the
absent Strategic Risk Register is listed under `gaps`.

### #4 risk-assessment skill, #5 risk-assessor (SPEC §9, §10)

The method is a skill; the agent is a job description that says "load the skill and follow
it". Ask yourself why that split matters before you write either; it is a DESIGN.md question.
**Run:** "run the risk-assessor". **Prove:** `build_register.py outputs/risk-ratings.json`
reports `failures: 0`; open `outputs/risk-register.md` and check two citations by hand.
**Goes wrong:** risks silently dropped → a justification with no resolvable citation (the
builder lists them under "Excluded by validation"); literal £ figures in prose → use `{{$.path}}`.

## Part 3: The human gate (TODO #6)

Open `outputs/auditor-comments.md`. For each risk write `approve`, `amend` or `reject` in
Decision, and a Comment for every amend or reject saying exactly what and why ("likelihood 3:
the metric is material but the 2024/25 audit gave Substantial assurance"). Fill `Reviewer:`
and `Date:`. Then: "run the risk-assessor again". **Prove:** `build_pack.py --gate` → gate closed,
register revision 1. You need at least one reasoned amend or reject; a person grades the reasoning.

## Part 4: The agent team (TODOs #7-#12)

A teammate is unlike a sub-agent: it stays alive, and teammates message each other directly.
The challenger argues with the planner; the qa-reviewer sends it failures; the planner rebuilds.
That loop is what you are building.

1. **#7** Set `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` to `"1"` under `env` in `.claude/settings.json`
   and restart Claude Code. Write the lead's procedure in `CLAUDE.md` (SPEC §12): gate first,
   spawn three named teammates, let them run, shut down on three DONEs, report.
2. **#8** the audit-program skill (SPEC §13). The planner's method. Samples are recipes the builder
   draws; read `contract/files.md` for the sample sources and their columns.
3. **#9-#11** the three teammates (SPEC §14-§16) and the protocol in `contract/team-protocol.md`.
   The prefixes are not decoration: the grader scores teamwork from them.
4. **#12** `scripts/checks/check_trace.py`. Implement the four functions; the docstring is the
   spec. Fastest loop: `python eval/planted/plant_errors.py`. It plants seven mistakes in a copy of
   your pack and shows which your checks catch. Three are yours to catch.

**Run:** "run the agent team for the audit planning pack". It takes 30 to 60 minutes. Watch the
messages go by; they are your video's best ten seconds. **Prove:** `python scripts/checks/run_checks.py`
→ `READY FOR SIGN-OFF (4/4)`; `outputs/challenges.md` has no open row.
**Goes wrong:** the challenger reads `analytics-full/` or runs Bash (teamwork critical/minor
fail, from the transcript); QA writes its review before `CHALLENGER DONE` (trace fails on open
challenges); the planner edits `audit-program.md` by hand (overwritten by the next build, and
it fails "matches a fresh build").

## Part 5: Sign-off (TODO #13)

Read `outputs/review.md` and the "For the auditor at sign-off" list in `challenges.md`. Decide.
Complete the block: name, date, `sign off` or `return to the team`, and a comment that deals with
every challenge left for you. Never sign a BLOCKED pack.

## Evaluate

```bash
python eval/run_all.py                    # the whole pipeline, read-only → reports/system.md
python eval/planted/plant_errors.py       # 7 of 7?
python eval/skill/run_eval.py --runs 3    # the skill, three fresh sessions
python eval/export_runs.py                # your agents' transcripts → runs/
python eval/build_report.py --student "Your Name" --video https://…   # the score → reports/report.json
```

Or in Claude Code: `/fde-ledger-eval`, which runs these in order and walks you through the
three parts only you can supply:

- **the live test**: five or more rules from clauses the answer key does not cover, checked by
  you against the PDF (`live-test.md`). A skill tuned only to the answer key's clauses shows up here;
- **the design interview**: five questions about your `DESIGN.md`, your answers recorded verbatim
  (`design-interview.md`);
- **your two trajectories**: copy `trajectories.template.md` to `trajectories.md`.

It writes `reports/report.json` (what `/evals` renders) and `reports/PRODUCT_EVAL.md`, your
evaluation report, then confirms the deployment. `eval/README.md` explains each tool and shows what
the reference build scored.

`quality/check.mjs` always prints two course-level notices you cannot clear and that score
nothing: P2 (the course's own rules still lack precedents) and E3 (a reminder that judges never
decide). The rules that matter for you are A1-A3 and B1-B2.

**Optional: AI judges.** `python eval/subagents/run_eval.py` and `python eval/team/run_eval.py`
have a model review each agent against `eval/subagents/rubric.md` and `eval/team/rubric.md`. They
score no points and use Claude Code usage; run them if you want a second opinion on a brief.

## Time and cost

Plan on a weekend: about a day of building and reading, plus agent time. The reference build
used about 75 agent-minutes for one full pipeline run (spend-analyst 8, findings-analyst 7,
risk-assessor 8 + 2, planner 24, challenger 12, qa-reviewer 13), with a peak context of about
263k tokens. Expect two or three full runs while you tune, and three skill runs for the eval.
There is no API bill: everything runs inside Claude Code on your plan; heavy runs count against
its usage limits, so start the team run when you have an hour.

## Deploy

| Piece | Host | Fixed? |
|---|---|---|
| The viewer (`/`, `/evals`, `/data`): this URL is the submission | **Vercel** | Yes |
| The harness itself | your machine, in Claude Code | Yes: it is not deployed; its outputs are |
| Anything holding keys | none: Ledger has no keys | n/a |
| Database | none: the state is the files in `outputs/` | n/a |

1. Commit everything the build reads: `outputs/`, `eval/skill/runs/`, `runs/`,
   `reports/report.json`, `reports/PRODUCT_EVAL.md`, `DESIGN.md`, `trajectories.md`, `live-test.md`,
   `design-interview.md` (`.gitignore` already keeps the rest out).
2. In Vercel: **Add New → Project**, import your repository, leave the root directory as the
   repository root. `vercel.json` sets the build (`node viewer/collect.mjs`, no install) and the
   output (`viewer/dist`). Deploy.
3. Open `/`, `/evals` and `/evals/report.json`. Then run the grader's tool against it:
   `python eval/grade_url.py https://<your-app>.vercel.app` must say **every re-derivable number reproduced**.

Every change to `outputs/` or the report means: re-run `build_report.py`, commit, push. Vercel
redeploys on push.

## Grading (100 points)

Eighty automated points from `eval/rubric.json`, scored by arithmetic and re-derived by the
grader from your deployment, except the rows marked *self-reported*, which only your local
transcripts can show and which the grader checks against your trajectories and video. Twenty
manual points are scored by a person. The rubric file is the authority; this is the shape:

| Area | Points | How |
|---|---|---|
| The skill's rules are right | 15 | answer key, three fresh runs |
| Analytics reproducible | 10 | schema, self-check, thresholds traced to rules |
| History sourced to the page | 5 | schema, verifier |
| Every rating cites evidence | 10 | schema, builder, register equals a fresh build |
| The human gate holds | 10 | gate closed, revision, a reasoned amend or reject |
| The pack passes QA | 10 | the four checks |
| Your checks catch planted errors | 10 | seven plants, golden thread |
| It worked as a team | 5 | from the transcripts (*self-reported*) |
| Harness hygiene | 5 | least privilege, team flag, no TODOs; run budgets (*self-reported*) |
| Design (with the interview), trajectories, your judgment, video | 20 | a person |

**Sample scorecard** (illustrative only; yours comes from your run, and fabricating one is an
automatic fail):

| Row | Points | Awarded | Status | Evidence |
|---|---|---|---|---|
| rules_extracted | 15 | 10 | ⚠️ Partial | weakest run found 84%; not invented 100%; fields 97% |
| pack_checks_pass | 10 | 10 | ✅ Pass | quotes, numbers, trace, samples all PASS |
| teamwork | 5 | 3 | ⚠️ Partial | the challenger used Bash beyond its definition |

**Red lines** (automatic fail): a number on `/evals` the grader cannot reproduce; a provided file
changed (self-reported; the grader uses its own copies anyway); a builder-rendered file edited by
hand (gates `Register` and `Pack (rendered)`); an accusation in a risk, challenge or memo (gate
`Language` lists the lines, a person decides); a supplier name published (the build fails);
DESIGN.md, interview answers, gate decisions or trajectory notes not your own.

## Stretch goals

Five points each, from `eval/rubric.json`: a new quality rule with a real precedent from your own
run; three skill runs each at found ≥ 95% with ≥ 90% agreement; a Claude Code hook that blocks a
write to `data/` or a hand edit of a rendered file, shown firing in a transcript.

## Submit

You submit three things, all reachable from **one URL**, your Vercel deployment:

1. **The deployed product**: `/`, your audit pack.
2. **The evaluation report**: `/evals` (also `/evals/PRODUCT_EVAL.md`, and
   `/evals/report.json` for the grader's tools).
3. **The demo video**: embedded on `/evals` (pass `--video` to `build_report.py`).

No repo, no zip. Course-wide rules: [`SUBMISSION.md`](../../SUBMISSION.md).

The 60 to 90 second video shows, in order: `/extract-rules` finishing with ALL CHECKS PASSED; one
sub-agent running; you recording a gate decision; the team's messages (a PACK READY, a CHALLENGE
and its RESPONSE); the QA verdict; then `/` and `/evals` on the deployed URL. The team run takes
30 to 60 minutes: record it and cut or speed it up. Show the messages, not the wait.

### Requirements checklist

- [ ] #1 `/extract-rules`: `verify_quotes.py` ALL CHECKS PASSED; three skill runs saved
- [ ] #2 spend-analyst: `analytics.json` valid; `selfcheck.json` covers every test that ran
- [ ] #3 findings-analyst: `verify_history.py` ALL CHECKS PASSED
- [ ] #4, #5 risk-assessment and risk-assessor: `build_register.py` failures 0
- [ ] #6 every risk decided, at least one reasoned amend or reject; register is a revision
- [ ] #7 agent teams enabled; the lead's procedure in `CLAUDE.md`
- [ ] #8, #9 audit-program and planner: `build_pack.py` failures 0
- [ ] #10 challenger: `challenges.md` with no open row
- [ ] #11 qa-reviewer: `review.md` with the results table as printed
- [ ] #12 `check_trace.py`: trace PASS; planted errors 7 of 7
- [ ] #13 sign-off block completed
- [ ] `DESIGN.md`, the design interview, `live-test.md`, `trajectories.md`
- [ ] deployed; `grade_url.py` reproduces every number; video linked

### Definition of done: this section is written for your coding agent

Verify, do not assume. Every line must hold before you tell the student the work is done
(the same block as `SPEC.md` §22):

```bash
python scripts/status.py                         # 13 of 13 done; every JSON output "valid"; no parent CLAUDE.md warning
python .claude/skills/extract-rules/verify_quotes.py outputs/rules.json data/contract-rules.pdf   # ALL CHECKS PASSED
python scripts/verify_history.py outputs/history.json data/committee                              # ALL CHECKS PASSED
python .claude/skills/risk-assessment/build_register.py outputs/risk-ratings.json                 # failures: 0, revision >= 1
python .claude/skills/audit-program/build_pack.py --gate                                          # gate closed
python scripts/checks/run_checks.py              # VERDICT: READY FOR SIGN-OFF (4/4)
python eval/planted/plant_errors.py              # 7 of 7, baseline yes
python eval/run_all.py                           # every gate passes, including Pack (rendered) and Language
python eval/build_report.py --student "…" --video …   # no red-line FLAG; "Still missing" empty
node viewer/collect.mjs                          # no LEAK
python eval/grade_url.py https://<your-app>.vercel.app   # every re-derivable number reproduced
```

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Every quote "NOT FOUND", tables garbled | Xpdf's `pdftotext` (Git for Windows), or text copied from the `--layout` file | Install poppler; `python scripts/pdftext.py --which`; quote from the plain text |
| `UnicodeEncodeError` / `UnicodeDecodeError` | Windows console encoding | The provided scripts fix themselves; for your own, set `PYTHONUTF8=1` |
| `export_runs.py` finds no transcripts / teamwork "No team transcripts found" | Claude Code was opened on a parent folder, so the transcripts are filed under another project | Open the assignment folder itself in Claude Code and re-run |
| Agent teams do nothing; teammates never spawn | Flag not set, or the session predates it | Set it in `.claude/settings.json` → `env`, restart Claude Code |
| `build_register.py`: risk "excluded by validation" | A justification has no resolvable citation, or a metric path points at an object, not a scalar | Cite a scalar path that exists in `analytics.json` |
| `build_pack.py`: "sampled row_id … not found in spend-clean.csv" | The analytics-full file and `spend-clean.csv` disagree on `row_id` | Fix the spend-analyst's scripts; re-run it, then the planner |
| `build_pack.py --gate` fails after decisions | The risk-assessor did not re-run, or did not write the `revision` block | "run the risk-assessor again" |
| trace FAIL: "challenges still open" | QA ran before `CHALLENGER DONE` | The qa-reviewer waits for both DONE messages before its final run (SPEC §16) |
| Planted errors: baseline NO | The untouched pack fails a check, so no catch counts | Get `run_checks.py` to 4/4 first |
| `collect.mjs`: LEAK | A supplier name escaped pseudonymisation (often a name with quotes in it) | Tell your instructor; do not deploy until fixed |
| `grade_url.py`: FABRICATED | The deployed `report.json` is older than the deployed `outputs/` | Re-run `build_report.py`, commit both, push |
| A run hit a usage limit mid-team | Long team runs are heavy | When the limit resets, run the team again. `outputs/` persists, so tell the lead what state `challenges.md` and `review.md` are in |
