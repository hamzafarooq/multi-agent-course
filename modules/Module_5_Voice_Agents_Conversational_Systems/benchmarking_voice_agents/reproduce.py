"""Run the whole benchmark end to end — gather, grade, and chart — in one command.

With the live stack up (see README section 5), `python reproduce.py` does everything:

    1. GATHER  — run BOTH architectures (cascade + s2s), writing raw runs to runs/<arch>/
                 (reseeds the DB to a clean baseline before/between passes)
    2. GRADE   — score every run: deterministic tools + LLM judge (accuracy + completeness)
    3. FINAL   — roll each arch up into a summary table
    4. COMPARE — build the comparison table image + charts

Usage:
    python reproduce.py               # full pipeline (servers MUST be up); resumes existing runs
    python reproduce.py --fresh       # clear old runs + grades, gather & judge everything anew
    python reproduce.py --grade-only  # skip gathering (no servers needed) — just re-grade the
                                      #   runs on disk and rebuild the tables/charts

Run it with the venv from requirements.txt active, so this one interpreter
(sys.executable) drives every step.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
PY = sys.executable
ARCHS = ("cascade", "s2s")


def run(title: str, *script_args: str) -> None:
    print(f"\n{'=' * 72}\n>>> {title}\n{'=' * 72}", flush=True)
    subprocess.run([PY, *script_args], cwd=HERE, check=True)


def main() -> None:
    ap = argparse.ArgumentParser(description="Run the voice-agent benchmark end to end.")
    ap.add_argument("--fresh", action="store_true",
                    help="delete existing runs + grades so everything is gathered & judged anew")
    ap.add_argument("--grade-only", action="store_true",
                    help="skip gathering (no servers needed); just grade existing runs + rebuild charts")
    ap.add_argument("--repeats", type=int, default=3, help="runs per query when gathering (default 3)")
    args = ap.parse_args()

    if args.fresh:
        for arch in ARCHS:
            base = HERE / "runs" / arch
            for f in base.glob("q*_r*.json"):
                f.unlink()
            graded = base / "final_metric" / "graded"
            if graded.exists():
                shutil.rmtree(graded)
        print("  --fresh: cleared existing runs + graded cache")

    # 1. GATHER — drive both servers (run_bench skips runs already on disk unless --fresh cleared them)
    if not args.grade_only:
        run("STEP 1/4 — gather runs from BOTH servers (reseed each pass)",
            "run_bench.py", "--arch", "both", "--reseed", "--repeats", str(args.repeats))

    # 2. GRADE — deterministic tools + LLM judge
    for arch in ARCHS:
        run(f"STEP 2/4 — grade {arch}  (deterministic tools + LLM judge)",
            "each_question_acc.py", "--arch", arch)

    # 3. FINAL — per-arch summary
    for arch in ARCHS:
        run(f"STEP 3/4 — roll up final metrics: {arch}", "final_metrics.py", "--arch", arch)

    # 4. COMPARE — cross-arch table + charts
    run("STEP 4/4 — comparison table + charts", "compare.py")

    print("\nDONE. Results:")
    print("  runs/<arch>/final_metric/  — per-question + final metrics (json/csv/md)")
    print("  comparison/                — comparison_table.png, comparison_chart.png, comparison_accuracy.png")


if __name__ == "__main__":
    main()
