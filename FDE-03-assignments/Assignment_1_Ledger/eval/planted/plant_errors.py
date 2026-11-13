#!/usr/bin/env python3
"""Plant seven known mistakes in a COPY of your pack and confirm the QA checks catch each one.

Usage: python eval/planted/plant_errors.py

This is the fastest feedback loop for TODO #12 (check_trace.py): three of the
seven plants are only caught by the trace check. A check that always fails
does not help: the untouched pack must pass first ("baseline"), or nothing
counts. Nothing in outputs/ or data/ is changed; plants go into a temporary copy.

  1. A figure in the memo that no script produced           -> check_numbers.py
  2. A sampled payment that does not exist                    -> check_samples.py
  3. A sampled payment with its amount changed by £1          -> check_samples.py
  4. A challenge left open                                    -> check_trace.py
  5. A rule neither tested nor given a reason                 -> check_trace.py
  6. A risk planned that the auditor did not approve          -> check_trace.py
  7. A rule quote with one word changed                       -> verify_quotes.py

Writes reports/planted.json. Exit 0 when the baseline passes and 7 of 7 are caught.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import importlib.util, json, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location("team_eval", ROOT / "eval/team/run_eval.py")
team = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(team)


def main():
    pe = team.planted_errors()
    out = ROOT / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / "planted.json").write_text(json.dumps(pe, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Baseline (the untouched pack passes every check): {'yes' if pe['baseline_ready'] else 'NO'}")
    for t in pe["trials"][1:]:
        print(f"  [{'caught' if t['caught'] else 'MISSED'}] {t['plant']}  ({t['expect']}; got: {t['got']})")
    print(f"\n{pe['caught']} of {pe['planted']} planted errors caught.")
    if not pe["baseline_ready"]:
        print("The untouched pack does not pass yet, so no catch counts. Run scripts/checks/run_checks.py first.")
    print("written: reports/planted.json")
    return 0 if pe["baseline_ready"] and pe["caught"] == pe["planted"] else 1


if __name__ == "__main__":
    sys.exit(main())
