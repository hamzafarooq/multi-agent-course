#!/usr/bin/env python3
"""Validate outputs/risk-ratings.json and render outputs/risk-register.md.

Usage: build_register.py RATINGS_JSON [--rules outputs/rules.json]
       [--analytics outputs/analytics.json] [--history outputs/history.json]
       [--out outputs/risk-register.md] [--comments outputs/auditor-comments.md]

Citations: [rule:CPR-13]  [metric:$.path.in.analytics]  [history:AUD-16]
Placeholders: {{$.path.in.analytics}} → value inserted from analytics.json.
Scores, matrix labels and bands are computed here from history.json.
Also writes the auditor's decision template (--comments), keeping any
decisions already in it. When that file holds decisions, the ratings file
must declare a "revision" block listing every amended and rejected ID;
the register is then headed as a revision and each decision is checked:
one left unapplied, or a change the auditor did not ask for, is a failure.
Exit 0 when no failures (warnings allowed); exit 1 otherwise.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, datetime, json, re, sys
from pathlib import Path

CITE_RE = re.compile(r"\[(rule|metric|history):((?:[^\[\]]|\[\d+\])+)\]")
PH_RE = re.compile(r"\{\{(\$[^}]+)\}\}")
NUM_RE = re.compile(r"£\s?\d|\b\d{3,}\b")
ADVERSE = re.compile(r"limited|weak|unsatisfactory|no assurance", re.I)


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


def history_index(h):
    idx = {}
    for a in h.get("audits", []):
        idx[a["id"]] = a
    for t in h.get("risk_themes", []):
        idx[t["id"]] = t
    for d in h.get("discrepancies", []):
        idx[d["id"]] = d
    for g in h.get("gaps", []):
        idx[g.get("item")] = g
    idx["scoring_method"] = h.get("scoring_method", {})
    return idx


COMMENTS_HEAD = """# Auditor comments: risk register gate

Reviewer: {reviewer}
Date: {date}
Register reviewed: `outputs/risk-register.md`, generated {generated}

## How to fill this in

- Put one word in **Decision** for each risk: `approve`, `amend` or `reject`.
- **approve** keeps the risk as rated. Leave Comment empty or add a note.
- **amend** changes the risk. Say exactly what to change, for example
  "likelihood 3, because ..." or "bring into scope" or "change focus to ...".
- **reject** removes the risk from scope. Give the reason.
- Leave Decision blank if you have not decided yet. Blank rows are ignored.
- Scores are shown as likelihood × impact = score, as they stand now.

This file is written by the risk-assessor each time it builds the register.
Your decisions and comments are kept when it is rewritten. When you are
done, ask for the risk-assessor to be re-run: it keeps approved risks,
applies amendments, moves rejections to the excluded list and marks the
register as a revision.

## Decisions

| ID | Risk | Now | Scope now | Decision | Comment |
|---|---|---|---|---|---|
"""

COMMENTS_TAIL = """
## Scope and general comments

Anything that is not about a single risk: missing risks you want added,
changes to the overall scope, or questions for the next run.

"""


def read_existing_comments(path):
    """Decisions, reviewer, date and general comments already in the file, so a rebuild never loses them."""
    out = {"reviewer": "", "date": "", "rows": {}, "general": "-"}
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
            out["rows"][cells[0]] = {"title": cells[1], "decision": cells[4], "comment": "|".join(cells[5:]).strip()}
    m = re.search(r"^## Scope and general comments\n.*?\n\n(.*)\Z", text, re.S | re.M)
    if m and m.group(1).strip():
        out["general"] = m.group(1).strip()
    return out


def write_comments_template(path, kept, generated):
    """One decision row per rated risk. Filled-in decisions are carried over; a decided risk
    that has since left the register keeps its row, marked as no longer rated."""
    old = read_existing_comments(path)
    rows, seen = [], set()
    for r, score, _label, _band in kept:
        prev = old["rows"].get(r["id"], {})
        L, I = r["likelihood"]["score"], r["impact"]["score"]
        scope = "in" if r.get("recommend_in_scope", True) else "out"
        rows.append(f"| {r['id']} | {r['title']} | {L} × {I} = {score} | {scope} | {prev.get('decision', '')} | {prev.get('comment', '')} |")
        seen.add(r["id"])
    carried = [rid for rid, v in old["rows"].items() if rid not in seen and v["decision"]]
    for rid in sorted(carried, key=lambda x: int(x.split("-")[1])):
        v = old["rows"][rid]
        rows.append(f"| {rid} | {v['title']} | not rated now | excluded | {v['decision']} | {v['comment']} |")
    decided = sum(1 for rid in seen if old["rows"].get(rid, {}).get("decision"))
    head = COMMENTS_HEAD.format(reviewer=old["reviewer"], date=old["date"], generated=generated)
    path.write_text(head + "\n".join(rows) + "\n" + COMMENTS_TAIL + old["general"] + "\n", encoding="utf-8")
    return f"{len(kept)} risks, {decided} with a decision already recorded"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("ratings")
    ap.add_argument("--rules", default="outputs/rules.json")
    ap.add_argument("--analytics", default="outputs/analytics.json")
    ap.add_argument("--history", default="outputs/history.json")
    ap.add_argument("--out", default="outputs/risk-register.md")
    ap.add_argument("--comments", default="outputs/auditor-comments.md",
                    help="auditor decision template, kept in step with the register")
    a = ap.parse_args()

    R = json.loads(Path(a.ratings).read_text())
    rules = json.loads(Path(a.rules).read_text())
    an = json.loads(Path(a.analytics).read_text())
    h = json.loads(Path(a.history).read_text())
    rule_ids = {r["rule_id"]: r for r in rules["rules"]}
    hidx = history_index(h)
    sm = h.get("scoring_method", {})
    council = bool(sm.get("usable")) and R.get("scale", {}).get("source", "council") == "council"

    fails, warns = [], []

    # ---- scale
    if council:
        lik = {l["score"]: l for l in sm["likelihood_scale"]}
        imp = {i["score"]: i for i in sm["impact_scale"]}
        cells = {}
        for row in sm["combination"]["matrix_cells"]:
            for L, s, lab in zip(row["likelihood"], row["scores"], row["labels"]):
                cells[(L, row["impact"])] = (s, lab)
        bands = sm["bands"]
        crr = sm.get("corporate_register_threshold", {}).get("score")
    else:
        labels = ["Very low", "Low", "Medium", "High", "Very high"]
        lik = {i + 1: {"label": labels[i], "definition": ""} for i in range(5)}
        imp = {i + 1: {"label": labels[i]} for i in range(5)}
        cells = {(L, I): (L * I, "High" if L * I >= 15 else "Medium" if L * I >= 8 else "Low") for L in range(1, 6) for I in range(1, 6)}
        bands = [{"level": "High", "score_low": 15, "score_high": 25}, {"level": "Medium", "score_low": 8, "score_high": 12},
                 {"level": "Low", "score_low": None, "score_high": 6}]
        crr = None

    def band_of(score):
        for b in bands:
            lo = b.get("score_low") or 0
            hi = b.get("score_high") or 99
            if lo <= score <= hi:
                return b["level"]
        return "unbanded"

    # ---- resolve citations / placeholders
    def resolve_cites(text, where):
        ok = 0
        for kind, ref in CITE_RE.findall(text or ""):
            ref = ref.strip()
            if kind == "rule":
                if ref in rule_ids: ok += 1
                else: fails.append(f"{where}: unknown rule {ref}")
            elif kind == "metric":
                found, val = jpath(an, ref)
                if found and not isinstance(val, (dict, list)): ok += 1
                elif found: fails.append(f"{where}: metric {ref} is not a scalar")
                else: fails.append(f"{where}: metric path not found {ref}")
            else:
                if ref in hidx: ok += 1
                else: fails.append(f"{where}: unknown history item {ref}")
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
            warns.append(f"{where}: literal figure typed in prose; use a {{{{metric}}}} placeholder: {stripped[:70]!r}")
        return out

    def strip_cites(text):
        return CITE_RE.sub("", text).strip()

    kept, dropped = [], []
    for r in R.get("risks", []):
        rid = r.get("id", "?")
        errs_before = len(fails)
        L, I = r["likelihood"]["score"], r["impact"]["score"]
        if L not in lik or I not in imp:
            fails.append(f"{rid}: likelihood/impact must be integers 1-5")
            dropped.append((r, "score out of range")); continue
        nl = resolve_cites(r["likelihood"]["justification"], f"{rid}.likelihood")
        ni = resolve_cites(r["impact"]["justification"], f"{rid}.impact")
        if nl == 0:
            fails.append(f"{rid}: likelihood justification has no resolvable citation")
        if ni == 0:
            fails.append(f"{rid}: impact justification has no resolvable citation")
        for e in r.get("evidence", []):
            resolve_cites(f"[{e['cite']}]", f"{rid}.evidence")
        rf = r.get("repeat_finding") or {}
        if rf.get("applied"):
            item = hidx.get(rf.get("history_id"))
            text = " ".join(str(item.get(k, "")) for k in ("opinion", "implementation_opinion")) if item else ""
            if not item or not ADVERSE.search(text):
                fails.append(f"{rid}: repeat_finding cites {rf.get('history_id')} which is not an adverse opinion")
        if NUM_RE.search(CITE_RE.sub("", r.get("statement", ""))):
            warns.append(f"{rid}: figure in risk statement; keep statements qualitative")
        if len(fails) > errs_before:
            dropped.append((r, "; ".join(fails[errs_before:])))
        else:
            score, label = cells[(L, I)]
            kept.append((r, score, label, band_of(score)))

    kept.sort(key=lambda t: (-t[1], t[0]["id"]))

    # ---- auditor decisions (a re-run after the gate must apply every one, and nothing else)
    old = read_existing_comments(Path(a.comments))
    decided = {rid: v for rid, v in old["rows"].items() if v["decision"]}
    rev = R.get("revision") or {}
    changed = rev.get("changed") or {}
    kept_ids = {r["id"] for r, *_ in kept}
    excl_ids = {x.get("id") for x in R.get("excluded", []) if x.get("id")}
    if decided and not rev:
        fails.append("auditor-comments.md records decisions but the ratings file has no `revision` block: apply them and declare the revision")
    if rev and not decided:
        fails.append("ratings file declares a revision but auditor-comments.md records no decisions")
    for rid, how in changed.items():
        d = decided.get(rid, {}).get("decision", "").lower()
        if how == "amended":
            if rid not in kept_ids: fails.append(f"revision: {rid} listed as amended but is not in the register")
            if d != "amend": fails.append(f"revision: {rid} amended without an amend decision in auditor-comments.md")
        elif how == "rejected":
            if rid not in excl_ids: fails.append(f"revision: {rid} listed as rejected but is not in `excluded` with its id")
            if d != "reject": fails.append(f"revision: {rid} rejected without a reject decision in auditor-comments.md")
        else:
            fails.append(f"revision: {rid} change {how!r} is not 'amended' or 'rejected'")
    for rid, v in decided.items():
        d = v["decision"].lower()
        if d == "approve" and rid not in kept_ids:
            fails.append(f"decision ignored: {rid} is approved but no longer in the register")
        elif d == "amend" and changed.get(rid) != "amended":
            fails.append(f"decision ignored: {rid} has an amend decision but revision.changed does not list it as amended")
        elif d == "reject" and changed.get(rid) != "rejected":
            fails.append(f"decision ignored: {rid} has a reject decision but revision.changed does not list it as rejected")
        elif d not in ("approve", "amend", "reject"):
            fails.append(f"auditor-comments.md: {rid} decision {v['decision']!r} is not approve, amend or reject")
    for r, *_ in kept:
        if r.get("auditor_override") and decided.get(r["id"], {}).get("decision", "").lower() != "amend":
            fails.append(f"{r['id']}: auditor_override set without an amend decision in auditor-comments.md")

    # ---- render
    today = R.get("generated_at") or str(datetime.date.today())
    when = f" dated {old['date']}" if old["date"] else ""
    rev_no = rev.get("number", 1) if rev else None
    status = f"REVISION {rev_no} for auditor sign-off" if rev else "DRAFT for auditor review (Phase 2 gate)"
    md = []
    md.append("# Procurement audit planning: risk register\n")
    md.append(f"*Generated {today} from `rules.json`, `analytics.json`, `history.json` via `risk-ratings.json`. "
              f"Status: {status}. Every rating below cites a rule, a named metric or a history item; "
              f"all figures are inserted from analytics.json by the builder.*\n")
    if rev:
        chg = ", ".join(f"{rid} ({how})" for rid, how in changed.items()) or "none"
        md.append(f"*Revision {rev_no}, following auditor comments{when}. Changed: {chg}.*\n")
    md.append("**Indicators, not findings.** Every risk describes a pattern in public data or a control to test. "
              "Nothing here asserts wrongdoing by the council, a department, an officer or a supplier.\n")
    md.append("## Scoring scale\n")
    if council:
        src = sm.get("source"); pg = sm.get("pdf_page")
        md.append(f"Council scale from `{src}` (p.{pg}): likelihood 1–5 × impact 1–5, read from the 5×5 matrix; bands from Table 4.\n")
        md.append("| Likelihood | Label | Definition |\n|---|---|---|")
        for s in sorted(lik):
            md.append(f"| {s} | {lik[s]['label']} | {lik[s].get('definition','')} ({lik[s].get('probability','')}) |")
        md.append("\n| Impact | Label | Financial band | Compliance descriptor |\n|---|---|---|---|")
        for s in sorted(imp):
            md.append(f"| {s} | {imp[s]['label']} | {imp[s].get('financial','')} | {imp[s].get('compliance','')} |")
        md.append("\n| Band | Scores | Escalation |\n|---|---|---|")
        for b in bands:
            md.append(f"| {b['level']} | {b.get('score_text') or f'{b.get('score_low')}–{b.get('score_high')}'} | {b.get('escalation','')} |")
        note = R.get("scale", {}).get("register_threshold_note")
        if note: md.append(f"\n> {note}")
        if crr: md.append(f"\n> Figure 4 corporate-register rule: score ≥ {crr}. Marked per risk below as \"CRR rule\".")
    else:
        md.append("**Fallback scale** (history.json reports no usable council method): likelihood and impact 1–5 Very low … Very high; score = L × I; High ≥ 15, Medium 8–12, Low ≤ 6.\n")

    md.append("\n## Summary\n")
    md.append("| ID | Risk | L | I | Score | Matrix label | Band | CRR rule | Recommend in scope |\n|---|---|---|---|---|---|---|---|---|")
    for r, score, label, band in kept:
        crr_mark = ("yes" if crr and score >= crr else "no") if crr else "n/a"
        md.append(f"| {r['id']} | {r['title']} | {r['likelihood']['score']} | {r['impact']['score']} | {score} | {label} | {band} | {crr_mark} | {'yes' if r.get('recommend_in_scope', True) else 'no'} |")

    md.append("\n## Risks\n")
    for r, score, label, band in kept:
        rid = r["id"]
        md.append(f"### {rid}: {r['title']}\n")
        md.append(f"**Theme:** {r.get('theme','')}  \n**Score:** {score} ({label}; band {band})\n")
        if r.get("auditor_override"):
            md.append("**Auditor override.** This score was set by the auditor at the gate (see `outputs/auditor-comments.md`); "
                      "the justification below quotes the decision and keeps its own citations.\n")
        md.append(f"**Risk.** {fill(r.get('statement',''), rid)}\n")
        md.append(f"**Likelihood {r['likelihood']['score']} ({lik[r['likelihood']['score']]['label']}).** {fill(r['likelihood']['justification'], rid)}\n")
        md.append(f"**Impact {r['impact']['score']} ({imp[r['impact']['score']]['label']}; driving column: {r['impact'].get('column','')}).** {fill(r['impact']['justification'], rid)}\n")
        rf = r.get("repeat_finding") or {}
        if rf.get("applied"):
            md.append(f"**Repeat finding uplift applied (+1 likelihood):** {rf.get('note','')} [history:{rf.get('history_id')}]\n")
        md.append("**Evidence.**\n")
        for e in r.get("evidence", []):
            kind, ref = e["cite"].split(":", 1)
            if kind == "rule":
                ru = rule_ids[ref]
                md.append(f"- [rule:{ref}] clause {ru['clause']} (p.{ru['page']}): \"{ru['verbatim_quote'][:160]}{'…' if len(ru['verbatim_quote'])>160 else ''}\"")
            elif kind == "metric":
                _, val = jpath(an, ref)
                md.append(f"- [metric:{ref}] = **{fmt(val)}**{', ' + e['label'] if e.get('label') else ''}")
            else:
                it = hidx[ref]
                desc = e.get("label") or it.get("audit_title") or it.get("theme") or it.get("item") or ref
                src = f" ({it.get('source')}, p.{it.get('pdf_page')})" if it.get("source") else ""
                md.append(f"- [history:{ref}] {desc}{src}")
        md.append(f"\n**Proposed focus.** {r.get('proposed_focus','')}  \n**Sample source:** `{r.get('sample_source','')}`\n")

    if dropped or R.get("excluded"):
        md.append("\n## Risks considered and excluded\n")
        for r, why in dropped:
            md.append(f"- **{r.get('title')}**: excluded by validation: {why}")
        for x in R.get("excluded", []):
            tag = f"{x['id']}: " if x.get("id") else ""
            md.append(f"- **{tag}{x.get('title')}**: {x.get('reason')}")
    if R.get("limitations"):
        md.append("\n## Limitations and data gaps\n")
        for l in R["limitations"]:
            md.append(f"- {fill(l, 'limitations')}")
    md.append("\n## Auditor decisions\n")
    if not decided:
        md.append("None recorded yet. For each risk, put **approve** (in scope as rated), **amend** (say what to change and why) "
                  "or **reject** (out of scope, say why) in `outputs/auditor-comments.md`. The risk-assessor applies the decisions "
                  "on its next run and marks the register as a revision.")
    else:
        md.append(f"Read from `outputs/auditor-comments.md`{when}. Undecided risks are not listed.\n")
        md.append("| ID | Decision | Comment | Applied as |\n|---|---|---|---|")
        for rid in sorted(decided, key=lambda x: int(x.split("-")[1])):
            v = decided[rid]
            applied = changed.get(rid) or ("kept as rated" if v["decision"].lower() == "approve" else "not applied")
            md.append(f"| {rid} | {v['decision']} | {v['comment']} | {applied} |")

    Path(a.out).write_text("\n".join(md) + "\n", encoding="utf-8")
    comments_note = write_comments_template(Path(a.comments), kept, today + (f" (revision {rev_no})" if rev else ""))
    if rev:
        comments_note += f"; revision {rev_no}, {len(changed)} changed"

    for w in warns: print("WARN ", w)
    for f in fails: print("FAIL ", f)
    print(f"\nrisks kept: {len(kept)}, excluded by validation: {len(dropped)}, warnings: {len(warns)}, failures: {len(fails)}")
    print(f"written: {a.out}")
    print(f"written: {a.comments} ({comments_note})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
