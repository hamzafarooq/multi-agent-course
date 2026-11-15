#!/usr/bin/env python3
"""Check the expense-checker's flags against the key.

Usage: python3 tools/check_flags.py [outputs/flags.csv]

outputs/flags.csv needs at least the columns claim_id and clause. A claim can break more than one rule: the key lists its clauses
separated by |. Reports the
claims it caught, the ones it missed, and false alarms (claims it flagged that
break no rule). Exit 0 when it caught every one with no false alarms.
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs/flags.csv"
    if not path.exists():
        sys.exit(f"STOP: {path} not found. Run the expense-checker first.")
    key = {r["claim_id"]: r for r in csv.DictReader(open(ROOT / "flags-key.csv", encoding="utf-8"))}
    flagged = {}
    for r in csv.DictReader(open(path, encoding="utf-8")):
        flagged.setdefault(r["claim_id"].strip(), set()).add(str(r.get("clause", "")).strip())
    caught = [c for c in key if c in flagged]
    missed = [c for c in key if c not in flagged]
    false = sorted(c for c in flagged if c not in key)
    wrong_clause = [c for c in caught if not set(key[c]["clause"].split("|")) <= flagged[c]]
    print(f"caught {len(caught)} of {len(key)} · false alarms {len(false)}")
    for c in missed:
        print(f"  missed {c}: {key[c]['why']}")
    for c in false:
        print(f"  false alarm {c} (clause {', '.join(sorted(flagged[c]))})")
    for c in wrong_clause:
        print(f"  {c} caught, but under clause {', '.join(sorted(flagged[c]))} rather than {key[c]['clause'].replace('|', ' and ')}")
    ok = not missed and not false
    print("PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
