#!/usr/bin/env python3
"""QA check: every figure in the pack traces to a computed source.

Scans outputs/planning-memo.md, risk-control-matrix.md and audit-program.md
for figures (three or more digits, or a £ amount). Each must be a value in
outputs/analytics.json, outputs/pack-figures.json, outputs/rules.json or one
of outputs/samples/*.csv. Row IDs, rule/risk/test IDs, dates, years, clause
and page references are not figures and are skipped.
Prints PASS/FAIL lines and a summary; exit 0 when clean.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import csv, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs"  # an outputs folder to check; default outputs/
DOCS = ["planning-memo.md", "risk-control-matrix.md", "audit-program.md"]
SKIP = [
    r"`[^`]*`",                      # code spans (row IDs, paths)
    r"\b[A-Za-z0-9_\-]+\.xlsx:\d+",  # bare row IDs
    r"\b(?:CPR|R|C|T)-\d+(?:\.\d+)?\b",
    r"\b\d{4}-\d{2}-\d{2}\b",        # dates
    r"\b(?:19|20)\d{2}\b",           # years
    r"\bp\.\s?\d+\b",                # page refs
    r"\bclause [\dA-Za-z. ]+",       # clause refs
    r"\[metric:[^\]]+\]",
]
NUM = re.compile(r"£\s?(\d[\d,]*(?:\.\d+)?)|(?<![\w.])(\d[\d,]*\d)(?![\w.])")


def walk(o, out):
    if isinstance(o, dict):
        for v in o.values(): walk(v, out)
    elif isinstance(o, list):
        for v in o: walk(v, out)
    elif isinstance(o, (int, float)) and not isinstance(o, bool):
        out.add(round(float(o), 2))
    elif isinstance(o, str):
        for m in re.finditer(r"\d[\d,]*(?:\.\d+)?", o):
            try: out.add(round(float(m.group(0).replace(",", "")), 2))
            except ValueError: pass


def main():
    allowed = set()
    IN = ROOT / "outputs"  # analytics and rules always come from the project
    for name in ("analytics.json", "pack-figures.json", "rules.json"):
        p = (OUT if name == "pack-figures.json" else IN) / name
        if p.exists(): walk(json.loads(p.read_text()), allowed)
    for p in (OUT / "samples").glob("*.csv"):
        with open(p, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                for v in row.values():
                    try: allowed.add(round(float(v), 2))
                    except (TypeError, ValueError): pass
    fails, checked = [], 0
    for name in DOCS:
        p = OUT / name
        if not p.exists():
            fails.append(f"{name} missing"); continue
        for ln, line in enumerate(p.read_text(encoding="utf-8").splitlines(), 1):
            text = line
            for pat in SKIP:
                text = re.sub(pat, " ", text)
            for m in NUM.finditer(text):
                raw = (m.group(1) or m.group(2)).replace(",", "")
                if len(re.sub(r"\D", "", raw)) < 3 and not m.group(1):
                    continue
                checked += 1
                try: val = round(float(raw), 2)
                except ValueError: continue
                if val not in allowed:
                    fails.append(f"{name}:{ln}: figure {m.group(0).strip()} not found in analytics, pack figures, rules or samples")
    for f in fails[:40]:
        print("FAIL ", f)
    if len(fails) > 40: print(f"FAIL  … and {len(fails) - 40} more")
    print(f"SUMMARY numbers: figures_checked={checked} allowed_values={len(allowed)} failures={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
