#!/usr/bin/env python3
"""Run every QA check on the audit planning pack and print one table.

Runs check_quotes.py, check_numbers.py, check_trace.py and check_samples.py
with the same interpreter, prints each script's FAIL lines and SUMMARY line,
then a table of check | result | summary. Exit 0 only when every check passes.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CHECKS = ["check_quotes.py", "check_numbers.py", "check_trace.py", "check_samples.py"]


def main():
    results = []
    extra = sys.argv[1:2]  # optional outputs folder, passed to every check
    for name in CHECKS:
        p = subprocess.run([sys.executable, str(HERE / name), *extra], capture_output=True, text=True)
        lines = p.stdout.strip().splitlines()
        summary = next((l for l in lines if l.startswith("SUMMARY")), "(no summary)")
        print(f"== {name}")
        for l in lines:
            if l.startswith("FAIL") or l.startswith("SUMMARY") or l.startswith("verify_quotes"):
                print("   " + l)
        if p.returncode != 0 and not lines:
            print("   " + (p.stderr.strip().splitlines() or ["(no output)"])[-1])
        results.append((name.replace("check_", "").replace(".py", ""), "PASS" if p.returncode == 0 else "FAIL", summary.replace("SUMMARY ", "")))
    print("\n| Check | Result | Summary |\n|---|---|---|")
    for name, res, summ in results:
        print(f"| {name} | {res} | {summ} |")
    ok = all(r == "PASS" for _, r, _ in results)
    print(f"\nVERDICT: {'READY FOR SIGN-OFF' if ok else 'BLOCKED'} ({sum(1 for _, r, _ in results if r == 'PASS')}/{len(results)} checks pass)")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
