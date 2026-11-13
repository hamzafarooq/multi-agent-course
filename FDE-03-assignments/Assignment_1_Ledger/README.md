# Assignment 1: LEDGER

> Build the harness for a procurement audit planner. Agents read a council's purchasing
> rulebook, analyse every payment, fold in past audit findings and rate the risks; you approve
> them; an agent team turns them into a checked audit plan; you sign it off.

You are given the data, the brief, the file contract, the guardrails, the grader and a viewer
site. You build the **harness**: the skills, the sub-agents and the agent team, plus one check,
plus your own decisions at two human gates. When your harness works, the site lights up.
That's the whole game.

---

## Start here

First, **copy this folder into a new private repository of your own** and open *that* folder
in Claude Code. Inside the course repo, Claude Code would also load the course tutor's
`CLAUDE.md`, and the eval would not find your agents' transcripts.

```bash
python3 -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python scripts/status.py                             # your progress bar: 0 of 13
node viewer/collect.mjs && python -m http.server -d viewer/dist 8000   # then open http://localhost:8000
```

Every panel of the site says **Not built yet**. That message is your progress bar (it plays
the part of LUMINA's `501`). Each TODO you finish lights one up.

## Then read, in this order

| # | Read | Why |
|---|---|---|
| 0 | [`START_HERE.md`](../../START_HERE.md) *(repo root)* | Course-wide: which files are for you, which for your coding agent, how to drive the build. ~10 min. |
| 1 | [`PRD.md`](PRD.md) | What the product is, the lesson, and the rules that decide your grade. ~10 min. |
| 2 | [`CLAUDE.md`](CLAUDE.md) and [`contract/files.md`](contract/files.md) | The system's flow, and how the components hand files to each other. |
| 3 | [`DESIGN.template.md`](DESIGN.template.md) | Copy to `DESIGN.md` and answer the five questions **before you write a skill**. Graded. |
| 4 | `benchmark/sla.json`, `expectations.json`, `eval/rubric.json` | The bars, the budgets, the points. Declared before you run, on purpose. |
| 5 | [`TECHNICAL.md`](TECHNICAL.md) | The build guide: setup, one part per lesson, troubleshooting. |

Your coding agent reads [`AGENTS.md`](AGENTS.md) (imported by `CLAUDE.md`) and
[`SPEC.md`](SPEC.md), which has every requirement, one section per TODO. Where your `DESIGN.md`
and the SPEC disagree, the SPEC wins: change the design.

## What you build

| | |
|---|---|
| ✅ **Provided** | `data/` (public council data), `contract/`, the verifiers and builders, three of four QA checks, `scripts/pdftext.py`, `scripts/status.py`, `eval/` (the grader), `quality/`, `viewer/`, the `/fde-ledger-eval` skill. |
| 🔨 **Yours** | Thirteen TODOs: the skills, the agents, the lead's procedure, `check_trace.py`, and two decisions only a human can make. |

Do not edit anything provided. It is hashed, and the grader re-runs everything with its own copy.

## The build, in one screen

1. **#1** `/extract-rules` skill: rulebook → `rules.json`, every quote verified.
2. **#2** `spend-analyst` sub-agent: every payment tested by Python it writes and runs.
3. **#3** `findings-analyst` sub-agent: past audits and the council's risk scale, sourced to the page.
4. **#4** `risk-assessment` skill (the method) and **#5** `risk-assessor` sub-agent (the job) → the risk register.
5. **#6** **You** approve, amend or reject every risk. Nothing is planned until you do.
6. **#7** Turn on agent teams; write how the lead runs the team.
7. **#8** `audit-program` skill and **#9** `planner`, **#10** `challenger`, **#11** `qa-reviewer` teammates.
8. **#12** `check_trace.py`: the check that ties every rule, risk and challenge together.
9. **#13** **You** sign off, or send it back.

Each step is a section in [`TECHNICAL.md`](TECHNICAL.md) with a prompt to start from, the proof
it works, and what goes wrong.

## How you prove it

```bash
python scripts/checks/run_checks.py      # the pack's four QA checks
python eval/planted/plant_errors.py      # do your checks catch seven planted mistakes?
python eval/run_all.py                   # the whole pipeline, every gate
```

Right but untraceable fails. Clever but unchecked fails. The bars are in `benchmark/sla.json`;
[`eval/README.md`](eval/README.md) explains every tool and what the reference build scored.

## How you submit

You hand in three things, all at **one URL** (your app on **Vercel**): the **deployed product**
(`/`, your pack), the **evaluation report** (`/evals`, also as `/evals/PRODUCT_EVAL.md`), and
the **demo video**, embedded on `/evals`. No repo, no zip.

In Claude Code, run `/fde-ledger-eval`. It runs the evaluation, walks you through the live
test, the design interview and your two trajectories, writes `reports/report.json` and
`reports/PRODUCT_EVAL.md`, and checks your deployment with the grader's own tool. Deploy steps and the video checklist:
[`TECHNICAL.md`](TECHNICAL.md#submit) · course-wide rules: [`SUBMISSION.md`](../../SUBMISSION.md).

## Stuck?

[`TECHNICAL.md`](TECHNICAL.md#troubleshooting) covers the failures that cost the most time:
quotes that will not verify on Windows, agents that print whole datasets, a register that drops
risks, a gate that will not close, and a team whose challenges stay open.
