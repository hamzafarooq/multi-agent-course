#!/usr/bin/env python3
"""Benchmark + SLA gate for Assignment 3 — Moment Search at Scale.

    python benchmark/bench.py                 # accept-latency, ingest-vs-search, recall
    python benchmark/bench.py --resilience    # kill a worker mid-ingest, assert no loss
    python benchmark/bench.py --json out.json # also write machine-readable results

Exits non-zero if ANY target in sla.json is missed, so it doubles as your grading
gate and a CI check.

This is a SCAFFOLD. The measurement skeleton, the SLA comparison, and the exit
code are done. You fill the four TODOs so it measures YOUR running app:
labeled queries for recall, the concurrent-ingest load, the throughput probe,
and the worker-crash step. Keep the gates in sla.json as-is.
"""
from __future__ import annotations

import argparse
import json
import os
import pathlib
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
SLA = json.loads((ROOT / "benchmark" / "sla.json").read_text())
BASE = os.getenv("BASE_URL", "http://localhost:8100").rstrip("/")
ADMIN = os.getenv("ADMIN_TOKEN", "")


def _req(method, path, body=None, token=None, timeout=30):
    url = f"{BASE}{path}"
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


def p95(xs):
    return statistics.quantiles(xs, n=100)[94] if len(xs) >= 20 else (max(xs) if xs else 0.0)


def measure_accept_latency(n=30):
    """POST /admin/documents should enqueue-and-return fast (no parsing in-request)."""
    lat = []
    for i in range(n):
        st, _, ms = _req("POST", "/admin/documents", token=ADMIN,
                         body={"uri": f"https://example.com/probe_{i}.pdf",
                               "kind": "paper", "title": f"probe {i}"})
        if st == 202:
            lat.append(ms)
    return p95(lat) if lat else float("inf")


def measure_search_p95(n=40):
    q = "what does the survey say about hybrid retrieval"
    lat = []
    for _ in range(n):
        st, _, ms = _req("GET", "/ask_stream?q=" + urllib.parse.quote(q))
        if st == 200:
            lat.append(ms)
    return p95(lat) if lat else float("inf")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--resilience", action="store_true")
    ap.add_argument("--json", dest="json_out", default="")
    args = ap.parse_args()

    results, failures = {}, []

    def gate(name, value, ok, target):
        results[name] = {"value": value, "target": target, "pass": bool(ok)}
        print(f"[{'PASS' if ok else 'FAIL'}] {name}: {value} (target {target})")
        if not ok:
            failures.append(name)

    if args.resilience:
        # TODO(you): start a large ingest, kill a worker mid-stream, then assert
        #   every source reaches 'indexed', no source is lost, and finished stages
        #   are not re-run. Poll GET /admin/sources for the terminal state.
        no_loss = False  # <- replace with your measured result
        gate("no_loss_under_crash", no_loss, no_loss and SLA["no_loss_required"], "0 dropped, all indexed")
        return sys.exit(1 if failures else 0)

    # 1. accept latency
    a = measure_accept_latency()
    gate("accept_latency_p95_ms", round(a, 1), a <= SLA["accept_latency_p95_ms"], SLA["accept_latency_p95_ms"])

    # 2. search stays fast during a big ingest
    idle = measure_search_p95()
    # TODO(you): kick off a large ingest (many /admin/documents) IN THE BACKGROUND,
    #   then measure search p95 again while it drains. Replace the line below.
    during = measure_search_p95()  # <- measure this WHILE ingesting
    ratio = (during / idle) if idle else float("inf")
    gate("search_p95_during_ingest_ratio", round(ratio, 2),
         ratio <= SLA["search_p95_during_ingest_ratio_max"], SLA["search_p95_during_ingest_ratio_max"])

    # 3. recall@10 on labeled queries
    # TODO(you): load benchmark/queries.jsonl (query -> expected source/locator),
    #   run each through /ask_stream, and compute recall@10. Replace the stub.
    recall = 0.0  # <- replace with your measured recall@10
    gate("recall_at_10", recall, recall >= SLA["recall_at_10_min"], SLA["recall_at_10_min"])

    # 4. ingestion throughput
    # TODO(you): time a known backfill (total chunks / seconds to all-indexed).
    throughput = 0.0  # <- replace with your measured chunks/s
    gate("ingest_throughput_chunks_per_s", throughput,
         throughput >= SLA["ingest_throughput_min_chunks_per_s"], SLA["ingest_throughput_min_chunks_per_s"])

    if args.json_out:
        pathlib.Path(args.json_out).write_text(json.dumps(results, indent=2))
        print(f"wrote {args.json_out}")

    print(f"\n{'ALL SLAs PASS' if not failures else 'SLA FAILURES: ' + ', '.join(failures)}")
    sys.exit(1 if failures else 0)


if __name__ == "__main__":
    main()
