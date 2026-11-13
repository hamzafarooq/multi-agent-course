#!/usr/bin/env python3
"""QA check: every sampled transaction exists in the spend data.

For every row in outputs/samples/T-*.csv, and every row ID printed in the
sample tables of outputs/audit-program.md:
1. the row_id is in outputs/analytics-full/spend-clean.csv with the same
   supplier and amount;
2. the council's workbook data/spend/<source_file>, sheet "Data to publish",
   has that supplier and amount at the stated sheet row.
Prints PASS/FAIL lines and a summary; exit 0 when clean.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import csv, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "outputs"  # an outputs folder to check; default outputs/
SPEND = ROOT / "data/spend"
FULL = ROOT / "outputs/analytics-full"  # the cleaned spend always comes from the project


def money(v):
    try: return round(float(str(v).replace(",", "").replace("£", "")), 2)
    except (TypeError, ValueError): return None


def load_workbook_rows(name, cache):
    """{sheet_row: {column: value}} for the workbook's data sheet, header found by name."""
    if name in cache: return cache[name]
    import openpyxl
    path = SPEND / name
    if not path.exists():
        cache[name] = None; return None
    wb = openpyxl.load_workbook(path, read_only=True, data_only=True)
    ws = wb["Data to publish"] if "Data to publish" in wb.sheetnames else wb[wb.sheetnames[0]]
    rows, header = {}, None
    for i, row in enumerate(ws.iter_rows(values_only=True), 1):
        vals = ["" if v is None else str(v).strip() for v in row]
        if header is None:
            if "Supplier name" in vals and "Net amount" in vals:
                header = vals
            continue
        rows[i] = dict(zip(header, vals))
    wb.close()
    cache[name] = rows
    return rows


def main():
    fails, checked = [], 0
    spend = {}
    with open(FULL / "spend-clean.csv", newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            spend[r["row_id"]] = r
    items = []
    for p in sorted((OUT / "samples").glob("T-*.csv")):
        with open(p, newline="", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                items.append((p.name, r["row_id"], r.get("supplier", ""), r.get("amount", "")))
    sampled_ids = {i[1] for i in items}
    program = (OUT / "audit-program.md").read_text(encoding="utf-8") if (OUT / "audit-program.md").exists() else ""
    program_ids = set(re.findall(r"`([^`]+\.xlsx:\d+)`", program))
    for rid in sorted(program_ids - sampled_ids):
        fails.append(f"audit-program.md lists {rid} but no sample file holds it")
    cache = {}
    for where, rid, sup, amt in items:
        checked += 1
        s = spend.get(rid)
        if not s:
            fails.append(f"{where}: {rid} not in spend-clean.csv"); continue
        if s.get("Supplier name", "").strip() != sup.strip() or money(s.get("Net amount")) != money(amt):
            fails.append(f"{where}: {rid} supplier/amount differ from spend-clean.csv")
        src, _, row = rid.rpartition(":")
        rows = load_workbook_rows(src, cache)
        if rows is None:
            fails.append(f"{where}: workbook {src} not found"); continue
        wrow = rows.get(int(row))
        if not wrow:
            fails.append(f"{where}: {rid}: row {row} not in workbook"); continue
        if wrow.get("Supplier name", "").strip() != sup.strip() or money(wrow.get("Net amount")) != money(amt):
            fails.append(f"{where}: {rid}: workbook row {row} has a different supplier or amount")
    for f in fails[:40]: print("FAIL ", f)
    if len(fails) > 40: print(f"FAIL  … and {len(fails) - 40} more")
    print(f"SUMMARY samples: transactions_checked={checked} in_program={len(program_ids)} workbooks={len([k for k, v in cache.items() if v])} failures={len(fails)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
