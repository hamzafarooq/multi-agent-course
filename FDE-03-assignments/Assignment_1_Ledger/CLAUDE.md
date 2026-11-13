# CLAUDE.md: Ledger, a procurement audit planning system

@AGENTS.md

An agent system that plans an internal audit of a council's procurement from its public
data. It turns the purchasing rulebook into testable rules, analyses every payment against
them, folds in past audit history, rates the risks for a human auditor to approve, and
turns the approved risks into a cross-checked audit planning pack.

**Everything here describes risk indicators to investigate. Nothing asserts wrongdoing by
the council, a department, an officer or a supplier.**

This file is the brief for the running system. `SPEC.md` holds every requirement in full,
one section per component. `contract/` fixes the shape of every file the components hand
each other. Where this file and `SPEC.md` are silent, ask; do not invent.

## How the system works

```
 data/contract-rules.pdf ──(1) /extract-rules  SKILL, run by the human ─────────► outputs/rules.json
                                     │
        ┌────────────────────────────┴──────────────────────────────┐
 (2) spend-analyst  SUB-AGENT                              findings-analyst  SUB-AGENT
     data/spend/*.xlsx + data/contracts.csv                data/committee/*.pdf
     writes and runs Python in scripts/                    reads, sources every item to a page
        │ outputs/analytics.json + analytics-full/                │ outputs/history.json
        └────────────────────────────┬──────────────────────────────┘
 (3) risk-assessor  SUB-AGENT, follows the risk-assessment SKILL
     → outputs/risk-ratings.json → build_register.py → risk-register.md + auditor-comments.md
                                     │
 (4) HUMAN GATE: the auditor approves, amends or rejects every risk in auditor-comments.md;
     the risk-assessor re-runs and the register becomes a revision
                                     │
 (5) AGENT TEAM, led by this session:
       planner      follows the audit-program SKILL → audit-plan.json → build_pack.py →
                    planning-memo.md, risk-control-matrix.md, audit-program.md, samples/
       challenger   → challenges.md; argues with the planner until every point is closed
       qa-reviewer  → runs scripts/checks/, writes review.md; blocks sign-off until all pass
                                     │
 (6) HUMAN GATE: the auditor signs off at the end of outputs/review.md
```

## Design principles: non-negotiable at every step

- **The model reads and judges; Python computes every number.** No agent does arithmetic
  over the data. Figures in prose are `{{$.path}}` placeholders the builders fill.
- **Everything traceable.** Every quote verified word for word against its page; every
  figure from a named script that can be rerun; every rating cites a rule, a metric or a
  past finding; every sampled payment traces to a rule and an approved risk.
- **Indicators, not accusations.** Patterns to investigate and controls to test.
- **Missing or malformed input stops the run.** Nothing is guessed. Figures the documents
  only name (the statutory thresholds) stay null until the auditor supplies them, with a source.
- **Context discipline.** Agents inspect data through `.head()`, `.info()` and aggregates.
  Whole datasets never enter a context window; full lists go to files.
- **Each component owns its files.** Nobody edits a file another component owns, and nobody
  hand-edits a file a builder renders.

## Running it

Python: run the project's scripts with the virtual environment's interpreter
(`.venv/bin/python` on macOS/Linux, `.venv\Scripts\python` on Windows, or `python` with the
venv activated). PDF text: always `python scripts/pdftext.py`, the same poppler engine the
verifiers use.

| Step | Ask Claude Code | Proof it worked |
|---|---|---|
| 1 | `/extract-rules` | `verify_quotes.py` prints ALL CHECKS PASSED |
| 2 | "run the spend-analyst", then "run the findings-analyst" | `python scripts/status.py` |
| 3 | "run the risk-assessor" | `build_register.py` reports no failures |
| 4 | *(you)* decide every risk in `outputs/auditor-comments.md`; then "run the risk-assessor again" | `build_pack.py --gate` passes |
| 5 | "run the agent team for the audit planning pack" | `scripts/checks/run_checks.py`: 4/4 |
| 6 | *(you)* complete the sign-off block at the end of `outputs/review.md` | |

## How the lead runs the team

<!--
TODO (YOU) #7: write the procedure THIS session (the team lead) follows when asked to run
the agent team. Also enable agent teams in .claude/settings.json (SPEC.md §12).
Requirements: SPEC.md §12 and contract/team-protocol.md. It must cover, in order:
  1. the gate check before anyone is spawned, and what to do when it fails;
  2. spawning the three teammates by name from .claude/agents/, each told the other two
     names and that the gate is closed; who starts at once and who waits;
  3. what the lead does while the team runs (answers questions; relays nothing it was not asked);
  4. when to shut the teammates down (all three DONE messages);
  5. the report to the human: under 300 words, what it contains, and that BLOCKED goes
     back to the team, never to the auditor.
Delete this comment when the section is written.
-->

TODO (YOU) #7: the lead's procedure goes here.
