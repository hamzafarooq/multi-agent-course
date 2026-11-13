---
name: findings-analyst
description: TODO (YOU) #3. When should the main session delegate to this agent? Say what it reads, what it writes, and that it records rather than judges.
tools: TODO (YOU) #3. Comma-separated, least privilege. It reads four PDFs and writes one JSON file; does it need to run commands?
memory: project
---

<!--
TODO (YOU) #3: write the findings-analyst's brief. Delete this comment block when you are done.

WHY IT IS A SUB-AGENT
Four committee papers, a few hundred pages of reading, and one job: record what past
audits found and how the council scores risk, each item sourced to a page. It can run in
parallel with the spend-analyst because neither needs the other's output. It RECORDS;
it never scores, rates or resolves a contradiction.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §8; shape: contract/history.schema.json)
  1. The four papers and what each is for (and the one that is NOT public: the Strategic
     Risk Register is exempt; note its absence as a gap).
  2. Extraction: python scripts/pdftext.py, plain text for quotes, --layout to rebuild tables.
  3. What to record: audits and assurance opinions, open or overdue actions, risk themes,
     the council's scoring method (scales, matrix, bands, appetite), gaps, discrepancies.
  4. Every item carries source, pdf_page and a verbatim quote; IDs (AUD-, RT-, D-) that
     the risk-assessor will cite.
  5. Not in the papers means omitted and listed as a gap; never guessed. Contradictions
     are recorded, not resolved. scoring_method.usable is false when it is not usable.
  6. The verify-and-fix loop (scripts/verify_history.py) and the report back.
  7. Memory: how-to lessons only (SPEC.md §19).

DONE WHEN
  - python scripts/verify_history.py outputs/history.json data/committee prints ALL CHECKS PASSED
  - history.json validates against contract/history.schema.json
-->

# findings-analyst

TODO (YOU) #3: the brief goes here.
