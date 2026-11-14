#!/usr/bin/env python3
"""
FDE · Assignment 1 · Benchmark & SLA gate  (PROVIDED — you run it, don't build it)
=================================================================================
Fires a realistic workload at your backend, measures latency / throughput /
cache-hit-rate / cost, and checks the results against the SLA in sla.json.

It talks to the same contract the widget uses, so it measures what your users
actually feel. By default it hits the Node gateway (end-to-end). Use --direct
to hit the Python AI service instead.

Usage:
    python bench.py                        # uses sla.json in this folder
    python bench.py --target http://localhost:8787
    python bench.py --direct               # target the AI service on :8000
    python bench.py --rounds 6 --concurrency 16
    python bench.py --json results.json    # also write machine-readable output

Exit code is non-zero if any SLA fails — so it works in CI / as a grading gate.
Standard library only; no pip install needed.
"""
import argparse
import json
import statistics
import sys
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

# A realistic mix: short UI strings + longer sentences, like a real page.
WORKLOAD = [
    "Home", "Best sellers", "Add to cart", "Checkout", "Your order is confirmed.",
    "Welcome to Sierra Coffee Roasters.", "Small-batch coffee, roasted fresh every morning.",
    "A smooth, balanced medium roast with notes of chocolate and toasted almond.",
    "Every order ships within 24 hours of roasting.",
    "If you are not completely satisfied, we offer a full refund within 30 days.",
    "Sign in", "Create an account", "Forgot your password?", "Contact support",
    "Free shipping on orders over $50.", "Our support team is here to help every day of the week.",
    "A bold, dark roast built for espresso with a long, sweet finish.",
    "Track your shipment", "Leave a review", "Frequently asked questions",
]

HERE = Path(__file__).resolve().parent


def load_sla(path: Path) -> dict:
    return json.loads(path.read_text())


def post(url: str, payload: dict, timeout: float = 60.0) -> dict:
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"}, method="POST"
    )
    t0 = time.perf_counter()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = json.loads(r.read().decode("utf-8"))
            ms = (time.perf_counter() - t0) * 1000
            return {
                "ok": True, "ms": ms, "status": getattr(r, "status", 200),
                "cached": bool(body.get("cached")), "translated": body.get("translated", ""),
            }
    except urllib.error.HTTPError as e:
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000, "status": e.code, "cached": False, "translated": ""}
    except Exception as e:  # noqa: BLE001 — benchmark should never crash on a bad response
        return {"ok": False, "ms": (time.perf_counter() - t0) * 1000, "status": 0, "cached": False, "translated": "", "error": str(e)}


def pctl(values, p) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def est_tokens(text: str) -> int:
    # ~4 chars per token is a good rough heuristic for cost estimation.
    return max(1, round(len(text) / 4))


def run_phase(base: str, items, concurrency: int):
    url = base + "/translate"
    results = []
    t0 = time.perf_counter()
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futures = [pool.submit(post, url, {"text": t, "target": "es-MX"}) for t in items]
        for i, fut in enumerate(futures):
            res = fut.result()
            res["text"] = items[i]
            results.append(res)
    elapsed = time.perf_counter() - t0
    return results, elapsed


def main() -> int:
    ap = argparse.ArgumentParser(description="FDE Assignment 1 benchmark & SLA gate")
    ap.add_argument("--sla", default=str(HERE / "sla.json"))
    ap.add_argument("--target", default=None, help="override target base URL")
    ap.add_argument("--direct", action="store_true", help="target AI service on :8000 instead of the gateway")
    ap.add_argument("--rounds", type=int, default=None)
    ap.add_argument("--concurrency", type=int, default=None)
    ap.add_argument("--json", default=None, help="write machine-readable results here")
    args = ap.parse_args()

    cfg = load_sla(Path(args.sla))
    sla = cfg["sla"]
    cost = cfg["cost_model"]
    base = args.target or ("http://localhost:8000" if args.direct else cfg.get("target", "http://localhost:8787"))
    rounds = args.rounds or cfg["workload"]["rounds"]
    concurrency = args.concurrency or cfg["workload"]["concurrency"]

    print(f"\nFDE · Assignment 1 — Benchmark")
    print(f"  target      {base}")
    print(f"  workload    {len(WORKLOAD)} phrases × {rounds} rounds   concurrency {concurrency}")

    # health
    try:
        with urllib.request.urlopen(base + "/health", timeout=10) as r:
            print(f"  health      {r.read().decode()[:120]}")
    except Exception as e:  # noqa: BLE001
        print(f"\n✗ Cannot reach {base}/health — is your backend running?  ({e})")
        return 2

    # Phase 1: COLD — one pass, warms the cache. These should be cache misses.
    print("\n→ cold pass (expect cache misses)…")
    cold, _ = run_phase(base, WORKLOAD, concurrency=min(concurrency, 4))

    # Phase 2: WARM — remaining rounds, should be cache hits. Timed for throughput.
    warm_items = WORKLOAD * max(1, rounds - 1)
    print(f"→ warm passes (expect cache hits)… {len(warm_items)} requests")
    warm, warm_elapsed = run_phase(base, warm_items, concurrency=concurrency)

    allr = cold + warm
    ok = [r for r in allr if r["ok"]]
    errs = [r for r in allr if not r["ok"]]
    hits = [r for r in ok if r["cached"]]
    misses = [r for r in ok if not r["cached"]]

    hit_ms = [r["ms"] for r in hits]
    miss_ms = [r["ms"] for r in misses]
    error_rate = 100.0 * len(errs) / max(1, len(allr))
    hit_rate = 100.0 * len(hits) / max(1, len(ok))
    throughput = len(warm) / warm_elapsed if warm_elapsed > 0 else 0.0

    # ---- cost model ----
    in_price = cost["input_usd_per_mtok"] / 1_000_000
    out_price = cost["output_usd_per_mtok"] / 1_000_000
    cost_per_miss = statistics.mean(
        [(est_tokens(r["text"]) * in_price) + (est_tokens(r["translated"] or r["text"]) * out_price) for r in misses]
    ) if misses else 0.0
    volume = cost["monthly_translation_volume"]
    # With caching at the measured hit rate, only misses cost money.
    monthly_uncached = volume * cost_per_miss
    monthly_cached = volume * (1 - hit_rate / 100.0) * cost_per_miss
    savings = monthly_uncached - monthly_cached

    # ---- report ----
    def line(label, val):
        print(f"    {label:<28}{val}")

    print("\n── LATENCY ─────────────────────────────────────────")
    line("cache MISS p50 / p95 (ms)", f"{pctl(miss_ms,50):.0f} / {pctl(miss_ms,95):.0f}")
    line("cache HIT  p50 / p95 (ms)", f"{pctl(hit_ms,50):.0f} / {pctl(hit_ms,95):.0f}")
    line("speedup (miss p95 / hit p95)", f"{(pctl(miss_ms,95)/pctl(hit_ms,95)):.0f}×" if hit_ms and miss_ms else "n/a")

    print("── THROUGHPUT & RELIABILITY ────────────────────────")
    line("warm throughput (req/s)", f"{throughput:.1f}")
    line("cache hit rate (%)", f"{hit_rate:.1f}")
    line("error rate (%)", f"{error_rate:.1f}  ({len(errs)} errors)")

    print("── COST (placeholder prices — verify in sla.json) ──")
    line("model", cost["model"])
    line("cost per MISS (avg)", f"${cost_per_miss:.6f}")
    line(f"@ {volume:,}/mo, no cache", f"${monthly_uncached:,.2f}")
    line(f"@ {volume:,}/mo, cached", f"${monthly_cached:,.2f}")
    line("monthly savings from cache", f"${savings:,.2f}")

    # ---- SLA gate ----
    checks = [
        ("cache_hit_p95_ms", pctl(hit_ms, 95), "<=", sla["cache_hit_p95_ms"]),
        ("cache_miss_p95_ms", pctl(miss_ms, 95), "<=", sla["cache_miss_p95_ms"]),
        ("min_cache_hit_rate_pct", hit_rate, ">=", sla["min_cache_hit_rate_pct"]),
        ("max_error_rate_pct", error_rate, "<=", sla["max_error_rate_pct"]),
        ("min_throughput_rps", throughput, ">=", sla["min_throughput_rps"]),
    ]
    print("── SLA GATE ────────────────────────────────────────")
    all_pass = True
    for name, actual, op, target in checks:
        passed = actual <= target if op == "<=" else actual >= target
        all_pass = all_pass and passed
        print(f"    {'PASS' if passed else 'FAIL'}  {name:<24} {actual:.1f} {op} {target}")

    print("\n" + ("✅ ALL SLAs MET" if all_pass else "❌ SLA FAILURES — see above") + "\n")

    if args.json:
        Path(args.json).write_text(json.dumps({
            "target": base, "rounds": rounds, "concurrency": concurrency,
            "latency": {"miss_p50": pctl(miss_ms, 50), "miss_p95": pctl(miss_ms, 95),
                         "hit_p50": pctl(hit_ms, 50), "hit_p95": pctl(hit_ms, 95)},
            "hit_rate_pct": hit_rate, "error_rate_pct": error_rate, "throughput_rps": throughput,
            "cost": {"per_miss_usd": cost_per_miss, "monthly_no_cache_usd": monthly_uncached,
                      "monthly_cached_usd": monthly_cached, "monthly_savings_usd": savings},
            "sla_pass": all_pass,
        }, indent=2))
        print(f"Wrote {args.json}")

    return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
