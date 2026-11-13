#!/usr/bin/env python3
"""Extract a PDF's text with poppler's pdftotext: the SAME engine the verifiers use.

Usage: python scripts/pdftext.py PDF OUT.txt            plain text (the source of truth for quotes)
       python scripts/pdftext.py PDF OUT.txt --layout   layout text (for reading tables only)
       python scripts/pdftext.py --which                 print the pdftotext this project will use

Pages are separated by form feeds (\\f); page N is the Nth chunk, starting at 1.

Why this exists. A quote is only "verbatim" relative to an extraction engine.
verify_quotes.py and verify_history.py read the PDFs with poppler's pdftotext
and nothing else. Git for Windows ships a DIFFERENT pdftotext (Xpdf 4), and
Claude Code's Bash tool on Windows finds Git's copy first; Xpdf lays tables out
differently, so quotes copied from its text fail verification. This script and
both verifiers search PATH for the poppler build and refuse Xpdf. Set
PDFTOTEXT=<full path> to point at a specific poppler pdftotext.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import os, subprocess, sys

INSTALL = ("poppler's pdftotext not found (Git for Windows ships Xpdf's pdftotext, which extracts tables differently "
           "and is refused). Install poppler: macOS `brew install poppler`; Debian/Ubuntu `sudo apt install poppler-utils`; "
           "Windows `winget install oschwartz10612.Poppler` (or `choco install poppler`, or `conda install -c conda-forge poppler`), "
           "then open a new terminal. Or set PDFTOTEXT to the full path of poppler's pdftotext.")


def pdftotext_path():
    """The first pdftotext on PATH (or $PDFTOTEXT) whose version banner says Poppler."""
    exe = "pdftotext.exe" if os.name == "nt" else "pdftotext"
    cands = [os.environ["PDFTOTEXT"]] if os.environ.get("PDFTOTEXT") else []
    cands += [os.path.join(d, exe) for d in os.environ.get("PATH", "").split(os.pathsep) if d]
    seen = set()
    for c in cands:
        if c in seen or not os.path.isfile(c):
            continue
        seen.add(c)
        try:
            v = subprocess.run([c, "-v"], capture_output=True, text=True, errors="replace")
        except OSError:
            continue
        if "poppler" in (v.stdout + v.stderr).lower():
            return c
    sys.exit("ERROR: " + INSTALL)


def pdf_text(pdf, layout=False):
    args = [pdftotext_path(), "-enc", "UTF-8"] + (["-layout"] if layout else []) + [str(pdf), "-"]
    return subprocess.run(args, capture_output=True, check=True).stdout.decode("utf-8", errors="replace")


def main():
    if "--which" in sys.argv:
        print(pdftotext_path())
        return 0
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if len(args) != 2:
        sys.exit(__doc__)
    text = pdf_text(args[0], layout="--layout" in sys.argv)
    with open(args[1], "w", encoding="utf-8", newline="\n") as f:
        f.write(text)
    print(f"{args[1]}: {text.count(chr(12)) + (0 if text.endswith(chr(12)) else 1)} pages, {len(text):,} characters")
    return 0


if __name__ == "__main__":
    sys.exit(main())
