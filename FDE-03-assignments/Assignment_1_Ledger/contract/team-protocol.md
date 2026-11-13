# The agent team's message protocol

Three teammates (planner, challenger, qa-reviewer) and the lead (your main Claude Code
session) coordinate by **messages**, not by the lead relaying. These message prefixes are
part of the contract: `eval/team/run_eval.py` reads them from the run transcripts to score
teamwork. A message that does not start with its prefix is a message the grader cannot see.

| From → to | Message | When |
|---|---|---|
| planner → challenger, qa-reviewer | `PACK READY v<N>` + the builder's summary line (`controls: …; tests: …; sampled transactions: …; rules cited: a/b`) | Each time `build_pack.py` reports no failures. v1, v2, … |
| challenger → planner | `CHALLENGE #<n> [<type>] R-xx: <one sentence>. Evidence: <citations>. Ask: <the specific change>.` | Round one: at most eight. Round two: at most four. |
| planner → challenger | `RESPONSE #<n>: accepted` (what changed, then a new PACK READY), `RESPONSE #<n>: declined` (the reason), or `RESPONSE #<n>: for the auditor` (rating and scope are the auditor's) | One per challenge. You may decline; you may not ignore. |
| qa-reviewer → planner | `QA v<N>: FAIL <check>: <items, at most ten>` | Any check failing on that pack version |
| qa-reviewer → lead | `QA BLOCKED ON INPUT: <what>` | A failure in a file the planner does not own |
| planner → lead | `PLANNER DONE v<N>` + five lines: risks, controls, tests, sampled transactions, open points | After responding to round two |
| challenger → lead | `CHALLENGER DONE` + counts by status and the *for the auditor* rows | Every row closed |
| qa-reviewer → lead | `QA DONE: READY FOR SIGN-OFF` or `QA DONE: BLOCKED` + failing checks | After writing `review.md` |
| any → lead | `<NAME> BLOCKED` + the reason | Gate not closed, input missing |

## File ownership (checked from the transcripts)

| Teammate | Writes only | Never reads |
|---|---|---|
| planner | `outputs/audit-plan.json` (the builder writes the rest of the pack) | |
| challenger | `outputs/challenges.md` | `data/`, `outputs/analytics-full/`: the summaries are its evidence |
| qa-reviewer | `outputs/review.md` | |

Each may also write its own `.claude/agent-memory/<name>/`. Anything else is a failure
of the *each teammate wrote only the files it owns* check.

## Ordering rules

1. The lead checks the gate (`build_pack.py --gate`) **before** spawning anyone.
2. The challenger and the qa-reviewer wait for `PACK READY v1`.
3. The qa-reviewer writes the final `review.md` only after `CHALLENGER DONE` and
   `PLANNER DONE`, because the trace check reads `challenges.md`.
4. The lead shuts the three down after all three `… DONE` messages. Its report to you is
   under 300 words. `BLOCKED` goes back to the team, never to the auditor.
