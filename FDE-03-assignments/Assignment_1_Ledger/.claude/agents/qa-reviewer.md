---
name: qa-reviewer
description: TODO (YOU) #11. Agent-team member. Say what it runs, what it writes, and that it blocks sign-off until every check passes.
tools: TODO (YOU) #11. Comma-separated, least privilege. It runs the check scripts and writes one Markdown file.
memory: project
---

<!--
TODO (YOU) #11: write the qa-reviewer's brief. Delete this comment block when you are done.

WHY IT EXISTS
The checks are the judge; this teammate is the bailiff. It decides nothing about the
audit. It runs scripts/checks/run_checks.py (quotes, numbers, trace = your TODO #12,
samples), reports exactly what the scripts say, sends failures to the planner, and
blocks sign-off until all four pass. A QA agent that "reads the files and agrees they
look fine" is the failure this design exists to prevent.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §16; formats: contract/files.md "review.md"
and contract/team-protocol.md)
  1. The scripts are the check: never re-derive a result by reading files, never soften a FAIL.
  2. Files: writes outputs/review.md ONLY; never the pack, the plan, the challenges, the checks.
  3. The protocol: wait for PACK READY v1; QA vN: FAIL <check>: <items> to the planner;
     QA BLOCKED ON INPUT to the lead; re-run on every PACK READY; write the final review only
     after CHALLENGER DONE and PLANNER DONE; QA DONE: READY FOR SIGN-OFF or BLOCKED.
  4. review.md: version, date, the results table exactly as printed, failures, verdict,
     run history, and the empty Auditor sign-off block.
  5. Memory: how-to lessons only (SPEC.md §19).

DONE WHEN
  - review.md's results table matches a fresh run of run_checks.py word for word
-->

# qa-reviewer

TODO (YOU) #11: the brief goes here.
