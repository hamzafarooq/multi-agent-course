#!/usr/bin/env python3
"""Grader: re-derive a deployed Ledger's evaluation from what it published, and compare.

Usage: python eval/grade_url.py https://student-ledger.vercel.app [--keep]

Run from the course's own copy of the assignment (provided files untouched). It:
  1. downloads /data/manifest.json, every file it lists, and /evals/report.json;
  2. builds a temporary project from THIS folder's provided files (data, verifiers,
     builders, checks, eval) plus the student's published outputs, skill runs,
     harness files and check_trace.py; the student's own copies of the provided
     tools are never used, so editing them gains nothing;
  3. restores the pseudonymised supplier names from the council's workbooks
     (SUP-<letters> is recomputed from every supplier name in data/spend/), which
     is itself a check: a sampled payment whose token matches no supplier fails;
  4. re-runs eval/run_all.py there and re-scores the automated rubric with the
     same code as eval/build_report.py;
  5. compares every row and headline number with the published report.json.

A published number the re-run does not reproduce is FABRICATED (automatic fail).
Two inputs cannot be re-derived from a URL and are marked SELF-REPORTED: teamwork
and the per-run budgets (both read Claude Code transcripts on the student's
machine). Check them against the trajectories and the video.
Writes reports/grade-<host>.md and .json. Exit 0 when nothing is fabricated.
"""
import os as _os, subprocess as _sp, sys as _sys
if __name__ == "__main__" and _os.name == "nt" and not _sys.flags.utf8_mode:  # Windows: rerun in UTF-8 mode
    _sys.exit(_sp.call([_sys.executable, "-X", "utf8", *_sys.argv]))  # (£, →, curly quotes in the data)
import argparse, hashlib, importlib.util, json, os, re, shutil, subprocess, sys, tempfile, urllib.parse, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location("build_report", ROOT / "eval/build_report.py")
br = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(br)

PROVIDED_DIRS = ["data", "contract", "quality", "benchmark"]
PROVIDED_FILES = ["expectations.json", "DESIGN.template.md", "scripts/verify_history.py", "scripts/pdftext.py",
                  "scripts/checks/run_checks.py", "scripts/checks/check_quotes.py", "scripts/checks/check_numbers.py",
                  "scripts/checks/check_samples.py", ".claude/skills/extract-rules/verify_quotes.py",
                  ".claude/skills/risk-assessment/build_register.py", ".claude/skills/audit-program/build_pack.py"]
SELF_REPORTED = {"teamwork"}  # harness_hygiene is partly self-reported: items 4 and 5 (quality kit, budgets)


def token(name):
    h = hashlib.sha256(name.strip().encode("utf-8")).hexdigest()[:10]
    return "SUP-" + "".join(chr(97 + int(c, 16)) for c in h)


def fetch(url, binary=False):
    req = urllib.request.Request(url, headers={"User-Agent": "ledger-grader/1.0", "Cache-Control": "no-cache"})
    with urllib.request.urlopen(req, timeout=60) as r:
        b = r.read()
    return b if binary else b.decode("utf-8")


def supplier_names():
    """Every supplier name in the council's workbooks (the 'Supplier name' column of 'Data to publish')."""
    import openpyxl
    names = set()
    for f in sorted((ROOT / "data/spend").glob("*.xlsx")):
        ws = openpyxl.load_workbook(f, read_only=True, data_only=True)["Data to publish"]
        col = None
        for row in ws.iter_rows(values_only=True):
            if col is None:
                if row and "Supplier name" in [str(c).strip() if c is not None else "" for c in row]:
                    col = [str(c).strip() if c is not None else "" for c in row].index("Supplier name")
                continue
            if col < len(row) and row[col] is not None:
                names.add(str(row[col]).strip())
    return names


def build_project(base, tmp):
    proj = Path(tmp) / "project"
    for d in PROVIDED_DIRS:
        shutil.copytree(ROOT / d, proj / d)
    shutil.copytree(ROOT / "eval", proj / "eval", ignore=shutil.ignore_patterns("runs", "judgements", "results.json", "__pycache__"))
    for f in PROVIDED_FILES:
        if (ROOT / f).exists():
            (proj / f).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / f, proj / f)
    manifest = json.loads(fetch(base + "/data/manifest.json"))
    pub = Path(tmp) / "published"
    for item in manifest["files"]:
        dest = pub / item["path"]
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(fetch(base + "/" + urllib.parse.quote(item["path"]), binary=True))
    data = pub / "data"
    if (data / "outputs").is_dir():
        shutil.copytree(data / "outputs", proj / "outputs")
    for f in (data / "eval/skill-runs").glob("*.json") if (data / "eval/skill-runs").is_dir() else []:
        (proj / "eval/skill/runs" / f.stem).mkdir(parents=True, exist_ok=True)
        shutil.copy(f, proj / "eval/skill/runs" / f.stem / "rules.json")
    h = data / "harness"
    for src, dst in [(h / "claude", proj / ".claude"), (h / "scripts", proj / "scripts")]:
        if src.is_dir():
            shutil.copytree(src, dst, dirs_exist_ok=True)
    for f in ("CLAUDE.md",):
        if (h / f).exists():
            shutil.copy(h / f, proj / f)
    for f in ("DESIGN.md", "trajectories.md"):
        if (data / f).exists():
            shutil.copy(data / f, proj / f)
    if (data / "runs").is_dir():
        shutil.copytree(data / "runs", proj / "runs")
    # never trust a published copy of a provided tool: put the course's versions back on top
    for f in PROVIDED_FILES:
        if (ROOT / f).exists():
            shutil.copy(ROOT / f, proj / f)
    return proj, manifest


def restore_names(proj):
    rev = {token(n): n for n in supplier_names()}
    unknown = set()
    rx = re.compile(r"SUP-[a-p]{10}")

    def sub(m):
        if m.group(0) in rev:
            return rev[m.group(0)]
        unknown.add(m.group(0))
        return m.group(0)

    for p in (proj / "outputs").rglob("*"):
        if p.is_file() and p.suffix in (".json", ".md", ".csv"):
            t = p.read_text(encoding="utf-8")
            if "SUP-" in t:
                p.write_text(rx.sub(sub, t), encoding="utf-8")
    return len(rev), sorted(unknown)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("--keep", action="store_true", help="keep the rebuilt project for inspection")
    a = ap.parse_args()
    base = a.url.rstrip("/")
    host = urllib.parse.urlparse(base).netloc or "local"
    claimed = json.loads(fetch(base + "/evals/report.json"))

    tmp = tempfile.mkdtemp(prefix="ledger-grade-")
    try:
        proj, manifest = build_project(base, tmp)
        n_names, unknown = restore_names(proj)
        env = dict(os.environ, LEDGER_TRANSCRIPTS=str(Path(tmp) / "no-transcripts"), LEDGER_GRADER="1")
        print("re-running the whole-system eval on the published outputs (a few minutes) ...", flush=True)
        code, text = br.run([sys.executable, "eval/run_all.py"], proj, env=env)
        system = br.read_json(proj / "reports/system.json")
        if not system:
            sys.exit("STOP: the re-run produced no system.json:\n" + text[-1500:])
        # transcript-derived parts cannot be re-derived from a URL: carry the claim, marked as such
        system["teamwork"] = (claimed.get("system") or {}).get("teamwork")
        system["value_added"] = (claimed.get("system") or {}).get("value_added")
        quality_claimed = claimed.get("quality") if isinstance(claimed.get("quality"), dict) and "results" in claimed.get("quality", {}) else None
        regraded = br.assemble(proj, system, quality_claimed, {k: claimed.get(k, "") for k in ("student", "video", "url")})
        if a.keep:
            print(f"kept: {proj}")
    finally:
        if not a.keep:
            shutil.rmtree(tmp, ignore_errors=True)

    rows, fabricated = [], []
    claim_rows = {r["id"]: r for r in claimed.get("rubric", {}).get("automated", [])}
    for r in regraded["rubric"]["automated"]:
        c = claim_rows.get(r["id"], {})
        same = c.get("awarded") == r["awarded"]
        kind = "self-reported" if r["id"] in SELF_REPORTED else ("match" if same else "FABRICATED")
        if kind == "FABRICATED":
            fabricated.append(f"{r['id']}: published {c.get('awarded')}, re-run {r['awarded']}")
        rows.append((r["id"], r["points"], c.get("awarded"), r["awarded"], kind, "; ".join(e for e in r["evidence"] if e)[:220]))

    def headline(rep):
        s = rep.get("system") or {}
        sk, gt, pe = s.get("skill") or {}, s.get("golden_thread") or {}, s.get("planted_errors") or {}
        return {"skill found": sk.get("found"), "skill not invented": sk.get("precision"), "skill fields right": sk.get("fields"),
                "skill runs": len(sk.get("runs") or []), "pipeline checks passed": sum(1 for g in s.get("gates", []) if g["pass"] and g["stage"] != "Pack (rendered)"),
                "golden thread complete": gt.get("complete"), "golden thread total": gt.get("total"),
                "planted errors caught": pe.get("caught"), "untouched pack passes": pe.get("baseline_ready")}
    hc, hr = headline(claimed), headline(regraded)
    nums = []
    for k in hr:
        ok = (hc.get(k) == hr[k]) or (isinstance(hc.get(k), float) and isinstance(hr[k], float) and abs(hc[k] - hr[k]) < 1e-9)
        if not ok:
            fabricated.append(f"{k}: published {hc.get(k)}, re-run {hr[k]}")
        nums.append((k, hc.get(k), hr[k], "match" if ok else "FABRICATED"))

    auto = sum(r["awarded"] for r in regraded["rubric"]["automated"])
    md = [f"# Ledger grade: {claimed.get('student') or host}", "", f"URL: {base}  ", f"Report generated: {claimed.get('generatedAt')}  ",
          f"Published files: {len(manifest['files'])}; supplier tokens restored from {n_names:,} workbook names"
          + (f"; **{len(unknown)} token(s) match no supplier in the workbooks**" if unknown else ""), "",
          f"**Automated, as re-derived: {auto:g} / {regraded['score']['automatedMax']}** (published: {claimed.get('score', {}).get('automated')})", "",
          f"**Verdict: {'FABRICATED NUMBERS: automatic fail' if fabricated else 'every re-derivable number reproduced'}**", ""]
    md += ["| Row | Points | Published | Re-run | Result | Evidence (re-run) |", "|---|---|---|---|---|---|"]
    md += [f"| {i} | {p} | {c} | {r:g} | {k} | {e.replace('|', '/')} |" for i, p, c, r, k, e in rows]
    md += ["", "| Headline number | Published | Re-run | Result |", "|---|---|---|---|"] + [f"| {k} | {c} | {r} | {res} |" for k, c, r, res in nums]
    pack_line = next((g["detail"] for g in (regraded["system"].get("gates") or []) if g["stage"] == "Pack"), "")
    m = re.search(r"sampled transactions: (\d+)", pack_line)
    pub = ((claimed.get("system") or {}).get("golden_thread") or {}).get("total")
    if m and pub is not None and int(m.group(1)) != pub:
        md += ["", f"Note: a fresh redraw here gives {m.group(1)} sampled payments against {pub} published. Recipes that filter "
               "`supplier_norm` by pattern (where_not_match) cannot match pseudonymised names, so the redraw differs; this is expected "
               "and not scored. The published samples themselves were verified payment by payment against the workbooks above."]
    md += ["", "Self-reported (transcripts on the student's machine): teamwork, and harness_hygiene items 4-5 (quality kit, per-agent budgets). "
           "Check them against the trajectories and the video.", "",
           "Manual rows (design, trajectories, auditor_judgment, video_demo) are yours: read /evals."]
    if fabricated:
        md += ["", "## Not reproduced", ""] + [f"- {f}" for f in fabricated]
    out = ROOT / "reports"
    out.mkdir(exist_ok=True)
    safe = re.sub(r"[^A-Za-z0-9.-]", "_", host)
    (out / f"grade-{safe}.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (out / f"grade-{safe}.json").write_text(json.dumps({"url": base, "fabricated": fabricated, "rows": rows, "headline": nums,
                                                         "unknown_tokens": unknown, "automated": auto}, indent=2, default=str) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwritten: reports/grade-{safe}.md")
    return 1 if fabricated else 0


if __name__ == "__main__":
    sys.exit(main())
