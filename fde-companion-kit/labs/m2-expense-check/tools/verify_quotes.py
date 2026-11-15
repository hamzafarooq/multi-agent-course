#!/usr/bin/env python3
"""Check outputs/rules.json against policy.md.

Usage: python3 tools/verify_quotes.py [outputs/rules.json] [policy.md]

Checks: every quote appears word for word in the policy; every numbered clause
in the policy is in exactly one of rules or excluded; no clause is invented;
every rule has the fields schema.json lists; thresholds are numbers or null;
parameters are never filled in. Prints ALL CHECKS PASSED, or each problem.
"""
import json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIELDS = ["rule_id", "clause", "quote", "threshold_low", "threshold_high", "inclusive", "unit", "approver", "action", "parameters"]


def squash(s):
    return re.sub(r"\s+", " ", s).strip()


def main():
    rules_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs/rules.json"
    policy_path = Path(sys.argv[2]) if len(sys.argv) > 2 else ROOT / "policy.md"
    if not rules_path.exists():
        sys.exit(f"STOP: {rules_path} not found. Run /extract-rules first.")
    policy = policy_path.read_text(encoding="utf-8")
    text = squash(policy)
    clauses = re.findall(r"^(\d+\.\d+)\s", policy, flags=re.M)
    try:
        data = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        sys.exit(f"FAIL: {rules_path} is not valid JSON: {e}")
    problems = []
    rules, excluded = data.get("rules", []), data.get("excluded", [])
    for i, r in enumerate(rules):
        rid = r.get("rule_id", f"rule {i + 1}")
        missing = [f for f in FIELDS if f not in r]
        if missing:
            problems.append(f"{rid}: missing fields {', '.join(missing)}")
        q = squash(str(r.get("quote", "")))
        if not q:
            problems.append(f"{rid}: empty quote")
        elif q not in text:
            problems.append(f"{rid}: quote not found word for word in the policy: \"{q[:80]}\"")
        for f in ("threshold_low", "threshold_high"):
            v = r.get(f)
            if v is not None and not isinstance(v, (int, float)):
                problems.append(f"{rid}: {f} must be a number or null, not {v!r}")
        for k, v in (r.get("parameters") or {}).items():
            if v is not None:
                problems.append(f"{rid}: parameter {k} has a value ({v!r}); the policy does not give it, so it must be null")
    in_rules = {str(r.get("clause")) for r in rules}
    in_excluded = [str(e.get("clause")) for e in excluded]
    for e in excluded:
        if not str(e.get("reason", "")).strip():
            problems.append(f"excluded {e.get('clause')}: no reason given")
    for c in clauses:
        if c in in_rules and c in in_excluded:
            problems.append(f"clause {c}: in both rules and excluded")
        elif c not in in_rules and c not in in_excluded:
            problems.append(f"clause {c}: in neither rules nor excluded")
    for c in sorted(in_rules | set(in_excluded)):
        if c not in clauses:
            problems.append(f"clause {c}: not in the policy")
    dup = {c for c in in_excluded if in_excluded.count(c) > 1}
    for c in sorted(dup):
        problems.append(f"clause {c}: excluded more than once")
    print(f"{len(rules)} rules, {len(excluded)} excluded, {len(clauses)} clauses in the policy")
    if problems:
        print(f"{len(problems)} problem(s):")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
