#!/usr/bin/env python3
"""Score the extract-rules skill against the answer key.

Usage: python3 tools/score_skill.py [RULES_JSON ...]

With no RULES_JSON, every runs/run-*/rules.json is scored. The answer key
(answer-key.csv) holds 14 clauses picked from the policy itself, not from the
skill's output, so it can show what the skill missed. Per clause:
  is_rule          yes / no: is there a rule you could test a claim against?
  threshold_low    blank = not checked; none = must be empty; a number = must equal
  threshold_high   the same; alternatives separated by |
  approver_keyword blank = not checked; words that must appear in the approver
  action_keyword   the same, for the action

Three numbers per run:
  found         the key's real rules that the skill turned into rules
  not invented  of the key clauses the skill turned into rules, the share that are real rules
  fields right  thresholds, approver and action that match the key
Plus: quotes verified (tools/verify_quotes.py) and, with two or more runs,
how often the runs agree. Exit 0 when the weakest run meets every bar.
"""
import csv, glob, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BAR = {"found": 0.90, "not_invented": 0.90, "fields_right": 0.85}


def matching(rules, clause):
    return [r for r in rules if str(r.get("clause", "")).strip() == clause or str(r.get("clause", "")).startswith(clause + ".")]


def threshold_ok(expected, rules, field):
    vals = [r.get(field) for r in rules]
    if expected == "none":
        return any(v is None for v in vals)
    wanted = {float(x) for x in expected.split("|")}
    return any(isinstance(v, (int, float)) and float(v) in wanted for v in vals)


def words_ok(expected, rules, field):
    alts = [a.strip().lower() for a in expected.split("|")]
    return any(a in str(r.get(field) or "").lower() for r in rules for a in alts)


def score(path, key):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    rules = data.get("rules", [])
    real = [k for k in key if k["is_rule"] == "yes"]
    turned = [k for k in key if matching(rules, k["clause"])]
    found = [k for k in real if matching(rules, k["clause"])]
    checks, passed, misses = 0, 0, []
    for k in found:
        m = matching(rules, k["clause"])
        for field, test in (("threshold_low", threshold_ok), ("threshold_high", threshold_ok),
                            ("approver_keyword", words_ok), ("action_keyword", words_ok)):
            exp = k[field].strip()
            if not exp:
                continue
            target = field.replace("_keyword", "")
            checks += 1
            if test(exp, m, target):
                passed += 1
            else:
                misses.append(f"{k['clause']} {target}: expected {exp}, got {[r.get(target) for r in m]}")
    verified = subprocess.run([sys.executable, str(ROOT / "tools/verify_quotes.py"), str(path)],
                              capture_output=True, text=True).returncode == 0
    return {
        "found": len(found) / len(real),
        "not_invented": (sum(k["is_rule"] == "yes" for k in turned) / len(turned)) if turned else 0.0,
        "fields_right": passed / checks if checks else 0.0,
        "quotes_verified": verified,
        "missed": [k["clause"] for k in real if k not in found],
        "invented": [k["clause"] for k in turned if k["is_rule"] == "no"],
        "field_misses": misses,
        "rule_clauses": {k["clause"] for k in turned},
    }


def main():
    key = list(csv.DictReader(open(ROOT / "answer-key.csv", encoding="utf-8")))
    paths = sys.argv[1:] or sorted(glob.glob(str(ROOT / "runs/run-*/rules.json")))
    if not paths:
        sys.exit("STOP: no runs to score. Run python3 tools/run_eval.py first, or pass a rules.json.")
    results = []
    for p in paths:
        s = score(p, key)
        results.append(s)
        print(f"{Path(p).parent.name if 'runs' in p else p}: found {s['found']:.0%} · not invented {s['not_invented']:.0%} · "
              f"fields right {s['fields_right']:.0%} · quotes {'verified' if s['quotes_verified'] else 'FAILED'}")
        for label, items in (("missed", s["missed"]), ("invented", s["invented"]), ("wrong field", s["field_misses"])):
            for it in items:
                print(f"    {label}: {it}")
    if len(results) > 1:
        agree = sum(len({k["clause"] in r["rule_clauses"] for r in results}) == 1 for k in key)
        print(f"consistent: the runs agree on {agree} of {len(key)} key clauses")
    weakest = {m: min(r[m] for r in results) for m in BAR}
    ok = all(weakest[m] >= BAR[m] for m in BAR) and all(r["quotes_verified"] for r in results)
    print("weakest run: " + " · ".join(f"{m.replace('_', ' ')} {weakest[m]:.0%} (bar {BAR[m]:.0%})" for m in BAR))
    print("PASS: every bar met" if ok else "FAIL: below a bar, or a quote did not verify")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
