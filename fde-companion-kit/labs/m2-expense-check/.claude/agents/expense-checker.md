---
name: expense-checker
description: TODO (you). When should Claude hand work to this agent? Say what it reads, what it writes, and what must exist first.
tools: TODO (you). Comma-separated. Give it only what it needs. It writes and runs Python; does it need the web?
model: sonnet
---

<!--
TODO (you), build 2: write the brief. Delete this comment when you are done.

Your brief must say:
  1. Its inputs, and that it never edits them.
  2. The rule that makes it trustworthy: it writes and runs Python; it never does maths in its head.
  3. Thresholds come only from outputs/rules.json.
  4. The tricky bits: per person and per night, "over" vs "or more", the cities with a higher
     hotel limit, an exception that overrides a general rule, a figure the policy doesn't give.
  5. What it writes: outputs/flags.csv with claim_id, clause, rule_id, why.
  6. What it reports back: short, figures from the script, no pasted tables.

DONE WHEN
  python3 tools/check_flags.py prints PASS.
-->

# expense-checker

TODO (you): the brief goes here.
