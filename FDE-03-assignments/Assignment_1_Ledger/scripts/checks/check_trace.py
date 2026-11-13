#!/usr/bin/env python3
"""QA check: traceability of the pack.            TODO (YOU) #12

The other three QA checks are provided. This one is yours, because it is the
check that holds the whole harness together: it proves that nothing in the
pack floats free of a rule, an approved risk, or a closed challenge.

It must fail (exit 1, one `FAIL <reason>` line per problem) when ANY of these
is untrue, and pass (exit 0) only when all four hold:

1. Every rule in outputs/rules.json is cited by a rated risk (risk-ratings.json),
   a control or a test (audit-plan.json), or listed in `rules_not_tested` with a
   non-empty reason.
2. Every approved, in-scope risk (auditor-comments.md + risk-register.md) is
   planned with at least one control, every control has at least one test, and
   the risk appears in risk-control-matrix.md and audit-program.md. Nothing that
   is not approved and in scope is planned. No risk in the register is undecided.
3. Every risk whose matrix label is High, Extreme or Very high is in scope, or was
   rejected with a comment, or is listed under "**Not in scope**" in the memo as
   `- R-xx: <title>: <reason>`.
4. outputs/challenges.md exists, has at least one challenge row, every row's
   Evidence cell cites something (a rule, a metric path, an audit/history or
   test/control ID), and no row's Status is `open` or blank.

The contract (do not change it; eval/planted/ and run_checks.py rely on it):
- `python scripts/checks/check_trace.py [OUTPUTS_DIR]`. OUTPUTS_DIR, when given,
  is a folder holding a COPY of the pack (audit-plan.json, the three .md files,
  challenges.md). The register, the decisions, the ratings and rules.json ALWAYS
  come from the project's own outputs/ (IN below). The planted-error evaluation
  copies the pack, plants a mistake in the copy and expects this script to fail.
- Print every failure as a line starting `FAIL `, then exactly one line starting
  `SUMMARY trace:` (format in main()). Exit 1 on any failure, 0 otherwise.
- Read the files; never write any.

Where the formats are defined: contract/files.md (the Markdown tables) and
contract/audit-plan.schema.json. The rendered files are written by the provided
builders, so open a real one to see a row before you parse it.

Done when: `python scripts/checks/run_checks.py` shows trace PASS on your pack AND
`python eval/planted/plant_errors.py` reports 7 of 7 planted errors caught.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "outputs"                                                   # register, decisions, ratings, rules
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs"     # the pack being checked

# Provided helpers -------------------------------------------------------------
CITE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")   # [rule:CPR-13] [metric:$.a.b[0]] [history:AUD-05]
HIGH = {"high", "extreme", "very high"}                                  # matrix labels that must be in scope or explained
EVIDENCE = re.compile(r"CPR-\d+|\$\.[\w.\[\]]+|\b(?:AUD|RT|D|T|C)-\d+|scoring_method")  # what counts as a citation in challenges.md


def read(path):
    return path.read_text(encoding="utf-8") if path.exists() else ""


def table_rows(text, first_col=r"R-\d+"):
    """Cells of every Markdown table row whose first cell matches first_col, e.g.
    table_rows(register) -> [["R-02", "Requirements split ...", "3", "4", "12", "High", ...], ...]"""
    rows = []
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if cells and re.fullmatch(first_col, cells[0]):
            rows.append(cells)
    return rows


def load():
    """Everything the four checks need, loaded once. Missing files load as empty."""
    return {
        "rules": [r["rule_id"] for r in json.loads(read(IN / "rules.json") or '{"rules": []}')["rules"]],
        "ratings": json.loads(read(IN / "risk-ratings.json") or "{}"),
        "register": read(IN / "risk-register.md"),        # its "## Summary" table: ID | Risk | L | I | Score | Matrix label | Band | CRR rule | Recommend in scope
        "comments": read(IN / "auditor-comments.md"),     # its "## Decisions" table: ID | Risk | Now | Scope now | Decision | Comment
        "plan": json.loads(read(OUT / "audit-plan.json") or "{}"),
        "memo": read(OUT / "planning-memo.md"),
        "matrix": read(OUT / "risk-control-matrix.md"),   # rows start "| R-xx: <title> |"
        "program": read(OUT / "audit-program.md"),        # sections start "## R-xx: <title>"
        "challenges_path": OUT / "challenges.md",         # table: # | Type | Risk | Challenge | Evidence | Ask | Response | Status
    }


# TODO (YOU) #12 ---------------------------------------------------------------
# Each function appends one plain-English string per problem to `fails` and
# returns the counts main() prints. Hints, in order of how much they give away:
#   1. The docstring at the top of this file is the specification.
#   2. CITE finds rule citations inside a rating's text; `cites` lists in the
#      plan look like ["rule:CPR-13", "metric:$.tests..."].
#   3. A risk is approved when its Decision is approve or amend AND its rating's
#      recommend_in_scope is not false.

def check_rules_accounted(d, fails):
    """Check 1. Return (cited_rule_ids: set, not_tested: dict rule_id -> reason)."""
    raise NotImplementedError("TODO (YOU) #12: check_rules_accounted() in scripts/checks/check_trace.py")


def check_scope(d, fails):
    """Check 2. Return (summary: dict risk_id -> {"label", "band", "scope"},
    decisions: dict risk_id -> {"decision", "comment"}, approved: list, planned: dict)."""
    raise NotImplementedError("TODO (YOU) #12: check_scope() in scripts/checks/check_trace.py")


def check_high_risks(d, summary, decisions, approved, fails):
    """Check 3. Returns nothing."""
    raise NotImplementedError("TODO (YOU) #12: check_high_risks() in scripts/checks/check_trace.py")


def check_challenges(d, fails):
    """Check 4. Return (n_challenges: int, open_rows: list of challenge numbers)."""
    raise NotImplementedError("TODO (YOU) #12: check_challenges() in scripts/checks/check_trace.py")


# Provided: orchestration and the output format ---------------------------------
def main():
    d, fails = load(), []
    if not d["plan"]:
        fails.append("audit-plan.json missing")
    cited, not_tested = check_rules_accounted(d, fails)
    summary, decisions, approved, planned = check_scope(d, fails)
    check_high_risks(d, summary, decisions, approved, fails)
    n_ch, open_rows = check_challenges(d, fails)
    rules = d["rules"]
    for f in fails:
        print("FAIL ", f)
    print(f"SUMMARY trace: rules={len(rules)} rules_cited={len([x for x in rules if x in cited])} "
          f"rules_not_tested={len([x for x in rules if x not in cited and not_tested.get(x)])} "
          f"approved_in_scope={len(approved)} planned={len(planned)} "
          f"high_risks={len([1 for v in summary.values() if v['label'].lower() in HIGH])} "
          f"challenges={n_ch} open={len(open_rows)} failures={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
