# SPEC, Assignment 1: LEDGER (procurement audit planner)

> **This is the exhaustive specification, written to be read by a coding agent.** It is
> deliberately dense: every requirement, file shape, stop condition and failure mode is
> stated once, explicitly, so an agent working from it cannot quietly skip one.
>
> **If you are a human, read [`PRD.md`](PRD.md) first**: the same product, short. Come here
> when you need the exact requirement for a component; each TODO has its own section
> (§6 to §18), and every stub file points at its section.
>
> **No number in here is authoritative.** Bars live in `benchmark/sla.json`,
> `expectations.json` and `eval/rubric.json`; file shapes live in `contract/`. If prose here
> disagrees with them, the JSON wins and this file is stale: say so.

## Contents

§1 What is built · §2 The flow · §3 Design principles · §4 Data · §5 Layout and ownership ·
§6 extract-rules (TODO #1) · §7 spend-analyst (#2) · §8 findings-analyst (#3) ·
§9 risk-assessment (#4) · §10 risk-assessor (#5) · §11 The human gate (#6) ·
§12 The agent team and the lead (#7) · §13 audit-program (#8) · §14 planner (#9) ·
§15 challenger (#10) · §16 qa-reviewer (#11) · §17 check_trace.py (#12) · §18 Sign-off (#13) ·
§19 Agent memory · §20 Evaluation · §21 Deploy and submit · §22 Definition of done

---

## §1 What is built

A Claude Code project that plans, never performs, an internal audit of West Berkshire
Council's procurement from public data. Output: an **audit planning pack**: what to test,
which payments to pull, what to ask the council for, every line traceable to a verified
quote, a computed figure or a past finding, approved by a human before it is planned and
signed off by a human after it is checked.

The student builds the **harness**: three skills, six agent definitions, the team lead's
procedure and the agent-teams setting, one QA check, and the two human decisions. The
deterministic guardrails (verifiers, builders, three QA checks), the data, the contract,
the grader and the viewer are provided.

## §2 The flow

| Step | Component | Kind | Reads | Writes |
|---|---|---|---|---|
| 1 | `extract-rules` | skill, invoked by the human (`/extract-rules`) in the main session | `data/contract-rules.pdf` | `outputs/rules.json` |
| 2a | `spend-analyst` | sub-agent | rules.json, `data/spend/*.xlsx`, `data/contracts.csv` | `scripts/clean.py`, `analyse.py`, `selfcheck.py`; `outputs/analytics.json`, `outputs/analytics-full/` |
| 2b | `findings-analyst` | sub-agent (may run in parallel with 2a) | `data/committee/*.pdf` | `outputs/history.json` |
| 3 | `risk-assessor` following the `risk-assessment` skill | sub-agent + skill | rules, analytics, history | `outputs/risk-ratings.json` → `build_register.py` → `risk-register.md`, `auditor-comments.md` |
| 4 | **human gate** | the student as auditor | the register | Decision and Comment cells in `auditor-comments.md`; then the risk-assessor re-runs (revision) |
| 5 | agent team: `planner` (follows `audit-program`), `challenger`, `qa-reviewer`, led by the main session | teammates | the approved register, summaries, the pack | `audit-plan.json` → `build_pack.py` → pack; `challenges.md`; `review.md` |
| 6 | **human gate** | the student as auditor | `review.md`, `challenges.md` | the sign-off block in `review.md` |

Components never call each other. They hand over files (§5), and inside the team they
exchange messages (`contract/team-protocol.md`).

## §3 Design principles (non-negotiable; each is checked)

1. **The model reads and judges; Python computes every number.** No agent performs, estimates
   or rounds arithmetic over the data. Every figure in prose is a `{{$.json.path}}`
   placeholder that a builder fills from `analytics.json`. A literal figure in register or
   memo prose is a builder warning or failure. *Checked by:* `build_register.py`,
   `build_pack.py`, `check_numbers.py`.
2. **Everything traceable.** Every `verbatim_quote` is found word for word on its stated page
   (`verify_quotes.py`); every history item on its page (`verify_history.py`); every rating
   cites `[rule:ID]`, `[metric:$.path]` or `[history:ID]` that resolves (`build_register.py`);
   every control and test cites a rule (`build_pack.py`); every sampled payment exists at its
   workbook row (`check_samples.py`) and traces to an approved risk (the golden thread, §20).
3. **Indicators, not accusations.** Outputs describe patterns to investigate and controls to
   test. No risk statement, challenge or memo line names a supplier, officer or service as
   doing wrong. Supplier names appear only inside sample lists. A missing contract notice is
   a prompt to check the council's register, never evidence of off-contract spend.
4. **Missing or malformed input stops the run.** Stop and report what is missing; never
   guess, patch or fabricate. Figures the documents only name (the statutory thresholds) are
   `parameters` with `value: null` until the auditor supplies them with a source; tests that
   need them are skipped and recorded.
5. **Context discipline.** Data is inspected with `.head()`, `.info()`, `.describe()`,
   `value_counts().head(20)` and aggregates only. Full datasets and flagged lists never enter
   a context window or a terminal; they go to files. JSON summaries carry counts, totals and
   top-20s. Agents read `analytics-full/` files with `head -3` only.
6. **Ownership.** Each file has one writer (§5). Nobody edits another component's file;
   nobody hand-edits a builder-rendered file; nobody edits `data/`.
7. **PDF text comes from one engine.** Always `python scripts/pdftext.py <pdf> <out> [--layout]`
   (poppler's `pdftotext`, UTF-8). The verifiers use the same engine and refuse Xpdf's
   `pdftotext`, which Git for Windows ships and which Claude Code's Bash tool on Windows
   finds first.

## §4 Data (read-only; details in `data/SOURCES.md`)

| File | Facts the harness must handle |
|---|---|
| `contract-rules.pdf` | About 15 pages. Page footers carry a `.docx` filename and page number: never part of a quote. Appendices A, B and C are tables: read them from the `--layout` text, quote from the plain text. Some bounds are named external figures ("the Threshold"), not numbers. |
| `spend/*.xlsx` | Sheet `Data to publish`. **The header row position varies by workbook**: find the row whose first cell is `Service`. Columns exactly `Service, Expenditure category, Narrative, Date, Net amount, Supplier name`. `Date` is a payment-run timestamp (many rows share it), not an invoice date: use calendar dates for windows. If text, dates are M/D/Y. Population is payments over £500 only, so split and duplicate counts are lower bounds. About a fifth of rows have supplier `Redacted` (many payees): never use them in a supplier-level test. |
| `contracts.csv` | A raw Contracts Finder **notice** export, not a register. Keep rows whose `Organisation Name` is the council (other buyers appear). `Supplier` is packed: `[Name|Address|Ref type|Ref Number|Is SME|Is VCSE][…]`; one (notice, supplier) row per block; the 4th element is a Companies House number when the 3rd is `COMPANIES_HOUSE`. Dates are D/M/Y. `Awarded Value` 0.00 is common (frameworks) and does not mean "no contract". If the file has exactly 1,000 rows or a year looks thin, warn: the export may be capped. Contracts Finder carries only awards above its publication threshold. |
| `committee/*.pdf` | Four papers (see SOURCES.md). The Strategic Risk Register is exempt and absent: record that as a gap. The scoring method comes from the Risk Management Strategy; it may state band thresholds two ways: record the discrepancy, do not resolve it. |

## §5 Layout and ownership

| Path | Owner | Status |
|---|---|---|
| `data/`, `contract/`, `eval/`, `quality/`, `benchmark/`, `viewer/`, `vercel.json`, `expectations.json` | provided | **DO NOT EDIT** (hashed in `eval/integrity.json`) |
| `.claude/skills/*/verify_quotes.py`, `build_register.py`, `build_pack.py`; `scripts/verify_history.py`, `scripts/pdftext.py`, `scripts/status.py`, `scripts/checks/{run_checks,check_quotes,check_numbers,check_samples}.py` | provided | **DO NOT EDIT** |
| `.claude/skills/{extract-rules,risk-assessment,audit-program}/SKILL.md` | student | TODO #1, #4, #8 |
| `.claude/agents/*.md` (six) | student | TODO #2, #3, #5, #9, #10, #11 |
| `.claude/settings.json`, `CLAUDE.md` § "How the lead runs the team" | student | TODO #7 |
| `scripts/checks/check_trace.py` | student | TODO #12 |
| `scripts/clean.py`, `analyse.py`, `selfcheck.py` (and helpers) | written by the spend-analyst at run time | |
| `outputs/rules.json` | extract-rules | |
| `outputs/analytics.json`, `outputs/analytics-full/` | spend-analyst's scripts | |
| `outputs/history.json` | findings-analyst | |
| `outputs/risk-ratings.json` | risk-assessor | |
| `outputs/risk-register.md`, `outputs/auditor-comments.md` | `build_register.py` only; the auditor edits Decision, Comment, Reviewer, Date | |
| `outputs/audit-plan.json` | planner | |
| `outputs/planning-memo.md`, `risk-control-matrix.md`, `audit-program.md`, `samples/`, `pack-figures.json` | `build_pack.py` only | |
| `outputs/challenges.md` | challenger | |
| `outputs/review.md` | qa-reviewer; the auditor fills the sign-off block | |
| `.claude/agent-memory/<agent>/` | that agent | §19 |
| `DESIGN.md`, `trajectories.md`, `live-test.md` | student, in their own words | |
| `design-interview.md` | the eval skill records the student's answers verbatim | |
| `eval/skill/runs/`, `runs/`, `reports/report.json`, `reports/PRODUCT_EVAL.md` | the eval tools | committed for deploy |

## §6 Skill: `extract-rules` (TODO #1)

**Kind:** skill, invoked by the human as `/extract-rules`, runs in the main session.
**Input:** `data/contract-rules.pdf`. **Output:** `outputs/rules.json`, shape
`contract/rules.schema.json`. **Proof:** `verify_quotes.py outputs/rules.json data/contract-rules.pdf`
exits 0 with `ALL CHECKS PASSED`.

1. Preconditions: the PDF exists and is non-empty; `python scripts/pdftext.py --which` finds
   poppler; if `outputs/rules.json` exists, ask before overwriting. Any failure: stop and say how to fix it.
2. Extract the text twice with `scripts/pdftext.py`: plain (the source of truth for quotes; page N
   is the Nth form-feed chunk) and `--layout` (only for reading which table cells belong to which row).
3. Enumerate every numbered clause and every appendix table row. Each ends up in exactly one of
   `rules` or `excluded`. Nothing is skipped.
4. **Testable** means: given a contract or payment and the council's records, an auditor could
   answer yes or no whether it was followed. Types: `threshold` (a monetary band that triggers a
   process), `required-action` (must / shall / no … shall attached to a concrete action or record),
   `approver` (names who must approve or decide), `anti-avoidance` (prohibits splitting or
   structuring to avoid a threshold). **Excluded** (one-line reason each): definitions, purpose,
   scope, legal basis; principles with no concrete action; discretionary wording (should, may)
   unless gated by a named approver; delegations to documents not in the PDF; duplicates of a
   captured rule (`"duplicate of CPR-NN"`, keep the more specific); genuinely unclear
   (`"ambiguous: …"`). Never guess.
5. Fields: `rule_id` `CPR-NN`, zero-padded, sequential in document order (the verifier enforces
   it); `clause` as printed or `App B row B1`; `page` where the quote is; thresholds as printed, as
   GBP integers, inclusivity in the `_inclusive` booleans (`more than £24,999.99` → `25000`,
   inclusive); a named external bound → numeric field `null`, `threshold_*_ref` set to a key
   declared in `parameters`; `required_action` one imperative sentence; `approver` as named or
   null; `evidence_source` the most public source that could test it.
6. `verbatim_quote`: the complete sentence(s) from the plain text, line breaks joined with one
   space, nothing else changed (keep curly quotes, £, asterisks, dashes, typos). Never across a
   page footer. Table rows: quote the obligation cell. At least one sentence; at most the clause.
7. `parameters` values are always `null` at extraction. `notes`: document-level observations
   (contradictions, blanks), each citing clauses.
8. Run the verifier; fix every failure by re-reading the plain text; re-run until clean. Never
   loosen a quote: if it cannot be found, it is wrong.
9. Report: counts by type, excluded count, parameters awaiting the auditor, a compact rule table,
   notes, and three quotes for the human to spot-check against the PDF.
10. Not this skill's job: rating risk, testing data, filling statutory thresholds, editing `data/`.

**Measured by** `eval/skill/run_eval.py` (fresh sessions, against `eval/skill/answer-key.csv`):
found, not invented, fields right, quotes verified, consistency.

## §7 Sub-agent: `spend-analyst` (TODO #2)

**Kind:** sub-agent; writes and runs Python. **Inputs:** rules.json, spend workbooks,
contracts.csv (optional: if absent, the notice-based tests are skipped and recorded).
**Outputs:** `analytics.json` (`contract/analytics.schema.json`) and `analytics-full/`
(`contract/files.md`). **Proof:** schema valid; `selfcheck.json` covers every test that ran.

1. Before writing code, report the thresholds derived from rules.json (value, inclusivity,
   rule_ids, competition-triggering or not), the null parameters, which inputs exist, and which
   tests will run, run degraded, or be skipped.
2. **Thresholds come only from rules.json**: every distinct numeric `threshold_low/high` of rules
   typed `threshold`, `approver` or `anti-avoidance`. A threshold is competition-triggering when
   its rule's required action involves quotes or tenders. Never type a threshold into a script.
3. `scripts/clean.py` → `spend-clean.csv`, `spend-excluded.csv`, `notices-clean.csv`,
   `cleaning-log.json`. Locate the header row; assert the six columns exactly; add `source_file`,
   `sheet_row`, `row_id` (`<file>:<sheet row>`), `pay_date`; assert no null date, amount or
   supplier and stop on any. Normalise supplier names with ONE function used on both sides
   (uppercase; `&`→AND; drop bracketed qualifiers and `T/A …`; keep A–Z 0–9 and spaces; drop
   LTD LIMITED PLC LLP LLC INC CIC CIO UK THE; collapse spaces) into `supplier_norm`, keeping
   `Supplier name` exactly as published. Exclusions (each: rows, £, reason; kept in
   `spend-excluded.csv`): redacted supplier; pension/statutory (`LGPS|PENSION|SUPERANNUATION`);
   inter-authority payees. Do not exclude grants or transfer payments: tag them. One `tag` per
   row, first match wins: `care_or_education_placement`, `grant`, `agency_staff`,
   `premises_non_procurement`, `general_procurement`. Parse contracts.csv per §4; keep the set
   active in the spend window (end date on or after the window start, or blank).
4. `scripts/analyse.py`, every test writing a CSV to `analytics-full/` and a block to
   `analytics.json` with `parameters`, `rule_ids`, counts, £ totals and a top 20 carrying
   `row_id`s. `annualised estimate = total × 12 / months_covered`, labelled as such everywhere.
   1. `threshold_clustering`: per threshold T, payments in `[0.9T, T)` (respecting inclusivity),
      with the comparator band `[T, 1.1T)`, the wider baseline, supplier concentration and the tag split.
   2. `split_purchases`: per competition-triggering T, same `supplier_norm`, two or more payments
      in a 30-day window, every payment below T, window total at or above T; de-duplicate
      overlapping windows; headline `general_procurement`, placements reported separately.
   3. `high_value_suppliers`: suppliers whose annualised estimate is at or above the lowest
      competition-triggering threshold, classed by dominant tag; this is the population for the
      contract-evidence request.
   4. `off_contract` (needs contracts.csv): match class per high-value supplier (exact; near by
      `difflib` ratio ≥ 0.85 or distinctive-token containment, reported as candidates, never
      counted as matches; none), only for suppliers above the publication threshold, with the
      caveat of §3.3 verbatim.
   5. `duplicates`: same supplier, same amount to the penny, within 7 days; tiers
      `same_timestamp` and `different_time`.
   6. `expired_notice_spend` (needs contracts.csv): exact-matched suppliers whose every notice
      ended before the window; cites the extension rule.
   7. `spend_vs_award` (needs contracts.csv): exact match to one live single-supplier notice with
      award > 0; ratio of annualised estimate to annual award rate; flag ≥ 1.25; cites the variation rule.
   A test that cannot run is written as `{"skipped": true, "reason": …}` and listed in `skipped`.
5. `scripts/selfcheck.py` → `selfcheck.json`: for one flagged item per test, re-derive it
   independently from `spend-clean.csv` and record `{"test", "pass", "row_id", …}`.
6. Report in under 450 words: population and exclusions, per test the headline count and £
   quoted from analytics.json, skipped tests and why, the self-check row_ids, data-quality
   warnings. No pasted tables.
7. Tools: it needs to run Python and write files. It needs nothing that talks to the network.

## §8 Sub-agent: `findings-analyst` (TODO #3)

**Kind:** sub-agent. **Inputs:** `data/committee/*.pdf`. **Output:** `history.json`
(`contract/history.schema.json`). **Proof:** `verify_history.py outputs/history.json data/committee`
prints ALL CHECKS PASSED.

1. Text via `scripts/pdftext.py` (plain for quotes; `--layout` to rebuild tables).
2. Record, each item with `source` (file name), integer `pdf_page` and a verbatim `quote`:
   audits recently completed with their assurance opinion and implementation opinion
   (`AUD-NN`), their procurement relevance and why; open or overdue agreed actions; planned
   audits; the audit approach; risk themes (`RT-NN`); the council's scoring method
   (likelihood and impact scales, the matrix as `combination.matrix_cells`, bands, any
   corporate-register threshold) with `usable: true`, or `usable: false` and why; gaps (what
   the plan would need and the papers do not hold; at least the absent Strategic Risk
   Register); discrepancies (`D-NN`), recorded not resolved.
3. It records; it never scores, rates or infers. Not in the papers → omitted and, if it matters,
   listed as a gap. No knowledge from outside the four papers.
4. Verify and fix until clean. Report counts per section, the scoring method's status, gaps and
   discrepancies.

## §9 Skill: `risk-assessment` (TODO #4)

**Kind:** skill (a method), loaded by the risk-assessor. **Writes (via the agent):**
`risk-ratings.json` (`contract/risk-ratings.schema.json`). **Proof:** `build_register.py
outputs/risk-ratings.json` reports `failures: 0`.

1. Every likelihood and impact justification cites at least one resolvable `[rule:CPR-NN]`,
   `[metric:$.path]` (a scalar in analytics.json) or `[history:ID]` (AUD-, RT-, D-, a gap's
   `item`, or `scoring_method`). Without one, the builder drops the risk. Never weaken a citation to make it resolve.
2. No figure from the data is typed: `{{$.path}}` placeholders only. Scores (1 to 5), rule IDs
   and history IDs are the only digits the model writes.
3. Scale: the council's (`history.json → scoring_method`) when `usable`; otherwise 1–5 Very low…Very
   high, score L×I, stated in the header (`scale.source: "fallback"`).
4. A likelihood rubric that makes two runs agree (e.g. 1 no indicator and recent substantial
   assurance … 5 only when the data shows the pattern occurring and history is adverse). Impact:
   the council's impact table applied to the plausible consequence; name the driving column.
5. Repeat finding: likelihood +1 when a cited history item records Limited, Weak or
   Unsatisfactory; stated with the history ID. The builder verifies the opinion is adverse.
6. Themes to consider at least: quotes and tenders at the thresholds; splitting; high-value
   suppliers without evidence of a compliant award; contracts past expiry; spend over award;
   duplicate payments; care and education placements and their exemption; waivers and
   exceptions; Key Decision and delegated-authority approvals at the higher bands; grants. A
   theme the data cannot see may still be a risk on a rule alone, and must say so.
7. Indicator language; no supplier, officer or service in a statement.
8. After the gate: a `revision` block listing every amend and reject applied (number rising by
   one each revision); `auditor_override: true` on amended scores, quoting the decision and
   keeping a real citation; rejected risks moved to `excluded` with the auditor's reason;
   nothing changed that the auditor did not ask for. The builder checks all of this.
9. Report under 400 words, ending with the request to approve, amend or reject each risk.

## §10 Sub-agent: `risk-assessor` (TODO #5)

**Kind:** sub-agent. Loads `.claude/skills/risk-assessment/SKILL.md` first and follows it.
Writes `outputs/risk-ratings.json` only; runs `build_register.py`; never edits the register
or the decision template. Reads the three summaries, never `data/` or `analytics-full/`.
Runs twice: to open the gate, and after the auditor's decisions to apply them (§9.8).

## §11 The human gate (TODO #6)

The student, as auditor, fills `outputs/auditor-comments.md` (format: `contract/files.md`): a
Decision for every risk (`approve`, `amend`, `reject`), a Comment saying what and why for
every amend or reject, `Reviewer:` and `Date:`. Then asks for the risk-assessor to re-run.
**Proof:** `build_pack.py --gate` exits 0. At least one amend or reject with a reason is
required (`benchmark/sla.json`); the reasoning is graded by a person.

## §12 The agent team and the lead (TODO #7)

1. `.claude/settings.json`: `{"env": {"CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS": "1"}}` (agent teams
   are an experimental Claude Code feature; restart the session after changing it).
2. `CLAUDE.md` § "How the lead runs the team", the main session's procedure when asked to run
   the team:
   1. Run `build_pack.py --gate` first. If it fails, report what is undecided and stop.
   2. Spawn `planner`, `challenger` and `qa-reviewer` as teammates from `.claude/agents/`, with
      those names, each told the other two names and that the gate is closed. The planner starts
      at once; the other two wait for `PACK READY v1`.
   3. The team runs itself (`contract/team-protocol.md`). The lead answers questions and relays
      nothing it was not asked to.
   4. On `PLANNER DONE`, `CHALLENGER DONE` and `QA DONE`, shut the three down.
   5. Report under 300 words: risks in scope, the three documents and the sample count, the
      challenges marked *for the auditor*, the QA verdict, and the request to complete the
      sign-off block. `BLOCKED` goes back to the team, never to the auditor.

## §13 Skill: `audit-program` (TODO #8)

**Kind:** skill (a method), loaded by the planner. **Writes (via the planner):**
`audit-plan.json` (`contract/audit-plan.schema.json`). **Proof:** `build_pack.py` reports `failures: 0`.

1. Gate first (`build_pack.py --gate`); plan exactly the approved, in-scope risks it lists.
2. Per risk: an `objective`; controls (`C-NN.n`), each citing at least one rule and naming the
   owner where the Rules name one; tests (`T-NN.n`), each tied to a control, with a `step` (what
   to obtain, compare, and what a pass looks like), the `evidence` to inspect, `cites`
   (a rule, plus the metric the risk rests on), a `sample` recipe and `pbc` (request) items.
3. Samples are recipes (`contract/audit-plan.schema.json` → `sample`; sources in
   `contract/files.md`), never lists: file, filters, order, size. Size by score: 10 items for
   scores of 9 and above, 5 below, all when fewer exist. General-procurement filter unless the
   risk is about placements. `exclude_drawn_in` so two tests do not pull the same payments.
   `kind: none` with a note for document or enquiry tests.
4. Every rule in rules.json is cited by a risk, control or test, or listed in `rules_not_tested`
   under an honest reason.
5. Memo sections (`purpose`, `background`, `approach`, `limitations`) as short paragraphs with
   placeholders; under 900 words of the model's own text.
6. Build and fix until clean; never edit a rendered file.

## §14 Teammate: `planner` (TODO #9)

Follows the audit-program skill. Writes `outputs/audit-plan.json` only. Protocol
(`contract/team-protocol.md`): `PACK READY vN` with the builder's summary line after every clean
build; one `RESPONSE #n` per challenge: accepted (change, rebuild, re-announce), declined (with a
reason), or `for the auditor` (rating and scope belong to the auditor's approved decisions); QA
failures fixed in the plan only; at most two challenge rounds; `PLANNER DONE vN` with five lines
(risks, controls, tests, sampled transactions, open points); `PLANNER BLOCKED` when the gate is
open or an input is missing. Reads `analytics-full/` with `head -3` only.

## §15 Teammate: `challenger` (TODO #10)

Writes `outputs/challenges.md` only. Reads the register, decisions, ratings, analytics.json,
history.json, rules.json and the pack; **never** `data/` or `analytics-full/` (checked from its
transcript). Tools must not include command execution (checked). Challenge types: `rating`
(low rating against a strong metric or adverse history) and `scope` (an adverse-history theme
left out): both for the auditor; `sample`, `control`, `test`, `coverage`: for the planner. Every
challenge cites a rule ID, metric path, history ID, or test or control ID; no citation, no
challenge. Sends `CHALLENGE #n [type] R-xx: … Evidence: … Ask: …`: at most eight in round one,
ordered by how much they would change the audit; verifies accepted changes in the next PACK READY;
at most four in round two; closes every row (`resolved`, `declined`, `for the auditor`); sends
`CHALLENGER DONE`. File format: `contract/files.md`. It challenges the plan, never the council.

## §16 Teammate: `qa-reviewer` (TODO #11)

Runs `python scripts/checks/run_checks.py` (quotes, numbers, trace, samples) on every PACK READY.
The scripts are the check: it never re-derives a result by reading files and never softens a
FAIL. Sends `QA vN: FAIL <check>: <at most ten items>` to the planner, `QA BLOCKED ON INPUT` to the
lead for inputs the planner does not own. Writes `outputs/review.md` only, and only after
`CHALLENGER DONE` and `PLANNER DONE`: version, date, the results table exactly as printed, the
failures, the run history, the verdict, and the empty sign-off block (`contract/files.md`).
Sends `QA DONE: READY FOR SIGN-OFF` or `QA DONE: BLOCKED`.

## §17 QA check: `scripts/checks/check_trace.py` (TODO #12)

The specification is the file's docstring; the contract (arguments, output lines, exit code,
read-only, inputs from the project versus the pack from `OUTPUTS_DIR`) is fixed there and relied
on by `run_checks.py` and the planted-error evaluation. Four checks: every rule accounted for;
every approved in-scope risk planned with control and test and present in the matrix and the
program, nothing else planned, no risk undecided; every High, Extreme or Very high risk in scope
or explained; challenges present, cited and closed. **Proof:** trace PASS on the real pack and
`eval/planted/plant_errors.py` 7 of 7 with the untouched pack passing.

## §18 Sign-off (TODO #13)

The student, as auditor, completes the block at the end of `outputs/review.md`: name, date,
decision (`sign off` or `return to the team`), comment. Signing off a pack whose verdict is
BLOCKED, or ignoring a challenge marked *for the auditor*, is graded down by a person.

## §19 Agent memory

Every agent has `memory: project` and a `.claude/agent-memory/<name>/MEMORY.md`. Memory holds
**how to do the work**: input quirks, pitfalls and fixes, wording a teammate rejected, method
instructions from the auditor not yet in the brief. It never holds figures, supplier names,
findings, ratings, decisions or challenge outcomes, and is never cited as evidence. When memory
contradicts the inputs, the inputs win and the entry is fixed. Under 150 lines. Each brief states this.

## §20 Evaluation (provided; details in `eval/README.md`)

| Instrument | Measures |
|---|---|
| contract schemas | each JSON output's shape |
| `Pack (rendered)` gate | the three pack documents equal a fresh build (never hand-edited) |
| `Language` gate | accusatory wording in model-written text, listed for a person to read |
| live test (`live-test.md`) | the skill on clauses the answer key does not cover, spot-checked by the student against the PDF |
| design interview (`design-interview.md`) | five questions on DESIGN.md, answers verbatim, for the person grading `design` |
| verifiers and builders | quotes, history quotes, register citations, the gate, the pack |
| `scripts/checks/run_checks.py` | quotes, numbers, trace, samples on the final pack |
| golden thread (`eval/run_all.py`) | every sampled payment → its workbook row → test → control → rule → verified quote, and an approved risk |
| `eval/planted/plant_errors.py` | seven planted mistakes caught, untouched pack passing |
| `eval/team/run_eval.py` (teamwork, self-reported) | from transcripts: challenges answered and closed, file ownership, challenger read no raw data, round limits, tools within definitions, a pack version per response round, all DONE |
| `quality/check.mjs` over `runs/` | each run terminated, no tool thrash, inside the budget in `expectations.json` |
| `eval/skill/run_eval.py` | the skill against the answer key, three fresh sessions |
| AI judges (`eval/subagents`, `eval/team`) | six dimensions per agent; **advisory, no points** |

Rubric: `eval/rubric.json` (eighty automated points, twenty manual). Report:
`eval/build_report.py` → `reports/report.json` and `reports/PRODUCT_EVAL.md`. Grader:
`eval/grade_url.py <url>`, which re-derives every automated row except the self-reported ones
(teamwork; harness hygiene items 4-5), which need the student's local transcripts.

## §21 Deploy and submit

- Vercel builds the static viewer from the repository: `vercel.json` runs `node viewer/collect.mjs`
  (no install) and serves `viewer/dist`. `/` is the pack, `/evals` the evaluation,
  `/evals/report.json` the machine-readable report, `/data/` every published file.
- For the build to see the run, commit `outputs/`, `eval/skill/runs/`, `runs/`,
  `reports/report.json`, `reports/PRODUCT_EVAL.md`, `DESIGN.md`, `trajectories.md`,
  `live-test.md` and `design-interview.md`.
- Supplier names are pseudonymised on publish; the build fails on a leak. Never bypass it.
- Submit the Vercel URL. It carries all three deliverables: the product (`/`), the evaluation
  report (`/evals`, also `/evals/PRODUCT_EVAL.md`) and the video (embedded on `/evals`).
  The video (60–90 s, edited or sped up through the long team run) shows: `/extract-rules` finishing
  with its quote check passing; one sub-agent running; a gate decision; team messages (PACK READY,
  a CHALLENGE and its RESPONSE); the QA verdict; `/` and `/evals` on the deployed URL.

## §22 Definition of done (self-verify; every line must hold)

```bash
python scripts/status.py                         # 13 of 13 done; every JSON output "valid"
python .claude/skills/extract-rules/verify_quotes.py outputs/rules.json data/contract-rules.pdf   # ALL CHECKS PASSED
python scripts/verify_history.py outputs/history.json data/committee                              # ALL CHECKS PASSED
python .claude/skills/risk-assessment/build_register.py outputs/risk-ratings.json                 # failures: 0, revision ≥ 1
python .claude/skills/audit-program/build_pack.py --gate                                          # gate closed
python scripts/checks/run_checks.py              # VERDICT: READY FOR SIGN-OFF (4/4)
python eval/planted/plant_errors.py              # 7 of 7, baseline yes
python eval/skill/run_eval.py --score-only       # three runs; weakest at or above the bars
python eval/run_all.py                           # every gate passes, including Pack (rendered) and Language
python eval/build_report.py --student "…" --video …   # no red line; "Still missing" empty
node viewer/collect.mjs                          # no LEAK
python eval/grade_url.py https://<your-app>.vercel.app   # every re-derivable number reproduced
```
