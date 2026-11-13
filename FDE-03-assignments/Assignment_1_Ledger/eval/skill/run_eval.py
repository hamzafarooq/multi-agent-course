#!/usr/bin/env python3
"""Evaluate the extract-rules skill without disturbing the project's outputs.

Usage: python eval/skill/run_eval.py [--runs N]          (default N = 2; 3 for your submission)
       python eval/skill/run_eval.py --score-only        (re-score the runs already saved)

Runs /extract-rules N times, each in a FRESH Claude Code session (no memory of
the last run), saves each result as eval/skill/runs/run-<n>/rules.json, puts the
project's own outputs/rules.json back, then scores every saved run against the
answer key with score_skill.py. Each run takes several minutes.

Why fresh sessions: a skill is judged on what it does from its instructions
alone. Repeating it shows whether the result is the skill or luck.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
ORIG = ROOT / "outputs/rules.json"
RUNS = ROOT / "eval/skill/runs"
BACKUP = RUNS / ".original-rules.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=2)
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    score = [sys.executable, str(ROOT / "eval/skill/score_skill.py")]
    if a.score_only:
        return subprocess.call(score, cwd=ROOT)

    if not ORIG.exists():
        sys.exit(f"STOP: {ORIG.relative_to(ROOT)} not found; nothing to protect. Run /extract-rules once first.")
    claude = shutil.which("claude")
    if not claude:
        sys.exit("STOP: the claude command is not on PATH.")
    if BACKUP.exists():
        sys.exit(f"STOP: {BACKUP.relative_to(ROOT)} exists, so an earlier evaluation did not finish. Check it, copy it to "
                 "outputs/rules.json if that is the original, delete it, and run again.")

    RUNS.mkdir(parents=True, exist_ok=True)
    shutil.copy(ORIG, BACKUP)
    last = max([int(m.group(1)) for p in RUNS.iterdir() if (m := re.fullmatch(r"run-(\d+)", p.name))] or [0])
    failed = 0
    try:
        for i in range(1, a.runs + 1):
            name = f"run-{last + i}"
            print(f"== {name}: running /extract-rules in a fresh session (this takes several minutes)", flush=True)
            ORIG.unlink(missing_ok=True)  # start from the PDF, not from an earlier answer
            log = RUNS / f"{name}.log"
            with open(log, "w", encoding="utf-8") as fh:
                subprocess.run([claude, "-p", "--no-session-persistence", "--permission-mode", "acceptEdits",
                                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep", "--", "/extract-rules"],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
            if ORIG.exists():
                (RUNS / name).mkdir(parents=True, exist_ok=True)
                shutil.copy(ORIG, RUNS / name / "rules.json")
                shutil.move(str(log), RUNS / name / "session.log")
                print(f"saved: eval/skill/runs/{name}/rules.json")
            else:
                print(f"FAILED: {name} produced no rules.json; see {log.relative_to(ROOT)}")
                failed += 1
    finally:
        shutil.copy(BACKUP, ORIG)
        BACKUP.unlink()
        print("restored: outputs/rules.json is the original again")

    print()
    status = subprocess.call(score, cwd=ROOT)
    if failed:
        print(f"{failed} run(s) failed to produce output.")
        return 1
    return status


if __name__ == "__main__":
    sys.exit(main())
