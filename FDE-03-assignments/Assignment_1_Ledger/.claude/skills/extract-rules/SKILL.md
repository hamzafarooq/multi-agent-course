---
name: extract-rules
description: TODO (YOU) #1. One or two sentences. Claude Code reads this line to decide when the skill applies, so say what it turns into what.
---

<!--
TODO (YOU) #1: write the extract-rules skill. Delete this comment block when you are done.

WHY IT EXISTS
Everything downstream stands on this file. The spend-analyst takes its thresholds from
rules.json, the risk-assessor cites rules by rule_id, the planner ties every control to a
rule, and QA checks every quote against the PDF. A missed rule is a hole in the audit; an
invented one sends fieldwork after a control that does not exist; a paraphrased "quote"
fails verification. This is a SKILL, not an agent: it is a procedure the human invokes
(/extract-rules) and watches, in the main session.

YOUR SKILL MUST PIN DOWN (requirements: SPEC.md §6; shape: contract/rules.schema.json)
  1. Preconditions, and what to do when one fails (stop and say what is missing).
  2. How to get the text: python scripts/pdftext.py, plain for quotes, --layout for
     reading the appendix tables. Why the plain text is the source of truth for quotes.
  3. How to walk the document so that EVERY clause and table row ends up in exactly one
     of `rules` or `excluded`.
  4. What makes a clause testable, and what is excluded (with a one-line reason each).
     This is where your recall and precision are won or lost.
  5. Each field of a rule, including thresholds as printed, inclusivity, and named
     external figures as `parameters` with value null (never from memory).
  6. How to copy a verbatim quote, and what never to change in it.
  7. The verify-and-fix loop: run verify_quotes.py until ALL CHECKS PASSED. Never loosen a
     quote to make it pass.
  8. What the final message to the human contains, including three quotes to spot-check.
  9. What is NOT this skill's job.

DONE WHEN
  - python .claude/skills/extract-rules/verify_quotes.py outputs/rules.json data/contract-rules.pdf
    prints ALL CHECKS PASSED
  - python eval/skill/run_eval.py --runs 3 scores found >= 90%, not invented >= 90%,
    fields right >= 85% in the weakest run (benchmark/sla.json)
-->

# extract-rules

TODO (YOU) #1: the procedure goes here.
