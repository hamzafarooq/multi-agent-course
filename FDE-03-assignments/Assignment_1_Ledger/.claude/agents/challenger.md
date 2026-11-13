---
name: challenger
description: TODO (YOU) #10. Agent-team member. Say what it reviews, what it writes, and who acts on its challenges.
tools: TODO (YOU) #10. Comma-separated, least privilege. It reads summaries and writes one Markdown file. It must not run commands or read raw data, and the grader checks its transcript for both.
memory: project
---

<!--
TODO (YOU) #10: write the challenger's brief. Delete this comment block when you are done.

WHY IT EXISTS
A plan written by one agent and checked by nobody drifts toward what was easy to plan.
The challenger's job is to find where the plan is weaker than the evidence and make the
planner answer for it, citing evidence every time. It never fixes anything itself.
Its tool list IS part of its design: an agent that may only read summaries cannot
"go and look at the data" and start re-doing the analysis.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §15; formats: contract/files.md
"challenges.md" and contract/team-protocol.md)
  1. What it reads (summaries and the pack) and what it NEVER reads (data/, analytics-full/).
  2. The six challenge types, which ones the planner can act on and which go to the auditor.
  3. No citation, no challenge.
  4. The protocol: wait for PACK READY v1; CHALLENGE #n messages, at most eight in round one
     and four in round two; verify each accepted change in the next PACK READY; close
     every row (resolved / declined / for the auditor); CHALLENGER DONE.
  5. The challenges.md file: heading, versions, date, how it read the pack, the table,
     "For the auditor at sign-off".
  6. Indicator language: it challenges the plan, never the council.
  7. Memory: how-to lessons only (SPEC.md §19).

DONE WHEN
  - challenges.md has no open row, every Evidence cell cites something
  - the teamwork checks in eval/team/run_eval.py pass for this teammate
-->

# challenger

TODO (YOU) #10: the brief goes here.
