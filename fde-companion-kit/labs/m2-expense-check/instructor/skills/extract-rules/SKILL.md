---
name: extract-rules
description: Turns the expense policy (policy.md) into outputs/rules.json, one rule per testable clause with a word-for-word quote, thresholds, approver and action, and every other clause excluded with a reason. Use when asked to extract, list or turn the policy's rules into data.
---

# extract-rules

Read `policy.md` and write `outputs/rules.json` in the shape `schema.json` shows. Every numbered
clause (1.1, 1.2, ...) ends up in exactly one place: `rules` or `excluded`.

## Before you start

- `policy.md` and `schema.json` must exist. If either is missing, stop and say which.
- Read `policy.md` in full, and `schema.json`'s `_fields` notes.

## Rule or excluded?

A clause is a **rule** when a single expense claim could break it: it says what must, must not,
may only or may up to happen, and you could check a claim against it. A limit, a required
receipt, a required approval, a deadline, a ban on a category: all rules.

A clause is **excluded** when no claim can break it. Give a one-line reason. Typical cases:
- background (what the policy is for, which version it replaces),
- definitions,
- principles with nothing you could measure ("spend carefully"),
- how the company runs (when claims are paid, what Finance may ask),
- advice or encouragement ("encouraged to", "should try to") with no requirement,
- consequences of breaking the policy.

When a clause sets a requirement for some claims and nothing else, it is a rule.

## The fields of a rule

- `rule_id`: R01, R02, ... in policy order.
- `clause`: the clause number as printed.
- `quote`: the clause text copied **word for word** from `policy.md`. Copy, never retype:
  keep the $ signs, the capitals and the punctuation. Never shorten, fix or reword a quote.
- `applies_to`: which claims, in a few words (any claim, client meals, hotels).
- `threshold_low`: the amount a claim must be over (or reach) for the rule to apply, as a number.
  "over $75" gives 75; "$25 or more" gives 25; "longer than 6 hours" gives 6.
- `threshold_high`: the most that is allowed, as a number. "up to $60" gives 60;
  "within 30 days" gives 30.
- `inclusive`: true for "or more", "up to", "within"; false for "over", "longer than";
  null when there is no threshold.
- `unit`: USD, USD per person, USD per night, days or hours.
- When a clause has two limits (one for most cities, one for named cities), write one rule per
  limit, both with the same clause and the same full quote.
- `approver`: the role named as approving or pre-approving (manager, director, vice president),
  else null.
- `action`: what someone must do, in a few plain words, using the policy's own key word:
  "attach a receipt", "get approval from a director", "get pre-approval from a vice president",
  "list every attendee and their company", "submit within 30 days", "pay at the per-diem rate".
  For a ban, say what is not allowed ("do not claim fines").
- `parameters`: a figure the policy names but does not give, such as a rate "published by
  Finance", as `{"per_diem_rate": null}`. Never fill one in from memory. Otherwise `{}`.

## Check, then fix

Run `python3 tools/verify_quotes.py`. It checks every quote against the policy and that every
clause is in exactly one place. Fix each problem it names and run it again until it prints
ALL CHECKS PASSED. Fix a failing quote by copying the clause again, never by loosening it.

## What you report

A short message: how many rules and how many excluded, one line per excluded clause with its
reason, the verifier's result, and three quotes for the human to spot-check against the policy.

## Not this skill's job

Checking claims. That is the expense-checker's job. Do not open `claims.csv`.
