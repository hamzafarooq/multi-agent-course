---
name: audit-program
description: TODO (YOU) #8. One or two sentences: what the method turns into what, and who loads it (the planner teammate).
---

<!--
TODO (YOU) #8: write the audit-program skill (the METHOD the planner follows).
Delete this comment block when you are done.

WHY IT EXISTS
The pack is what an auditor carries into fieldwork: for each approved risk, the control the
Rules require, the test that shows whether it worked, and the specific payments to pull.
The planner JUDGES (which control, which test, which recipe). build_pack.py (provided, in
this folder) checks the gate, draws every sample from the recipe, verifies every payment
exists, checks every rule is accounted for, and renders the three documents. The planner
never types a row ID, a supplier name or a figure.

YOUR SKILL MUST PIN DOWN (requirements: SPEC.md §13; shape: contract/audit-plan.schema.json,
sample sources: contract/files.md)
  1. The gate check first (build_pack.py --gate), and planning EXACTLY the approved,
     in-scope risks.
  2. Per risk: the expected control (cites a rule; names the owner where the Rules do),
     the test step (what to obtain, compare, and what a pass looks like), the evidence.
  3. Sample recipes, not lists: kinds (rows, groups, suppliers, none), filters, order,
     size by score, exclude_drawn_in so two tests do not pull the same payments.
     How to look at an analytics-full file without loading it (head -3).
  4. The request (PBC) list for each test.
  5. Accounting for every rule: cited, or in rules_not_tested with an honest reason.
  6. Memo text with {{$.path}} placeholders; no literal figures.
  7. The build-and-fix loop; never editing a rendered file.
  8. What is NOT this skill's job (rating, scope, challenging, QA).

DONE WHEN
  - python .claude/skills/audit-program/build_pack.py reports no failures
  - python scripts/checks/run_checks.py passes numbers, samples (and quotes, trace)
-->

# audit-program

TODO (YOU) #8: the method goes here.
