---
name: risk-assessment
description: TODO (YOU) #4. One or two sentences: what the method turns into what, and who loads it (the risk-assessor).
---

<!--
TODO (YOU) #4: write the risk-assessment skill (the METHOD the risk-assessor follows).
Delete this comment block when you are done.

WHY IT EXISTS
Two auditors rating the same evidence should get the same register. The method (the
scale, the likelihood rubric, the citation rule, the repeat-finding uplift) lives here,
in a skill, so it is versioned, loadable by any agent, and separate from the agent's job
description. The model JUDGES and CITES; build_register.py (provided, in this folder)
resolves every citation, fills every figure, computes every score and renders the register.

YOUR SKILL MUST PIN DOWN (requirements: SPEC.md §9; shape: contract/risk-ratings.schema.json)
  1. Inputs (rules.json, analytics.json, history.json) and outputs (risk-ratings.json, which
     the agent writes; risk-register.md and auditor-comments.md, which ONLY the builder writes).
  2. The citation rule: every likelihood and impact justification cites at least one
     [rule:..], [metric:$.path] or [history:..]; what the builder does to a risk without one.
  3. Placeholders: no figure from the data is ever typed; {{$.path}} instead.
  4. The scale: the council's own (history.json scoring_method) when usable, else the
     fallback, stated in the header.
  5. A likelihood rubric precise enough that two runs agree. Impact: which column, why.
  6. The repeat-finding uplift (+1 for an adverse prior opinion on the theme), stated.
  7. Which themes to consider, and how to handle a theme the data cannot see.
  8. Indicator language: no supplier, officer or service in a risk statement.
  9. The re-run after the gate: the `revision` block, `auditor_override`, rejected risks
     moved to `excluded`, and changing NOTHING the auditor did not ask for.
 10. The build-and-fix loop, and the report to the human that opens the gate.

DONE WHEN
  - python .claude/skills/risk-assessment/build_register.py outputs/risk-ratings.json
    reports no failures, and outputs/risk-register.md is exactly what it rendered
-->

# risk-assessment

TODO (YOU) #4: the method goes here.
