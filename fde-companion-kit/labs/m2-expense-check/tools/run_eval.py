#!/usr/bin/env python3
"""Evaluate the extract-rules skill without losing your own outputs/rules.json.

Usage: python3 tools/run_eval.py [--runs N]      (default 3)
       python3 tools/run_eval.py --score-only    (score the runs already saved)

Runs /extract-rules N times, each in a fresh Claude Code session with no memory
of the last one, saves each result as runs/run-<n>/rules.json, puts your own
outputs/rules.json back, then scores every saved run with score_skill.py.
Each run takes a few minutes.

Why fresh sessions: a skill is judged on what it does from its instructions
alone. Running it again shows whether the result is the skill or luck.
"""
import argparse, re, shutil, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ORIG = ROOT / "outputs/rules.json"
RUNS = ROOT / "runs"
BACKUP = RUNS / ".original-rules.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--score-only", action="store_true")
    a = ap.parse_args()
    score = [sys.executable, str(ROOT / "tools/score_skill.py")]
    if a.score_only:
        return subprocess.call(score, cwd=ROOT)
    if not (ROOT / ".claude/skills/extract-rules/SKILL.md").exists():
        sys.exit("STOP: .claude/skills/extract-rules/SKILL.md not found. Write the skill first.")
    claude = shutil.which("claude")
    if not claude:
        sys.exit("STOP: the claude command is not on your PATH.")
    if BACKUP.exists():
        sys.exit(f"STOP: {BACKUP.relative_to(ROOT)} exists, so an earlier evaluation did not finish. "
                 "If it is your original, copy it to outputs/rules.json, delete it, and run again.")
    RUNS.mkdir(exist_ok=True)
    had_original = ORIG.exists()
    if had_original:
        shutil.copy(ORIG, BACKUP)
    last = max([int(m.group(1)) for p in RUNS.iterdir() if (m := re.fullmatch(r"run-(\d+)", p.name))] or [0])
    try:
        for i in range(1, a.runs + 1):
            name = f"run-{last + i}"
            print(f"== {name}: running /extract-rules in a fresh session (a few minutes)", flush=True)
            ORIG.unlink(missing_ok=True)
            start = time.time()
            with open(RUNS / f"{name}.log", "w", encoding="utf-8") as fh:
                subprocess.run([claude, "-p", "--no-session-persistence", "--permission-mode", "acceptEdits",
                                "--allowedTools", "Bash,Read,Write,Edit,Glob,Grep", "--", "/extract-rules"],
                               cwd=ROOT, stdout=fh, stderr=subprocess.STDOUT)
            took = time.time() - start
            if ORIG.exists():
                (RUNS / name).mkdir(exist_ok=True)
                shutil.move(str(ORIG), RUNS / name / "rules.json")
                print(f"   saved runs/{name}/rules.json ({took / 60:.1f} min)")
            else:
                print(f"   no outputs/rules.json written ({took / 60:.1f} min); see runs/{name}.log")
    finally:
        if had_original:
            shutil.copy(BACKUP, ORIG)
            BACKUP.unlink()
    return subprocess.call(score, cwd=ROOT)


if __name__ == "__main__":
    sys.exit(main())
