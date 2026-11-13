---
name: planner
description: TODO (YOU) #9. Agent-team member. Say what it owns, what it builds from, and that it answers the challenger and the qa-reviewer.
tools: TODO (YOU) #9. Comma-separated, least privilege. It writes audit-plan.json and runs the builder.
memory: project
---

<!--
TODO (YOU) #9: write the planner's brief. Delete this comment block when you are done.

WHY IT IS A TEAMMATE, NOT A SUB-AGENT
A sub-agent reports to the main session and stops. A teammate stays alive and talks to
the other teammates directly: the challenger argues with it, the qa-reviewer sends it
failures, it rebuilds and re-announces. That conversation is the point of the agent team.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §14; protocol: contract/team-protocol.md)
  1. Its method is the audit-program skill (TODO #8): load it first, follow it exactly.
  2. File ownership: writes outputs/audit-plan.json ONLY; the builder renders the pack;
     never challenges.md or review.md, never the register or the inputs.
  3. The protocol: PACK READY vN with the builder's summary line; RESPONSE #n accepted /
     declined (with a reason) / for the auditor (rating and scope are the auditor's);
     fixing QA failures in the plan, never in the rendered files or the checks;
     at most two challenge rounds; PLANNER DONE vN; PLANNER BLOCKED.
  4. Context discipline: analytics-full files with head -3 only.
  5. Memory: how-to lessons only (SPEC.md §19).

DONE WHEN
  - build_pack.py reports no failures on the final version
  - every CHALLENGE #n has a RESPONSE #n, and the transcript shows PLANNER DONE
-->

# planner

TODO (YOU) #9: the brief goes here.
