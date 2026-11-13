#!/usr/bin/env python3
"""Validate outputs/audit-plan.json and render the audit planning pack.

Usage: build_pack.py [PLAN_JSON] [--gate]
       [--rules outputs/rules.json] [--analytics outputs/analytics.json]
       [--ratings outputs/risk-ratings.json] [--register outputs/risk-register.md]
       [--comments outputs/auditor-comments.md] [--full outputs/analytics-full]
       [--out-dir outputs]

--gate only checks the auditor gate: every risk in the register has a
decision and the register is a revision that applied them. It prints the
approved scope and exits 0, or names what is missing and exits 1.

Otherwise the plan is validated and rendered:
  scope      every planned risk is approved and in scope; every approved
             in-scope risk is planned; nothing else.
  citations  [rule:ID] and [metric:$.path] resolve; {{$.path}} placeholders
             are filled from analytics.json; literal figures typed in prose
             are failures.
  samples    each test's sample recipe is drawn deterministically from a
             file in analytics-full/ and every transaction it yields exists
             in spend-clean.csv; the rows go to outputs/samples/<test>.csv.
  trace      every rule in rules.json is cited by a risk, a control or a
             test, or is listed in rules_not_tested with a reason; every
             planned risk has at least one control and one test.
Renders planning-memo.md, risk-control-matrix.md and audit-program.md
(ending with the PBC list) and writes pack-figures.json, the list of every
figure the builder itself computed, so the QA number check can trace them.
Exit 0 when no failures; exit 1 otherwise.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, csv, datetime, json, re, sys
from collections import OrderedDict
from pathlib import Path

CITE_RE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")
PH_RE = re.compile(r"\{\{(\$[^}]+)\}\}")
NUM_RE = re.compile(r"£\s?\d|\b\d{3,}\b")
HIGH_LABELS = {"high", "extreme", "very high"}
GATE_DECISIONS = {"approve", "amend", "reject"}


def jpath(obj, path):
    """Resolve $.a.b[0].c against obj; return (found, value)."""
    if not path.startswith("$"):
        return False, None
    cur = obj
    for tok in re.findall(r"\.([^.\[\]]+)|\[(\d+)\]", path[1:]):
        key, idx = tok
        try:
            cur = cur[int(idx)] if idx else cur[key]
        except (KeyError, IndexError, TypeError):
            return False, None
    return True, cur


def fmt(v):
    if isinstance(v, bool) or v is None:
        return str(v)
    if isinstance(v, float):
        return f"{v:,.2f}" if v != int(v) else f"{int(v):,}"
    if isinstance(v, int):
        return f"{v:,}"
    return str(v)


def gbp(v):
    try:
        return f"£{float(v):,.2f}"
    except (TypeError, ValueError):
        return str(v)


def read_decisions(path):
    """Decisions in auditor-comments.md: id -> {title, now, scope, decision, comment}."""
    out = {"reviewer": "", "date": "", "rows": OrderedDict()}
    if not path.exists():
        return out
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^Reviewer:[ \t]*(.*)$", text, re.M)
    out["reviewer"] = m.group(1).strip() if m else ""
    m = re.search(r"^Date:[ \t]*(.*)$", text, re.M)
    out["date"] = m.group(1).strip() if m else ""
    for line in text.splitlines():
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 6 and re.fullmatch(r"R-\d+", cells[0]):
            out["rows"][cells[0]] = {"title": cells[1], "now": cells[2], "scope": cells[3],
                                     "decision": cells[4].lower(), "comment": "|".join(cells[5:]).strip()}
    return out


def read_register(path):
    """Summary rows of risk-register.md: id -> {title, L, I, score, label, band, scope}; plus header revision."""
    rows, rev = OrderedDict(), None
    if not path.exists():
        return rows, rev
    text = path.read_text(encoding="utf-8")
    m = re.search(r"^\*Revision (\d+), following auditor comments", text, re.M)
    rev = int(m.group(1)) if m else None
    in_summary = False
    for line in text.splitlines():
        if line.startswith("## "):
            in_summary = line.strip() == "## Summary"
            continue
        if not in_summary:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) >= 9 and re.fullmatch(r"R-\d+", cells[0]):
            rows[cells[0]] = {"title": cells[1], "L": cells[2], "I": cells[3], "score": int(cells[4]),
                              "label": cells[5], "band": cells[6], "scope": cells[8]}
    return rows, rev


def scope_check(reg, rev, dec, ratings, fails):
    """The approved scope, or failures explaining why the gate is not closed."""
    if not reg:
        fails.append("gate: risk-register.md has no summary table")
        return OrderedDict(), OrderedDict()
    undecided = [rid for rid in reg if dec["rows"].get(rid, {}).get("decision", "") == ""]
    if undecided:
        fails.append(f"gate not closed: no decision for {', '.join(undecided)} in auditor-comments.md")
    bad = [rid for rid, v in dec["rows"].items() if v["decision"] and v["decision"] not in GATE_DECISIONS]
    if bad:
        fails.append(f"gate: decision not approve/amend/reject for {', '.join(bad)}")
    if rev is None:
        fails.append("gate: the register is not a revision; re-run the risk-assessor so the decisions are applied")
    rat = {r["id"]: r for r in ratings.get("risks", [])}
    excl = {x.get("id"): x for x in ratings.get("excluded", []) if x.get("id")}
    approved, out_of_scope = OrderedDict(), OrderedDict()
    for rid, v in dec["rows"].items():
        d = v["decision"]
        if d in ("approve", "amend"):
            if rid not in reg or rid not in rat:
                fails.append(f"gate: {rid} is {d}d but not in the current register")
                continue
            if rat[rid].get("recommend_in_scope", True):
                approved[rid] = {**reg[rid], "decision": d, "comment": v["comment"],
                                 "override": bool(rat[rid].get("auditor_override")),
                                 "sample_source": rat[rid].get("sample_source", "")}
            else:
                out_of_scope[rid] = {**reg[rid], "decision": d, "comment": v["comment"],
                                     "reason": "rated, recommended out of scope; approved as rated"}
        elif d == "reject":
            if rid in reg:
                fails.append(f"gate: {rid} was rejected but is still in the register; re-run the risk-assessor")
            reason = (excl.get(rid) or {}).get("reason") or v["comment"] or "rejected at the gate"
            out_of_scope[rid] = {"title": v["title"], "score": None, "label": "", "band": "",
                                 "decision": d, "comment": v["comment"], "reason": reason}
    return approved, out_of_scope


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def to_num(s):
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def draw_sample(spec, tid, full, spend_by_id, fails, drawn=None):
    """Apply a sample recipe to a file in analytics-full/. Returns (rows, describe).
    drawn: {test id: {"suppliers": set, "row_ids": set}} for tests already sampled, for exclude_drawn_in."""
    drawn = drawn or {}
    kind = spec.get("kind", "rows")
    if kind == "none":
        return [], spec.get("note", "no transaction sample; document or enquiry test")
    src = full / spec.get("source", "")
    if not src.exists():
        fails.append(f"{tid}: sample source not found {spec.get('source')}")
        return [], ""
    rows = load_csv(src)
    where = spec.get("where") or {}
    for col, want in where.items():
        if rows and col not in rows[0]:
            fails.append(f"{tid}: sample where-column {col!r} not in {spec['source']}")
            return [], ""
        wants = want if isinstance(want, list) else [want]
        wants = [str(w) for w in wants] + [fmt(w) for w in wants if isinstance(w, (int, float))]
        rows = [r for r in rows if r[col] in wants or (to_num(r[col]) is not None and any(to_num(r[col]) == to_num(w) for w in wants))]
    for col, lo in (spec.get("where_min") or {}).items():
        rows = [r for r in rows if to_num(r.get(col)) is not None and to_num(r[col]) >= float(lo)]
    for col, hi in (spec.get("where_max") or {}).items():
        rows = [r for r in rows if to_num(r.get(col)) is not None and to_num(r[col]) <= float(hi)]
    for col, pat in (spec.get("where_not_match") or {}).items():  # drop rows whose column matches a regex
        try:
            rx = re.compile(pat, re.I)
        except re.error:
            fails.append(f"{tid}: where_not_match pattern for {col!r} is not a valid regex"); return [], ""
        rows = [r for r in rows if not rx.search(r.get(col, ""))]
    excl_sup, excl_ids = set(), set()
    for other in spec.get("exclude_drawn_in") or []:  # skip what an earlier test already pulled
        if other not in drawn:
            fails.append(f"{tid}: exclude_drawn_in names {other}, which has not been sampled before this test"); return [], ""
        excl_sup |= drawn[other]["suppliers"]; excl_ids |= drawn[other]["row_ids"]
    if excl_sup and rows and "supplier_norm" in rows[0]:
        rows = [r for r in rows if r.get("supplier_norm") not in excl_sup]
    order = spec.get("order_by")
    if order:
        if rows and order not in rows[0]:
            fails.append(f"{tid}: sample order_by column {order!r} not in {spec['source']}")
            return [], ""
        rows.sort(key=lambda r: (to_num(r[order]) if to_num(r[order]) is not None else r[order]),
                  reverse=bool(spec.get("descending", True)))
    if spec.get("distinct_by"):  # one item per value of a column, first after sorting
        col, seen, uniq = spec["distinct_by"], set(), []
        if rows and col not in rows[0]:
            fails.append(f"{tid}: distinct_by column {col!r} not in {spec['source']}"); return [], ""
        for r in rows:
            if r[col] not in seen:
                seen.add(r[col]); uniq.append(r)
        rows = uniq
    n = int(spec.get("n", 10))
    picked = rows[:n]
    per = int(spec.get("per_group_n", 0) or 0)
    out = []
    for i, r in enumerate(picked, 1):
        if kind == "rows":
            ids = [r.get("row_id", "")]
            key = r.get("row_id", "")
        elif kind == "groups":
            ids = [x for x in re.split(r"[;,]\s*", r.get(spec.get("ids_column", "row_ids"), "")) if x]
            if per:  # largest payments of the group first
                ids.sort(key=lambda x: -(to_num((spend_by_id.get(x) or {}).get("Net amount")) or 0))
                ids = ids[:per]
            key = r.get(spec.get("key", "window_id" if "window_id" in r else "group_id"), str(i))
        elif kind == "suppliers":
            sup = r.get("supplier_norm", "")
            pay = [s for s in spend_by_id.values() if s.get("supplier_norm") == sup]
            pay.sort(key=lambda s: -(to_num(s.get("Net amount")) or 0))
            ids = [s["row_id"] for s in (pay[:per] if per else pay)]
            key = sup
        else:
            fails.append(f"{tid}: unknown sample kind {kind!r}")
            return [], ""
        for rid in ids:
            if rid in excl_ids:
                continue
            s = spend_by_id.get(rid)
            if not s:
                fails.append(f"{tid}: sampled row_id {rid} not found in spend-clean.csv")
                continue
            out.append({"test": tid, "item": i, "group": key, "row_id": rid, "source_file": s.get("source_file", ""),
                        "sheet_row": s.get("sheet_row", ""), "pay_date": s.get("pay_date", ""),
                        "supplier": s.get("Supplier name", ""), "amount": s.get("Net amount", ""),
                        "service": s.get("Service", ""), "narrative": s.get("Narrative", "")})
    parts = [f"{len(picked)} {'item' if len(picked) == 1 else 'items'} from `{spec['source']}`"]
    if where or spec.get("where_min") or spec.get("where_max"):
        conds = [f"{c} = {v}" for c, v in where.items()] + [f"{c} ≥ {v}" for c, v in (spec.get("where_min") or {}).items()] \
              + [f"{c} ≤ {v}" for c, v in (spec.get("where_max") or {}).items()]
        parts.append("where " + ", ".join(conds))
    if order:
        parts.append(f"largest {order} first" if spec.get("descending", True) else f"smallest {order} first")
    if kind == "suppliers":
        parts.append(f"{'all' if not per else per} payments per supplier")
    if kind == "groups" and per:
        parts.append(f"largest {per} payments per item")
    if spec.get("distinct_by"):
        parts.append(f"one item per {spec['distinct_by']}")
    if spec.get("where_not_match"):
        parts.append("excluding " + ", ".join(f"{c} matching /{pat}/" for c, pat in spec["where_not_match"].items()))
    if spec.get("exclude_drawn_in"):
        parts.append("excluding suppliers and rows already drawn in " + ", ".join(spec["exclude_drawn_in"]))
    if len(rows) < n:
        parts.append(f"(only {len(rows)} available)")
    return out, ", ".join(parts) + f"; {len(out)} transactions"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", nargs="?", default="outputs/audit-plan.json")
    ap.add_argument("--gate", action="store_true", help="only check the auditor gate and print the scope")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--ratings", default="outputs/risk-ratings.json")
    ap.add_argument("--register", default="outputs/risk-register.md")
    ap.add_argument("--comments", default="outputs/auditor-comments.md")
    ap.add_argument("--full", default="outputs/analytics-full")
    ap.add_argument("--out-dir", default="outputs")
    a = ap.parse_args()

    fails, warns, figures = [], [], OrderedDict()
    rules = json.loads(Path(a.rules).read_text())
    an = json.loads(Path(a.analytics).read_text())
    ratings = json.loads(Path(a.ratings).read_text())
    rule_ids = OrderedDict((r["rule_id"], r) for r in rules["rules"])
    reg, rev = read_register(Path(a.register))
    dec = read_decisions(Path(a.comments))
    approved, out_of_scope = scope_check(reg, rev, dec, ratings, fails)

    if a.gate:
        for f in fails: print("FAIL ", f)
        if not fails:
            print(f"gate closed: register revision {rev}, {len(dec['rows'])} decisions by {dec['reviewer'] or 'unnamed reviewer'} dated {dec['date'] or 'undated'}")
            print("approved, in scope: " + ", ".join(f"{rid} ({v['score']})" for rid, v in approved.items()))
            print("not in scope: " + (", ".join(f"{rid} ({v['decision']})" for rid, v in out_of_scope.items()) or "none"))
        return 1 if fails else 0

    P = json.loads(Path(a.plan).read_text())
    full = Path(a.full)
    spend_by_id = {r["row_id"]: r for r in load_csv(full / "spend-clean.csv")} if (full / "spend-clean.csv").exists() else {}
    if not spend_by_id:
        fails.append(f"{full}/spend-clean.csv missing: samples cannot be verified")

    # ---- citations and placeholders
    cited_rules = OrderedDict()   # rule -> set of places

    def resolve(text, where):
        ok = 0
        for kind, ref in CITE_RE.findall(text or ""):
            ref = ref.strip()
            if kind == "rule":
                if ref in rule_ids:
                    ok += 1; cited_rules.setdefault(ref, set()).add(where.split(".")[0])
                else:
                    fails.append(f"{where}: unknown rule {ref}")
            elif kind == "metric":
                found, val = jpath(an, ref)
                if found and not isinstance(val, (dict, list)): ok += 1
                elif found: fails.append(f"{where}: metric {ref} is not a scalar")
                else: fails.append(f"{where}: metric path not found {ref}")
            else:
                ok += 1  # history items are the register's business; the pack cites the register by risk id
        return ok

    def fill(text, where):
        def sub(m):
            found, val = jpath(an, m.group(1))
            if not found or isinstance(val, (dict, list)):
                fails.append(f"{where}: placeholder not resolvable {m.group(1)}")
                return "«unresolved»"
            return fmt(val)
        out = PH_RE.sub(sub, text or "")
        stripped = CITE_RE.sub("", PH_RE.sub("", text or ""))
        if NUM_RE.search(stripped):
            fails.append(f"{where}: literal figure typed in prose; use a {{{{metric}}}} placeholder: {stripped[:70]!r}")
        return out

    def strip_cites(text):
        return CITE_RE.sub("", text or "").replace("  ", " ").strip()

    def cite_list(cites, where):
        for c in cites or []:
            resolve(f"[{c}]", where)
        return ", ".join(c.split(":", 1)[1] if c.startswith("rule:") else c for c in cites or [])

    # ---- scope vs plan
    planned = OrderedDict((r["id"], r) for r in P.get("risks", []))
    for rid in planned:
        if rid not in approved:
            fails.append(f"scope: {rid} is planned but is not an approved, in-scope risk")
    for rid in approved:
        if rid not in planned:
            fails.append(f"scope: {rid} is approved and in scope but has no plan entry")
    # rules cited by the register's rated risks count as traced to a risk
    for r in ratings.get("risks", []):
        for kind, ref in CITE_RE.findall(json.dumps(r)):
            if kind == "rule" and ref in rule_ids:
                cited_rules.setdefault(ref, set()).add(r["id"])

    # ---- controls, tests, samples
    samples_dir = Path(a.out_dir) / "samples"
    samples_dir.mkdir(parents=True, exist_ok=True)
    for old in samples_dir.glob("T-*.csv"):
        old.unlink()
    all_samples, pbc, drawn = [], OrderedDict(), OrderedDict()
    n_controls = n_tests = 0
    for rid, r in planned.items():
        controls = r.get("controls") or []
        tests = r.get("tests") or []
        if not controls: fails.append(f"{rid}: no expected control")
        if not tests: fails.append(f"{rid}: no test step")
        cids = set()
        for c in controls:
            n_controls += 1
            cids.add(c.get("id"))
            if not c.get("cites"): fails.append(f"{rid}.{c.get('id')}: control cites no rule")
            c["_cites"] = cite_list(c.get("cites"), f"{rid}.{c.get('id')}")
            c["_text"] = fill(c.get("control", ""), f"{rid}.{c.get('id')}")
        tested = set()
        for t in tests:
            n_tests += 1
            tid = t.get("id", "?")
            if t.get("control") not in cids:
                fails.append(f"{rid}.{tid}: test refers to control {t.get('control')!r} which is not defined for this risk")
            tested.add(t.get("control"))
            if not t.get("cites"): fails.append(f"{rid}.{tid}: test cites no rule or metric")
            t["_cites"] = cite_list(t.get("cites"), f"{rid}.{tid}")
            t["_step"] = fill(t.get("step", ""), f"{rid}.{tid}")
            t["_evidence"] = fill(t.get("evidence", ""), f"{rid}.{tid}")
            spec = t.get("sample") or {"kind": "none", "note": "no sample specified"}
            rows, desc = draw_sample(spec, tid, full, spend_by_id, fails, drawn)
            t["_rows"], t["_desc"] = rows, desc
            drawn[tid] = {"suppliers": {(spend_by_id.get(s["row_id"]) or {}).get("supplier_norm") for s in rows},
                          "row_ids": {s["row_id"] for s in rows}}
            if spec.get("kind", "rows") != "none" and not rows:
                fails.append(f"{rid}.{tid}: sample recipe yielded no transactions")
            if rows:
                with open(samples_dir / f"{tid}.csv", "w", newline="", encoding="utf-8") as f:
                    w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
                all_samples += rows
            for item in t.get("pbc") or []:
                pbc.setdefault(rid, OrderedDict()).setdefault(item, []).append(tid)
        for c in controls:
            if c.get("id") not in tested:
                fails.append(f"{rid}.{c.get('id')}: control has no test")

    # ---- rule coverage
    not_tested = OrderedDict()
    for grp in P.get("rules_not_tested") or []:
        if not grp.get("reason"):
            fails.append("rules_not_tested: a group has no reason")
        for x in grp.get("rule_ids") or []:
            if x not in rule_ids: fails.append(f"rules_not_tested: unknown rule {x}")
            not_tested[x] = grp.get("reason", "")
    uncovered = [x for x in rule_ids if x not in cited_rules and x not in not_tested]
    if uncovered:
        fails.append(f"trace: {len(uncovered)} rules neither cited by a risk, control or test nor listed as not tested: {', '.join(uncovered[:12])}{'…' if len(uncovered) > 12 else ''}")
    both = [x for x in not_tested if x in cited_rules]
    if both:
        warns.append(f"rules listed as not tested but also cited: {', '.join(both)}")

    # ---- memo text
    M = P.get("memo") or {}
    memo = {k: [fill(p, f"memo.{k}") for p in (M.get(k) if isinstance(M.get(k), list) else [M.get(k, "")])] for k in ("purpose", "background", "approach", "limitations")}
    for k in ("purpose", "background", "approach"):
        if not any(s.strip() for s in memo[k]):
            fails.append(f"memo.{k} is empty")

    # ---- figures the builder computed (for the QA number check)
    # Sample recipes are the planner's only permitted digits: their values are recorded here so the number check can trace them.
    recipe_values = set()
    for r in planned.values():
        for t in r.get("tests") or []:
            spec = t.get("sample") or {}
            for key in ("n", "per_group_n"):
                if to_num(spec.get(key)) is not None: recipe_values.add(to_num(spec.get(key)))
            for cond in ("where", "where_min", "where_max"):
                for v in (spec.get(cond) or {}).values():
                    for x in (v if isinstance(v, list) else [v]):
                        if to_num(x) is not None: recipe_values.add(to_num(x))
    figures["sample_recipe_values"] = sorted(recipe_values)
    figures.update({
        "approved_in_scope": len(approved), "not_in_scope": len(out_of_scope), "register_risks": len(reg),
        "controls": n_controls, "tests": n_tests, "sampled_transactions": len(all_samples),
        "sampled_gbp": round(sum(to_num(s["amount"]) or 0 for s in all_samples), 2),
        "rules_total": len(rule_ids), "rules_cited": len([x for x in rule_ids if x in cited_rules]),
        "rules_not_tested": len([x for x in rule_ids if x not in cited_rules and x in not_tested]),
        "register_revision": rev, "decisions": len(dec["rows"]),
        "pbc_items": sum(len(v) for v in pbc.values()),
    })

    # ---- render
    today = P.get("generated_at") or str(datetime.date.today())
    who = f" by {dec['reviewer']}" if dec["reviewer"] else ""
    when = f" dated {dec['date']}" if dec["date"] else ""
    head_note = (f"*Generated {today} by `build_pack.py` from `audit-plan.json`, `risk-register.md` (revision {rev}), "
                 f"`auditor-comments.md`{who}{when}, `rules.json` and `analytics.json`. Status: DRAFT for challenge, QA review and auditor sign-off.*\n")
    indic = ("**Indicators, not findings.** Every test below checks a control against a pattern in public data. "
             "Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.\n")

    def risk_line(rid, v):
        sc = f"{v['score']} ({v['label']}; {v['band']})" if v.get("score") is not None else "not rated"
        return f"{rid}: {v['title']} [{sc}]"

    # planning memo
    md = ["# Procurement audit: planning memo\n", head_note, indic, "## Purpose\n", *memo["purpose"], "\n## Background\n", *memo["background"]]
    md.append("\n## Scope\n")
    n_out = figures['not_in_scope']
    md.append(f"The register lists {figures['register_risks']} rated risks. The auditor recorded {figures['decisions']} decisions{who}{when}: "
              f"{figures['approved_in_scope']} risks are approved and in scope, and {n_out} {'is' if n_out == 1 else 'are'} not.\n")
    md.append("| ID | Risk | Score | Band | Decision | Auditor comment |\n|---|---|---|---|---|---|")
    for rid, v in approved.items():
        note = v["comment"] + (" (auditor override applied)" if v["override"] else "")
        md.append(f"| {rid} | {v['title']} | {v['score']} | {v['band']} | {v['decision']} | {note} |")
    if out_of_scope:
        md.append("\n**Not in scope**\n")
        for rid, v in out_of_scope.items():
            md.append(f"- {rid}: {v['title']}: {v['decision']}; {v['reason']}")
    md += ["\n## Approach\n", *memo["approach"]]
    md.append(f"\nThe programme holds {figures['controls']} expected controls and {figures['tests']} test steps, with {figures['sampled_transactions']} "
              f"sampled transactions worth £{figures['sampled_gbp']:,.2f}, each traceable to its row in the council's published workbooks "
              f"(see `audit-program.md` and `outputs/samples/`).")
    md.append("\n## Rules coverage\n")
    md.append(f"{figures['rules_cited']} of {figures['rules_total']} rules in `rules.json` are cited by a risk, a control or a test. "
              f"The remaining {figures['rules_not_tested']} are not tested in this audit, for these reasons:\n")
    by_reason = OrderedDict()
    for x, why in not_tested.items():
        if x not in cited_rules: by_reason.setdefault(why, []).append(x)
    for why, xs in by_reason.items():
        md.append(f"- {why}: {', '.join(xs)}")
    if memo["limitations"] and any(s.strip() for s in memo["limitations"]):
        md.append("\n## Limitations\n")
        for l in memo["limitations"]:
            if l.strip(): md.append(f"- {l}")
    md.append("\n## Review and sign-off\n")
    md.append("The challenger's points and their status are in `challenges.md`; points marked *for the auditor* need a decision at sign-off. "
              "The QA reviewer's checks and verdict are in `review.md`, which ends with the sign-off block.")
    Path(a.out_dir, "planning-memo.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # risk-control matrix
    md = ["# Risk-control matrix\n", head_note, indic]
    md.append("| Risk | Score | Expected control | Rules | Tests |\n|---|---|---|---|---|")
    for rid, r in planned.items():
        v = approved.get(rid, {})
        for c in r.get("controls") or []:
            tests = ", ".join(t.get("id", "?") for t in r.get("tests") or [] if t.get("control") == c.get("id"))
            md.append(f"| {rid}: {v.get('title', '')} | {v.get('score', '')} ({v.get('band', '')}) | {c.get('id')}: {c['_text']} | {c['_cites']} | {tests} |")
    Path(a.out_dir, "risk-control-matrix.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # audit program
    md = ["# Audit program\n", head_note, indic]
    md.append(f"{figures['approved_in_scope']} risks in scope, {figures['controls']} controls, {figures['tests']} tests, "
              f"{figures['sampled_transactions']} sampled transactions. Samples are drawn by the builder from `analytics-full/` "
              f"by the recipe stated under each test, and every transaction is listed with its workbook row.\n")
    for rid, r in planned.items():
        v = approved.get(rid, {})
        md.append(f"\n## {risk_line(rid, v)}\n")
        if r.get("objective"): md.append(f"**Audit objective.** {fill(r['objective'], f'{rid}.objective')}\n")
        for c in r.get("controls") or []:
            md.append(f"**{c.get('id')}. Expected control.** {c['_text']} [{c['_cites']}]" + (f" Owner: {c['owner']}." if c.get("owner") else "") + "\n")
            for t in r.get("tests") or []:
                if t.get("control") != c.get("id"): continue
                md.append(f"**{t.get('id')}. Test.** {t['_step']} [{t['_cites']}]  \n**Evidence to inspect:** {t['_evidence']}  \n**Sample:** {t['_desc']}\n")
                if t["_rows"]:
                    md.append("| # | Row ID | Date | Supplier | Amount | Service |\n|---|---|---|---|---|---|")
                    for s in t["_rows"]:
                        md.append(f"| {s['item']} | `{s['row_id']}` | {s['pay_date']} | {s['supplier']} | {gbp(s['amount'])} | {s['service']} |")
                    md.append("")
    md.append("\n## Prepared-by-client (PBC) request list\n")
    md.append("Derived from the test steps above. Each item names the tests that need it.\n")
    md.append("| # | Risk | Item requested | For tests |\n|---|---|---|---|")
    n = 0
    for rid, items in pbc.items():
        for item, tids in items.items():
            n += 1
            md.append(f"| {n} | {rid} | {item} | {', '.join(tids)} |")
    Path(a.out_dir, "audit-program.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    Path(a.out_dir, "pack-figures.json").write_text(json.dumps({"generated_at": today, "figures": figures}, indent=2) + "\n", encoding="utf-8")

    for w in warns: print("WARN ", w)
    for f in fails: print("FAIL ", f)
    print(f"\nscope: {len(approved)} approved risks planned, {len(out_of_scope)} not in scope; controls: {n_controls}; tests: {n_tests}; "
          f"sampled transactions: {len(all_samples)}; rules cited: {figures['rules_cited']}/{figures['rules_total']}; warnings: {len(warns)}; failures: {len(fails)}")
    for name in ("planning-memo.md", "risk-control-matrix.md", "audit-program.md", "pack-figures.json"):
        print(f"written: {Path(a.out_dir, name)}")
    print(f"written: {samples_dir}/ ({len([p for p in samples_dir.glob('T-*.csv')])} files)")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
