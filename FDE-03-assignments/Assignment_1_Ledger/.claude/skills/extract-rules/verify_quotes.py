#!/usr/bin/env python3
"""Verify outputs/rules.json against the Contract Rules PDF.

Usage: verify_quotes.py RULES_JSON PDF_PATH

Checks
  1. JSON parses and has the expected top-level keys.
  2. Every rule has the required fields with the right types.
  3. rule_ids are unique and sequential (CPR-01, CPR-02, ...).
  4. Every threshold_*_ref names a key in `parameters`.
  5. Every verbatim_quote appears in the PDF text after light normalisation
     (whitespace collapsed, page footers and bullet glyphs removed, quote/dash
     glyphs unified).
  6. The rule's `page` matches the page on which the quote was found.
  7. Every excluded entry has clause, page and reason.

Exit 0 and print ALL CHECKS PASSED when clean; exit 1 otherwise.
Requires poppler's `pdftotext` (found on PATH or via $PDFTOTEXT; Xpdf's is refused).
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

REQUIRED_FIELDS = {
    "rule_id": str,
    "clause": str,
    "page": int,
    "type": str,
    "scope": str,
    "condition": str,
    "threshold_low": (int, type(None)),
    "threshold_low_inclusive": (bool, type(None)),
    "threshold_high": (int, type(None)),
    "threshold_high_inclusive": (bool, type(None)),
    "required_action": (str, type(None)),
    "approver": (str, type(None)),
    "evidence_source": str,
    "verbatim_quote": str,
}
OPTIONAL_REF_FIELDS = ("threshold_low_ref", "threshold_high_ref")
TYPES = {"threshold", "required-action", "approver", "anti-avoidance"}
SCOPES = {"goods-services", "works-concession-light-touch", "all"}
EVIDENCE = {"spend-data", "contracts-register", "council-records"}

FOOTER_RE = re.compile(r"^\S+\.docx\s*\n\s*\n?\s*\d+\s*$", re.MULTILINE)
GLYPHS = str.maketrans({
    "‘": "'", "’": "'", "“": '"', "”": '"',
    "–": "-", "\u2014": "-", " ": " ",
})


def pdftotext_path() -> str:
    """The first pdftotext on PATH (or $PDFTOTEXT) whose banner says Poppler. Xpdf's pdftotext (shipped with
    Git for Windows) lays tables out differently, so quotes would not match: it is refused. Same logic as scripts/pdftext.py."""
    import os
    exe = "pdftotext.exe" if os.name == "nt" else "pdftotext"
    cands = [os.environ["PDFTOTEXT"]] if os.environ.get("PDFTOTEXT") else []
    cands += [os.path.join(d, exe) for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    for c in dict.fromkeys(cands):
        if not os.path.isfile(c):
            continue
        try:
            v = subprocess.run([c, "-v"], capture_output=True, text=True, errors="replace")
        except OSError:
            continue
        if "poppler" in (v.stdout + v.stderr).lower():
            return c
    sys.exit("ERROR: poppler's pdftotext not found (Xpdf's, shipped with Git for Windows, is refused). "
             "Install poppler (macOS: brew install poppler; Linux: apt install poppler-utils; "
             "Windows: winget install oschwartz10612.Poppler), or set PDFTOTEXT to its full path.")


def pdf_pages(pdf: Path) -> list[str]:
    out = subprocess.run([pdftotext_path(), "-enc", "UTF-8", str(pdf), "-"], capture_output=True, check=True).stdout
    pages = out.decode("utf-8", errors="replace").split("\f")
    if pages and not pages[-1].strip():
        pages.pop()
    return pages


BULLET_RE = re.compile(r"[\ue000-\uf8ff\u2022\u25aa\u25cf\u2043]")


def normalise(text: str) -> str:
    text = FOOTER_RE.sub(" ", text)
    text = text.translate(GLYPHS)
    text = BULLET_RE.sub(" ", text)
    return re.sub(r"\s+", " ", text).strip()


def main(rules_path: str, pdf_path: str) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        doc = json.loads(Path(rules_path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        print(f"ERROR: cannot read {rules_path}: {e}")
        return 1

    for key in ("source", "parameters", "notes", "rules", "excluded"):
        if key not in doc:
            errors.append(f"top-level key missing: {key}")
    rules = doc.get("rules", [])
    params = doc.get("parameters", {})
    excluded = doc.get("excluded", [])

    pages = [normalise(p) for p in pdf_pages(Path(pdf_path))]
    full = " ".join(pages)
    print(f"PDF: {len(pages)} pages, {len(full)} normalised chars")
    print(f"rules.json: {len(rules)} rules, {len(excluded)} excluded, {len(params)} parameters")

    seen_ids = set()
    for i, r in enumerate(rules, start=1):
        rid = r.get("rule_id", f"<rule #{i}>")
        for field, typ in REQUIRED_FIELDS.items():
            if field not in r:
                errors.append(f"{rid}: missing field '{field}'")
            elif not isinstance(r[field], typ) or (typ is int and isinstance(r[field], bool)):
                errors.append(f"{rid}: field '{field}' has wrong type {type(r[field]).__name__}")
        if rid in seen_ids:
            errors.append(f"{rid}: duplicate rule_id")
        seen_ids.add(rid)
        if rid != f"CPR-{i:02d}":
            errors.append(f"{rid}: expected CPR-{i:02d} at position {i} (ids must be sequential)")
        if r.get("type") not in TYPES:
            errors.append(f"{rid}: type '{r.get('type')}' not in {sorted(TYPES)}")
        if r.get("scope") not in SCOPES:
            errors.append(f"{rid}: scope '{r.get('scope')}' not in {sorted(SCOPES)}")
        if r.get("evidence_source") not in EVIDENCE:
            errors.append(f"{rid}: evidence_source '{r.get('evidence_source')}' not in {sorted(EVIDENCE)}")
        for ref in OPTIONAL_REF_FIELDS:
            val = r.get(ref)
            if val is not None and val not in params:
                errors.append(f"{rid}: {ref} '{val}' not declared in parameters")
            bound = ref.replace("_ref", "")
            if val is not None and r.get(bound) is not None:
                errors.append(f"{rid}: {bound} is numeric AND {ref} is set; use one or the other")
        lo, hi = r.get("threshold_low"), r.get("threshold_high")
        if isinstance(lo, int) and isinstance(hi, int) and lo >= hi:
            errors.append(f"{rid}: threshold_low {lo} >= threshold_high {hi}")

        quote = r.get("verbatim_quote")
        if isinstance(quote, str):
            q = normalise(quote)
            if len(q) < 20:
                errors.append(f"{rid}: quote too short to be a sentence ({len(q)} chars)")
            hits = [n for n, p in enumerate(pages, start=1) if q in p]
            if not hits:
                if q in full:
                    errors.append(f"{rid}: quote straddles a page boundary; shorten it to one page")
                else:
                    errors.append(f"{rid}: quote NOT FOUND in PDF text: {quote[:80]!r}…")
            else:
                page = r.get("page")
                if page not in hits:
                    errors.append(f"{rid}: page is {page} but quote found on page(s) {hits}")
                if len(hits) > 1:
                    warnings.append(f"{rid}: quote appears on several pages {hits}; page={page} accepted")

    for name, p in params.items():
        if not isinstance(p, dict) or "value" not in p or "description" not in p:
            errors.append(f"parameter {name}: needs 'value' and 'description'")
        elif p["value"] is not None:
            warnings.append(f"parameter {name}: has value {p['value']}; confirm the auditor supplied it with a source")

    for j, x in enumerate(excluded, start=1):
        for field in ("clause", "page", "reason"):
            if field not in x:
                errors.append(f"excluded #{j}: missing '{field}'")
        if isinstance(x.get("reason"), str) and len(x["reason"].strip()) < 8:
            errors.append(f"excluded #{j} ({x.get('clause')}): reason too short")

    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"FAIL  {e}")
    if errors:
        print(f"\n{len(errors)} failure(s), {len(warnings)} warning(s)")
        return 1
    print(f"\nALL CHECKS PASSED ({len(rules)} rules, {len(excluded)} excluded, {len(warnings)} warning(s))")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    sys.exit(main(sys.argv[1], sys.argv[2]))
