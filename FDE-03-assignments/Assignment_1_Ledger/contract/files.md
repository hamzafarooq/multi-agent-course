# The file contract

The pipeline's components never call each other. They hand over **files**. This page
fixes the shape of every file that is not a JSON Schema in this folder. The provided
builders, checks and grader read exactly these shapes. If yours differ, they fail
loudly, and the failure names the file.

| File | Written by | Read by | Shape |
|---|---|---|---|
| `outputs/rules.json` | extract-rules skill | everyone | [`rules.schema.json`](rules.schema.json) |
| `outputs/analytics.json` | spend-analyst's scripts | risk-assessor, planner, challenger, QA numbers check | [`analytics.schema.json`](analytics.schema.json) |
| `outputs/analytics-full/*` | spend-analyst's scripts | `build_pack.py` (samples), QA samples check | [below](#outputsanalytics-full) |
| `outputs/history.json` | findings-analyst | risk-assessor, challenger | [`history.schema.json`](history.schema.json) |
| `outputs/risk-ratings.json` | risk-assessor | `build_register.py`, planner, QA trace check | [`risk-ratings.schema.json`](risk-ratings.schema.json) |
| `outputs/risk-register.md`, `outputs/auditor-comments.md` | `build_register.py` (never by hand) | the auditor, planner, QA trace check | [below](#the-register-and-the-decisions) |
| `outputs/audit-plan.json` | planner | `build_pack.py`, challenger, QA | [`audit-plan.schema.json`](audit-plan.schema.json) |
| `outputs/planning-memo.md`, `risk-control-matrix.md`, `audit-program.md`, `samples/T-*.csv`, `pack-figures.json` | `build_pack.py` (never by hand) | challenger, QA, the auditor | [below](#the-pack) |
| `outputs/challenges.md` | challenger | planner, QA trace check | [below](#outputschallengesmd) |
| `outputs/review.md` | qa-reviewer | the auditor (signs it) | [below](#outputsreviewmd) |

## `outputs/analytics-full/`

Full lists, too big for any context window. Agents look at them with `head -3` only.
Every payment row carries a `row_id` of the form `<workbook file name>:<sheet row>`, for
example `Over500_2026_P04_-_published.xlsx:2239`. That is the row number you see in
Excel, so an auditor can open the workbook and find the payment.

**Required by the provided tools.** These names and columns are load-bearing:

| File | Required columns | Why |
|---|---|---|
| `spend-clean.csv` | `row_id`, `source_file`, `sheet_row`, `pay_date`, `Service`, `Narrative`, `Net amount`, `Supplier name`, `supplier_norm`, `tag` | `build_pack.py` verifies every sampled payment here; the samples check and the golden thread start here |
| `selfcheck.json` | a JSON **list**, one object per test: `{"test": "<test name>", "pass": true, "row_id": "...", ...}` | the eval counts how many tests a flagged item was independently re-derived for |
| `cleaning-log.json` | free-form object: per workbook the header row found, rows, £, date range; exclusions; notice filtering | evidence for the spend-analyst's judge |

**Sample sources.** These are the files the planner's sample recipes point at. Any file
works as a `source` if it has the columns the recipe uses. These are the ones the
reference build produced, and every one carries `supplier_norm`:

| File | Kind | Key columns |
|---|---|---|
| `threshold-clustering.csv` | `rows` | `row_id`, `threshold`, `Net amount`, `tag`, plus the spend-clean columns |
| `split-purchases-windows.csv` | `groups` | `window_id`, `threshold`, `window_total`, `n_payments`, `dominant_tag`, `row_ids` (`;`-separated) |
| `split-purchases-rows.csv` | `rows` | `window_id`, `row_id`, `threshold` |
| `duplicates-groups.csv` | `groups` | `group_id`, `tier` (`same_timestamp` / `different_time`), `amount`, `tag`, `row_ids` |
| `duplicates-rows.csv` | `rows` | `group_id`, `tier`, `row_id` |
| `high-value-suppliers.csv` | `suppliers` | `total_gbp`, `annualised_estimate`, `dominant_tag`, `match_class` |
| `expired-notice-spend.csv` | `suppliers` | `annualised_estimate`, `latest_end_date`, `notice_ids` |
| `spend-vs-award.csv` | `suppliers` | `ratio`, `annualised_estimate`, `award_annual_rate` |

## The register and the decisions

Both are rendered by `build_register.py`. Never edit `risk-register.md`. The auditor
edits `auditor-comments.md` in exactly two places: the **Decision** and **Comment**
cells, and the `Reviewer:` / `Date:` lines.

- `risk-register.md` has a `## Summary` table:
  `| ID | Risk | L | I | Score | Matrix label | Band | CRR rule | Recommend in scope |`
- `auditor-comments.md` has a `## Decisions` table:
  `| ID | Risk | Now | Scope now | Decision | Comment |`. The Decision is one of
  `approve`, `amend` or `reject`. An amend or reject needs a Comment saying what and why.

The gate is closed when every risk has a decision and the register has been rebuilt as a
**revision** that applied them. `build_pack.py --gate` is the test.

## The pack

All of it is rendered by `build_pack.py` from `audit-plan.json`. Never edit it by hand.

- `risk-control-matrix.md`: one row per control, starting `| R-xx: <title> |`.
- `audit-program.md`: one section per planned risk, headed `## R-xx: <title> [...]`, ending with the PBC (request) list.
- `planning-memo.md`: sections `## Purpose`, `## Background`, `## Scope` (with a
  `**Not in scope**` list of `- R-xx: <title>: <reason>`), `## Approach`,
  `## Rules coverage`, `## Limitations`, `## Review and sign-off`.
- `samples/T-<risk>.<n>.csv` has the columns
  `test,item,group,row_id,source_file,sheet_row,pay_date,supplier,amount,service,narrative`.
- `pack-figures.json` holds `{"generated_at": "...", "figures": {...}}`. It lists every figure the builder computed, so the QA number check can trace each figure in the memo.

## `outputs/challenges.md`

A heading; the pack versions reviewed; the date; one paragraph on how the pack was read.
Then one table, one row per challenge:

```
| # | Type | Risk | Challenge | Evidence | Ask | Response | Status |
```

- **Type** is one of `rating`, `scope`, `sample`, `control`, `test`, `coverage`.
- **Evidence** must cite a rule ID, a metric path, a history ID, or a test or control ID.
- **Response** quotes the planner.
- **Status** is `resolved`, `declined` or `for the auditor`. It is never `open`, and never blank, at the end.

The file ends with a "For the auditor at sign-off" list.

## `outputs/review.md`

The pack version checked and the date. The results table exactly as
`scripts/checks/run_checks.py` printed it. Any failures. The verdict, `READY FOR SIGN-OFF`
or `BLOCKED`. The file ends with the auditor's block, which the auditor fills in (TODO #13):

```
## Auditor sign-off

Signed off by:
Date:
Decision (sign off / return to the team):
Comment:
```
