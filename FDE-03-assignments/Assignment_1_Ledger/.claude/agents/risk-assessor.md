---
name: risk-assessor
description: TODO (YOU) #5. When should the main session delegate to this agent? Include the re-run after the auditor has recorded decisions.
tools: TODO (YOU) #5. Comma-separated, least privilege. It writes one JSON file and runs the builder.
memory: project
---

<!--
TODO (YOU) #5: write the risk-assessor's brief. Delete this comment block when you are done.

WHY IT IS A SUB-AGENT, AND WHY THE METHOD IS A SKILL
The agent is the JOB (merge three summaries into a register the auditor can decide on);
the risk-assessment skill (TODO #4) is the METHOD. Keep them apart: the brief says "load
the skill and follow it" and adds only what the skill leaves to the agent. It runs twice:
once to open the gate, once after your decisions to apply them, and nothing else.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §10)
  1. Load .claude/skills/risk-assessment/SKILL.md first and follow it exactly.
  2. Files: it writes outputs/risk-ratings.json ONLY. build_register.py writes the
     register and the decision template; nobody edits those by hand.
  3. Stop and report when an input is missing; read summaries, never data/ or analytics-full/.
  4. The re-run: read auditor-comments.md, apply every decision, change nothing else,
     mark the revision.
  5. The report back that asks the auditor to decide (the gate).
  6. Memory: how-to lessons only (SPEC.md §19).

DONE WHEN
  - build_register.py reports no failures; after your decisions the register is a revision
  - python .claude/skills/audit-program/build_pack.py --gate passes
-->

# risk-assessor

TODO (YOU) #5: the brief goes here.
