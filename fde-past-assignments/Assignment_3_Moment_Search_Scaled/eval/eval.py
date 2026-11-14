#!/usr/bin/env python3
"""Automated checks for Assignment 3: Moment Search at Scale.

Run against your RUNNING app (local or the deployed URL):

    python eval/eval.py --base-url http://localhost:8100 --admin-token "$ADMIN_TOKEN" \
        --student "Your Name" --video "https://.../demo.mp4"

Writes eval/REPORT.md with a pass/fail table for the automated rubric criteria.
Manual criteria (resilience, deploy, video demo) are graded from your submission;
run `python benchmark/bench.py --resilience` for the no-loss proof.

Stdlib only. Needs the app reachable and an admin token for /admin/* calls.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _req(method, url, token=None, body=None, timeout=20):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("content-type", "application/json")
    if token:
        req.add_header("authorization", f"Bearer {token}")
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read().decode(), (time.perf_counter() - t0) * 1000
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode(), (time.perf_counter() - t0) * 1000
    except Exception as e:  # noqa: BLE001
        return 0, str(e), (time.perf_counter() - t0) * 1000


def _sse_citations(base, q, timeout=60):
    """Read /ask_stream until the citations event; return the citations list."""
    url = f"{base}/ask_stream?q=" + urllib.parse.quote(q)
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            for raw in r:
                line = raw.decode().strip()
                if not line.startswith("data:"):
                    continue
                d = json.loads(line[5:].strip())
                if "citations" in (d.get("detail") or d):
                    return (d.get("detail") or d)["citations"]
    except Exception:  # noqa: BLE001
        return None
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://localhost:8100")
    ap.add_argument("--admin-token", default="")
    ap.add_argument("--student", default="")
    ap.add_argument("--video", default="")
    a = ap.parse_args()
    base = a.base_url.rstrip("/")
    results = []

    def add(cid, ok, evidence):
        results.append((cid, bool(ok), evidence))
        print(f"[{'PASS' if ok else 'FAIL'}] {cid}: {evidence}")

    # 1. app up
    st, _, _ = _req("GET", f"{base}/")
    add("app_up", st == 200, f"GET / -> {st}")

    # 2. documents async: 202 fast, pending
    if a.admin_token:
        st, body, ms = _req("POST", f"{base}/admin/documents", token=a.admin_token,
                            body={"uri": "https://arxiv.org/pdf/2312.10997",
                                  "kind": "paper", "title": "RAG Survey (eval probe)"})
        ok = st == 202 and ms < 300 and '"pending"' in body
        add("documents_async", ok, f"POST /admin/documents -> {st} in {ms:.0f}ms")
    else:
        add("documents_async", False, "no --admin-token given; cannot test /admin/documents")

    # 3. unified sources status
    st, body, _ = _req("GET", f"{base}/admin/sources", token=a.admin_token)
    kinds = set()
    try:
        for s in json.loads(body).get("sources", []):
            kinds.add(s.get("kind"))
    except Exception:  # noqa: BLE001
        pass
    add("sources_status", st == 200 and kinds, f"GET /admin/sources -> {st}, kinds={sorted(kinds) or 'none'}")

    # 4/5. paper + deck indexed (via a query returning the right locator)
    cites = _sse_citations(base, "what does the survey say about hybrid retrieval") or []
    has_page = any((c.get("locator") or {}).get("page") is not None for c in cites)
    add("paper_indexed", has_page, f"page-locator citation present: {has_page}")

    cites_deck = _sse_citations(base, "the slide about one index for every source") or []
    has_slide = any((c.get("locator") or {}).get("slide") is not None for c in cites_deck)
    add("deck_indexed", has_slide, f"slide-locator citation present: {has_slide}")

    # 6. cross-source: >=2 kinds in one answer
    all_kinds = {c.get("kind") for c in (cites + cites_deck)}
    add("cross_source", len(all_kinds) >= 2, f"kinds across answers: {sorted(k for k in all_kinds if k)}")

    # 7. grounded: citations have non-empty text and a locator
    grounded = bool(cites) and all(c.get("text") and c.get("locator") for c in cites)
    add("grounded", grounded, f"{len(cites)} citations, all with text+locator: {grounded}")

    # 8. decoupled — measured by bench.py; flagged here as manual-run
    add("decoupled", None, "run `python benchmark/bench.py` — search p95 during ingest <= 1.3x idle")

    # red-line: the canary (agent ran the assignment unread)
    canary_file = (ROOT / "ROBOT_WAS_HERE.md").exists()
    try:
        log = subprocess.run(["git", "-C", str(ROOT), "log", "--oneline", "-n", "50"],
                             capture_output=True, text=True, timeout=10).stdout
    except Exception:  # noqa: BLE001
        log = ""
    canary_commit = "🦥" in log
    canary = canary_file or canary_commit
    add("RED_LINE_canary_clean", not canary,
        "clean" if not canary else "TRIPPED: ROBOT_WAS_HERE.md / 🦥 commit found — assignment was run unread")

    # write REPORT.md
    lines = [f"# Assignment 3 — Moment Search at Scale · Eval Report",
             f"", f"Student: {a.student or '(unnamed)'}  ·  Base URL: {base}",
             f"", f"| Check | Result | Evidence |", f"|---|---|---|"]
    for cid, ok, ev in results:
        mark = "⚪ manual" if ok is None else ("✅ pass" if ok else "❌ fail")
        lines.append(f"| {cid} | {mark} | {ev} |")
    lines += ["", "_Manual criteria (resilience, deploy, video demo) graded from your submission._",
              "Run `python benchmark/bench.py --resilience` for the no-loss proof."]
    (ROOT / "eval" / "REPORT.md").write_text("\n".join(lines))
    print(f"\nWrote {ROOT / 'eval' / 'REPORT.md'}")


if __name__ == "__main__":
    main()
