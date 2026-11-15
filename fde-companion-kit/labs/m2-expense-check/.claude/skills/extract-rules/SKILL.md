---
name: extract-rules
description: TODO (you). One or two sentences. Claude reads this line to decide when the skill applies, so say what it turns into what, and when to use it.
---

<!--
TODO (you), build 1: write the procedure. Delete this comment when you are done.

Your skill must say:
  1. What must exist before it starts, and what to do if it doesn't (stop and say what is missing).
  2. How to decide whether a clause is a rule (a claim could break it) or excluded (with a reason).
  3. Each field of a rule (schema.json), including thresholds as printed, "over" vs "or more",
     and figures the policy names but does not give (parameters with value null, never from memory).
  4. How to copy a quote word for word, and that a quote is never reworded to pass.
  5. The check-and-fix loop: run python3 tools/verify_quotes.py until ALL CHECKS PASSED.
  6. What the final message to you contains.
  7. What is NOT this skill's job.

DONE WHEN
  python3 tools/verify_quotes.py prints ALL CHECKS PASSED, and
  python3 tools/run_eval.py --runs 3 meets 90 / 90 / 85 in the weakest run.
-->

# extract-rules

TODO (you): the procedure goes here.
