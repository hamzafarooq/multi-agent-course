---
name: spend-analyst
description: TODO (YOU) #2. When should the main session delegate to this agent? Say what it reads, what it writes, and what must exist first.
tools: TODO (YOU) #2. Comma-separated, least privilege. This agent writes and runs Python; which tools does that need, and which does it NOT need?
memory: project
---

<!--
TODO (YOU) #2: write the spend-analyst's brief. Delete this comment block when you are done.

WHY IT IS A SUB-AGENT
~10,600 payments across three workbooks. The work is long, mechanical, and would flood the
main session's context; it runs in its own context and hands back a summary and FILES.
The rule that makes this agent trustworthy: the model writes and runs Python; it never
computes, estimates or rounds a number itself. Every figure it reports is read from a
script's output.

YOUR BRIEF MUST PIN DOWN (requirements: SPEC.md §7; shapes: contract/analytics.schema.json
and contract/files.md "analytics-full")
  1. Inputs and the data quirks that will bite (header row moves between workbooks,
     "Redacted" suppliers, date formats, the packed supplier field in contracts.csv,
     what a missing contract notice does and does NOT mean).
  2. Non-negotiables: no arithmetic by the model; context discipline (.head(), aggregates,
     never a full table in the terminal); thresholds ONLY from rules.json; stop and report
     on malformed input; indicator language; a row_id on every flagged row.
  3. The scripts it writes (scripts/clean.py, scripts/analyse.py, scripts/selfcheck.py)
     and what each produces.
  4. Cleaning: exclusions (logged, reversible), tagging, supplier normalisation.
  5. The six tests, parameterised from rules.json, and what to do when a parameter is null.
  6. selfcheck.json: one flagged item per test re-derived independently.
  7. The report back: short, figures quoted from the files, no tables pasted.
  8. Memory: how-to lessons only, never figures or findings (SPEC.md §19).

DONE WHEN
  - python scripts/status.py shows analytics.json valid against its schema
  - outputs/analytics-full/spend-clean.csv has the columns contract/files.md requires
  - selfcheck.json covers every test that ran, all passing
-->

# spend-analyst

TODO (YOU) #2: the brief goes here.
