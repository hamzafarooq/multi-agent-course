#!/usr/bin/env python3
"""Where you are: the thirteen TODOs, the outputs they produce, and your tools. Your progress bar.

Usage: python scripts/status.py

Quick and read-only. It checks that files exist, that the JSON outputs match their
schemas in contract/, and that your tools are installed. It does not run the
verifiers or the evaluation: `python eval/run_all.py` does that.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import importlib.util, json, re, shutil, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs"
MARK = "TODO (YOU)"


def text(rel):
    p = ROOT / rel
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def written(rel):
    t = text(rel)
    return "missing" if not t else "open" if MARK in t else "written"


def decisions():
    rows = [c for c in ([x.strip() for x in l.strip().strip("|").split("|")] for l in text("outputs/auditor-comments.md").splitlines())
            if len(c) >= 6 and re.fullmatch(r"R-\d+", c[0])]
    if not rows:
        return "waiting (no register yet)"
    done = [c for c in rows if c[4].strip().lower() in ("approve", "amend", "reject")]
    return "done" if len(done) == len(rows) else f"open ({len(done)}/{len(rows)} decided)"


def team_setup():
    try:
        on = str((json.loads(text(".claude/settings.json") or "{}").get("env") or {}).get("CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS")) == "1"
    except json.JSONDecodeError:
        on = False
    lead = MARK not in text("CLAUDE.md")
    return "written" if on and lead else "open (" + ", ".join(x for x, ok in (("settings flag", on), ("lead procedure in CLAUDE.md", lead)) if not ok) + ")"


def trace():
    t = text("scripts/checks/check_trace.py")
    return "open" if 'NotImplementedError("TODO (YOU) #12' in t else "written"


def signed():
    m = re.search(r"^Signed off by:[ \t]*(\S.*)?$", text("outputs/review.md"), re.M)
    return "done" if m and m.group(1) else "waiting (no review yet)" if not text("outputs/review.md") else "open"


TODOS = [
    ("#1", "extract-rules skill", lambda: written(".claude/skills/extract-rules/SKILL.md")),
    ("#2", "spend-analyst sub-agent", lambda: written(".claude/agents/spend-analyst.md")),
    ("#3", "findings-analyst sub-agent", lambda: written(".claude/agents/findings-analyst.md")),
    ("#4", "risk-assessment skill", lambda: written(".claude/skills/risk-assessment/SKILL.md")),
    ("#5", "risk-assessor sub-agent", lambda: written(".claude/agents/risk-assessor.md")),
    ("#6", "you: decide every risk at the gate", decisions),
    ("#7", "agent teams on + the lead's procedure", team_setup),
    ("#8", "audit-program skill", lambda: written(".claude/skills/audit-program/SKILL.md")),
    ("#9", "planner teammate", lambda: written(".claude/agents/planner.md")),
    ("#10", "challenger teammate", lambda: written(".claude/agents/challenger.md")),
    ("#11", "qa-reviewer teammate", lambda: written(".claude/agents/qa-reviewer.md")),
    ("#12", "scripts/checks/check_trace.py", trace),
    ("#13", "you: sign off in outputs/review.md", signed),
]

OUTPUTS = [
    ("rules.json", "#1", "rules"), ("analytics.json", "#2", "analytics"), ("analytics-full/spend-clean.csv", "#2", None),
    ("analytics-full/selfcheck.json", "#2", None), ("history.json", "#3", "history"), ("risk-ratings.json", "#5", "risk-ratings"),
    ("risk-register.md", "#5", None), ("auditor-comments.md", "#5", None), ("audit-plan.json", "#9", "audit-plan"),
    ("planning-memo.md", "#9", None), ("challenges.md", "#10", None), ("review.md", "#11", None),
]


def schema_state(name, rel):
    try:
        from jsonschema import Draft202012Validator
    except ImportError:
        return "exists (jsonschema not installed)"
    try:
        doc = json.loads((OUT / rel).read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return f"INVALID JSON: {e}"
    schema = json.loads(text(f"contract/{name}.schema.json"))
    errs = sorted(Draft202012Validator(schema).iter_errors(doc), key=lambda e: list(e.path))
    return "valid" if not errs else f"{len(errs)} schema error(s); first: {'/'.join(map(str, errs[0].path)) or '(root)'}: {errs[0].message[:90]}"


def tools():
    rows = []
    for mod in ("pandas", "openpyxl", "jsonschema"):
        rows.append((mod, "ok" if importlib.util.find_spec(mod) else "MISSING: pip install -r requirements.txt"))
    spec = importlib.util.spec_from_file_location("pdftext", ROOT / "scripts/pdftext.py")
    pdftext = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(pdftext)
    try:
        rows.append(("poppler pdftotext", pdftext.pdftotext_path()))
    except SystemExit as e:
        rows.append(("poppler pdftotext", f"MISSING: {e}"[:160]))
    rows.append(("node (viewer, quality kit)", shutil.which("node") or "MISSING: install Node 18+"))
    rows.append(("claude (Claude Code)", shutil.which("claude") or "MISSING: install Claude Code"))
    return rows


def main():
    print("LEDGER status\n\n| TODO | What | State |\n|---|---|---|")
    states = []
    for n, what, fn in TODOS:
        s = fn()
        states.append((n, what, s))
        print(f"| {n} | {what} | {s} |")
    done = sum(1 for _, _, s in states if s in ("written", "done"))
    print(f"\n{done} of {len(TODOS)} done.\n\n| Output | From | State |\n|---|---|---|")
    for rel, todo, schema in OUTPUTS:
        p = OUT / rel
        st = "not built yet" if not p.exists() else schema_state(schema, rel) if schema else "exists"
        print(f"| outputs/{rel} | {todo} | {st} |")
    print("\n| Tool | State |\n|---|---|")
    for name, st in tools():
        print(f"| {name} | {st} |")
    parent = next((p for p in ROOT.parents if (p / "CLAUDE.md").exists()), None)
    if parent:
        print(f"\nWARNING: {parent / 'CLAUDE.md'} exists above this folder. Claude Code loads every CLAUDE.md up the tree, so "
              "another project's instructions (e.g. the course tutor's) will mix with Ledger's. Copy this folder into its own "
              "repository and open it there (README.md, Start here).")
    nxt = next(((n, w) for n, w, s in states if s not in ("written", "done")), None)
    if nxt:
        print(f"\nNext: TODO {nxt[0]}, {nxt[1]}. TECHNICAL.md has a section for it; SPEC.md has its requirements.")
    else:
        print("\nAll thirteen done. Next: python eval/build_report.py, then deploy (TECHNICAL.md, Submit).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
