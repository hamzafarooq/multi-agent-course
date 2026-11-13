#!/usr/bin/env python3
"""Score the extract-rules skill against a human answer key.

Usage: score_skill.py [RULES_JSON ...] [--key eval/skill/answer-key.csv]
       [--pdf data/contract-rules.pdf] [--out eval/skill/report.md]

With no RULES_JSON, every eval/skill/runs/*/rules.json is scored.

The answer key (answer-key.csv) holds clauses sampled from the PDF itself, not
from the skill's output, so it can show what the skill missed. Per clause:
  is_rule          yes / no  (is there a testable rule here?)
  threshold_low    blank = not checked; "none" = must be empty; a number = must equal
  threshold_high   same
  approver_keyword blank = not checked; words that must appear in the rule's
                   approver; alternatives separated by |
  action_keyword   same, for the rule's required action

Five measures, per run:
  found            real rules the skill extracted            (recall)
  not invented     rules it produced where the key has none  (precision)
  fields right     thresholds, approver and action match the key
  quotes verified  verify_quotes.py passes
  consistent       the runs agree with each other (with two or more runs)
Exit 0 when every run meets the bar for found, not invented and quotes; 1 otherwise.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, csv, glob, itertools, json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERIFIER = ROOT / ".claude/skills/extract-rules/verify_quotes.py"
BAR = {"found": 0.90, "precision": 0.90, "fields": 0.85}


def norm_clause(c):
    return re.sub(r"\s+", " ", str(c or "")).strip().lower()


def matches(rule_clause, key_clause):
    """A rule belongs to a key clause if it is that clause or one of its sub-clauses (4.1 covers 4.1.2)."""
    r, k = norm_clause(rule_clause), norm_clause(key_clause)
    return r == k or r.startswith(k + ".")


def parent_of(key_clause):
    """The parent of a list item: 7.5.4 -> 7.5. None for anything else."""
    m = re.fullmatch(r"(\d+\.\d+)\.\d+", norm_clause(key_clause))
    return m.group(1) if m else None


def num(v):
    try:
        return float(str(v).replace(",", "").replace("£", ""))
    except (TypeError, ValueError):
        return None


def check_threshold(expected, actual):
    """None when not checked; True/False otherwise."""
    e = (expected or "").strip().lower()
    if not e:
        return None
    if e in ("none", "null", "-"):
        return actual is None
    # within 1 of the key: "above 1,000" may be stored as 1000 or 1001, "up to 25,000" as 24999.99
    return actual is not None and num(e) is not None and num(actual) is not None and abs(num(e) - num(actual)) <= 1


def check_keyword(expected, actual):
    e = (expected or "").strip()
    if not e:
        return None
    text = (actual or "").lower()
    return any(alt.strip().lower() in text for alt in e.split("|") if alt.strip())


def load_key(path):
    raw = Path(path).read_bytes()
    for enc in ("utf-8-sig", "mac_roman", "cp1252"):  # spreadsheets re-save in their own encoding
        try:
            text = raw.decode(enc); break
        except UnicodeDecodeError:
            continue
    import io
    rows = list(csv.DictReader(io.StringIO(text)))
    blank = [r["id"] for r in rows if (r.get("is_rule") or "").strip().lower() not in ("yes", "no")]
    return rows, blank


def score_run(rules_doc, key):
    rules = rules_doc.get("rules", [])
    excluded = rules_doc.get("excluded", [])
    res = {"tp": 0, "fn": 0, "fp": 0, "tn": 0, "unaccounted": 0, "fields_ok": 0, "fields_checked": 0, "rows": []}
    for k in key:
        want = k["is_rule"].strip().lower() == "yes"
        cand = [r for r in rules if matches(r.get("clause"), k["clause"])]
        in_excl = any(matches(x.get("clause"), k["clause"]) for x in excluded)
        # a list item the key calls a rule is also found when the skill holds the rule at the list's parent
        par = parent_of(k["clause"])
        if want and not cand and par:
            cand = [r for r in rules if norm_clause(r.get("clause")) == par]
        got = bool(cand)
        if not got and not in_excl:
            res["unaccounted"] += 1
        row = {"id": k["id"], "clause": k["clause"], "want": want, "got": got, "fields": []}
        if want and got:
            res["tp"] += 1
            # score fields against the best-matching candidate rule
            best, best_ok, best_n = None, -1, 0
            for r in cand:
                checks = [
                    ("threshold_low", check_threshold(k["threshold_low"], r.get("threshold_low"))),
                    ("threshold_high", check_threshold(k["threshold_high"], r.get("threshold_high"))),
                    ("approver", check_keyword(k["approver_keyword"], r.get("approver"))),
                    ("action", check_keyword(k["action_keyword"], r.get("required_action"))),
                ]
                checks = [(n, v) for n, v in checks if v is not None]
                ok = sum(1 for _, v in checks if v)
                if ok > best_ok:
                    best, best_ok, best_n = checks, ok, len(checks)
            res["fields_ok"] += best_ok
            res["fields_checked"] += best_n
            row["fields"] = [n for n, v in (best or []) if not v]
        elif want:
            res["fn"] += 1
        elif got:
            res["fp"] += 1
        else:
            res["tn"] += 1
        res["rows"].append(row)
    tp, fn, fp = res["tp"], res["fn"], res["fp"]
    res["found"] = tp / (tp + fn) if tp + fn else None
    res["precision"] = tp / (tp + fp) if tp + fp else None
    res["fields"] = res["fields_ok"] / res["fields_checked"] if res["fields_checked"] else None
    return res


def quotes_ok(rules_path, pdf):
    p = subprocess.run([sys.executable, str(VERIFIER), str(rules_path), str(pdf)], capture_output=True, text=True)
    last = (p.stdout.strip().splitlines() or ["(no output)"])[-1]
    return p.returncode == 0, last


def signature(rules_doc):
    """What 'the same rule set' means across runs: clause, type and thresholds."""
    return {(norm_clause(r.get("clause")), r.get("type"), num(r.get("threshold_low")), num(r.get("threshold_high")))
            for r in rules_doc.get("rules", [])}


def pct(x):
    return "n/a" if x is None else f"{x:.0%}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("rules", nargs="*")
    ap.add_argument("--key", default=str(ROOT / "eval/skill/answer-key.csv"))
    ap.add_argument("--pdf", default=str(ROOT / "data/contract-rules.pdf"))
    ap.add_argument("--out", default=str(ROOT / "eval/skill/report.md"))
    a = ap.parse_args()

    paths = [Path(p) for p in (a.rules or sorted(glob.glob(str(ROOT / "eval/skill/runs/*/rules.json"))))]
    if not paths:
        sys.exit("STOP: no runs to score. Run eval/skill/run_eval.sh, or pass a rules.json path.")
    key, blank = load_key(a.key)
    if blank:
        sys.exit(f"STOP: the answer key is not filled in: is_rule is blank or not yes/no for {', '.join(blank)}.")

    runs = []
    for p in paths:
        doc = json.loads(p.read_text())
        s = score_run(doc, key)
        s["quotes_ok"], s["quotes_line"] = quotes_ok(p, a.pdf)
        s["name"] = p.parent.name if p.name == "rules.json" else p.stem
        s["n_rules"], s["n_excluded"] = len(doc.get("rules", [])), len(doc.get("excluded", []))
        s["sig"] = signature(doc)
        runs.append(s)

    # consistency: pairwise agreement of rule sets, and of the verdict on each key clause
    cons, verdict_agree = None, None
    if len(runs) > 1:
        pairs = list(itertools.combinations(runs, 2))
        cons = sum(len(x["sig"] & y["sig"]) / len(x["sig"] | y["sig"]) for x, y in pairs if x["sig"] | y["sig"]) / len(pairs)
        same = sum(1 for i in range(len(key)) if len({r["rows"][i]["got"] for r in runs}) == 1)
        verdict_agree = same / len(key)

    n_yes = sum(1 for k in key if k["is_rule"].strip().lower() == "yes")
    lines = ["# extract-rules skill: evaluation", ""]
    lines += [
             f"Answer key: {len(key)} clauses sampled from the PDF ({n_yes} with a testable rule, {len(key) - n_yes} without). "
             f"Runs scored: {len(runs)}.", "",
             "| Run | Rules | Found (recall) | Not invented (precision) | Fields right | Quotes verified | Not accounted for |",
             "|---|---|---|---|---|---|---|"]
    for r in runs:
        lines.append(f"| {r['name']} | {r['n_rules']} | {pct(r['found'])} ({r['tp']}/{r['tp'] + r['fn']}) | "
                     f"{pct(r['precision'])} ({r['fp']} invented) | {pct(r['fields'])} ({r['fields_ok']}/{r['fields_checked']}) | "
                     f"{'yes' if r['quotes_ok'] else 'NO'} | {r['unaccounted']} |")
    lines += ["", f"**Consistent across runs:** "
              + ("needs two or more runs" if cons is None else f"rule sets agree {cons:.0%} on average; the verdict on each key clause agrees in {verdict_agree:.0%} of clauses"),
              "", f"Bar: found ≥ {BAR['found']:.0%}, not invented ≥ {BAR['precision']:.0%}, fields right ≥ {BAR['fields']:.0%}, quotes verified.",
              "", "## Misses, by run", ""]
    for r in runs:
        miss = [x for x in r["rows"] if x["want"] and not x["got"]]
        inv = [x for x in r["rows"] if not x["want"] and x["got"]]
        wrong = [x for x in r["rows"] if x["fields"]]
        lines.append(f"**{r['name']}**: "
                     + ("; ".join(filter(None, [
                         "missed " + ", ".join(f"{x['id']} ({x['clause']})" for x in miss) if miss else "",
                         "invented " + ", ".join(f"{x['id']} ({x['clause']})" for x in inv) if inv else "",
                         "wrong fields " + ", ".join(f"{x['id']} ({x['clause']}: {'/'.join(x['fields'])})" for x in wrong) if wrong else "",
                     ])) or "nothing missed, invented or wrong"))
        lines.append("")
    Path(a.out).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print("\n".join(lines))
    print(f"written: {a.out}")

    ok = all((r["found"] or 0) >= BAR["found"] and (r["precision"] if r["precision"] is not None else 1) >= BAR["precision"]
             and r["quotes_ok"] for r in runs)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
