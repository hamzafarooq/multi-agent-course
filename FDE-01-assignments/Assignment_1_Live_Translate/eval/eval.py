#!/usr/bin/env python3
"""
FDE · Assignment 1 · Rubric eval & submission report  (PROVIDED)
================================================================
Runs the automated portion of the rubric against your running backend, captures
evidence for the human-graded portion, and writes a submission report you turn
in ALONGSIDE your video demo.

    # with both services running:
    python eval/eval.py --student "Jane Doe" --video "https://youtu.be/…" \
        --deploy-url "https://your-gateway.fly.dev"

Outputs (next to this script):
    REPORT.md     ← your scored rubric SCORECARD. The /fde-live-translate-eval
                    skill folds this into PRODUCT_EVAL.md, which is what you submit.
    report.json   ← machine-readable, same data

`auto` criteria are scored here. `manual` criteria (Mexican-Spanish quality,
docs) are left for the grader, who uses the captured evidence + your video.
Standard library only.
"""
import argparse
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RUBRIC = json.loads((HERE / "rubric.json").read_text())


def get(url, timeout=10):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def post(url, payload, timeout=60, headers=None):
    data = json.dumps(payload).encode()
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, data=data, headers=h, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, None
    except Exception:
        return 0, None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--target", default="http://localhost:8787")
    ap.add_argument("--ai", default="http://localhost:8000")
    ap.add_argument("--student", default="")
    ap.add_argument("--video", default="")
    ap.add_argument("--deploy-url", default="", help="public Fly.io gateway URL, e.g. https://your-gw.fly.dev")
    args = ap.parse_args()

    ev = {}  # evidence bag
    scores = {}  # criterion id -> awarded points
    notes = {}

    def award(cid, pts, note):
        scores[cid] = pts
        notes[cid] = note

    crit = {c["id"]: c for c in RUBRIC["criteria"]}

    # ---- widget_lights_up: contract works ----
    s1, b1 = post(args.target + "/translate", {"text": "Good morning, welcome!", "target": "es-MX"})
    s2, bb = post(args.target + "/translate/batch", {"texts": ["Home", "Add to cart"], "target": "es-MX"})
    single_ok = s1 == 200 and isinstance(b1, dict) and all(k in b1 for k in ("translated", "cached", "latencyMs", "model"))
    batch_ok = s2 == 200 and isinstance(bb, dict) and isinstance(bb.get("results"), list) and len(bb["results"]) == 2
    ev["sample_translation"] = b1.get("translated") if b1 else None
    if single_ok and batch_ok:
        award("widget_lights_up", crit["widget_lights_up"]["points"], "translate + batch return valid shapes")
    else:
        award("widget_lights_up", 0, f"single_ok={single_ok} batch_ok={batch_ok} (status {s1}/{s2})")

    # ---- caching_correctness ----
    phrase = {"text": "The quick brown fox jumps over the lazy dog.", "target": "es-MX"}
    _, c1 = post(args.target + "/translate", phrase)
    time.sleep(0.05)
    _, c2 = post(args.target + "/translate", phrase)
    hit_second = bool(c2 and c2.get("cached"))
    faster = bool(c1 and c2 and c2.get("latencyMs", 1e9) <= c1.get("latencyMs", 0))
    db_files = list((ROOT / "backend" / "ai-service-python").glob("*.db"))
    db_persisted = any(f.stat().st_size > 0 for f in db_files)
    ev["cache_first_ms"] = c1.get("latencyMs") if c1 else None
    ev["cache_second_ms"] = c2.get("latencyMs") if c2 else None
    cache_pts = crit["caching_correctness"]["points"]
    got = (0.5 * cache_pts if hit_second and faster else 0) + (0.5 * cache_pts if db_persisted else 0)
    award("caching_correctness", round(got),
          f"2nd cached={hit_second}, faster={faster}, sqlite_persisted={db_persisted}")

    # ---- performance_sla: run bench.py ----
    bench = ROOT / "benchmark" / "bench.py"
    out_json = HERE / "_bench.json"
    sla_pass, bench_metrics = False, {}
    try:
        proc = subprocess.run(
            [sys.executable, str(bench), "--target", args.target, "--json", str(out_json)],
            capture_output=True, text=True, timeout=600,
        )
        sla_pass = proc.returncode == 0
        if out_json.exists():
            bench_metrics = json.loads(out_json.read_text())
        ev["bench_tail"] = "\n".join(proc.stdout.strip().splitlines()[-14:])
    except Exception as e:  # noqa: BLE001
        ev["bench_tail"] = f"bench failed to run: {e}"
    ev["bench_metrics"] = bench_metrics
    award("performance_sla", crit["performance_sla"]["points"] if sla_pass else 0,
          f"bench SLA gate {'PASS' if sla_pass else 'FAIL'}")

    # ---- logging_observability (incl. trace correlation) ----
    _, stats = get(args.target + "/stats")
    _, health = get(args.target + "/health")
    has_hit_rate = bool(stats and any("hit_rate" in k for k in stats))
    health_nests_ai = bool(health and isinstance(health.get("aiService"), (dict, str)) and health.get("aiService") != "unreachable")
    ai_log = ROOT / "backend" / "ai-service-python" / "ai-service.log"
    log_ok = ai_log.exists() and ai_log.stat().st_size > 0

    # trace: send a sentinel X-Request-Id, confirm it lands in BOTH services' logs
    trace_id = "evaltrace-" + uuid.uuid4().hex[:12]
    post(args.target + "/translate", {"text": "trace probe", "target": "es-MX"},
         headers={"X-Request-Id": trace_id})
    time.sleep(0.2)

    def _log_has(token, candidates):
        for p in candidates:
            try:
                if p.exists() and token in p.read_text(errors="ignore"):
                    return True
            except Exception:
                pass
        return False

    gw_logs = [ROOT / "gateway.log", ROOT / "backend" / "gateway-node" / "gateway.log"]
    ai_logs = [ai_log, ROOT / "ai-service.log"]
    trace_ok = _log_has(trace_id, gw_logs) and _log_has(trace_id, ai_logs)
    ev["trace_correlated"] = trace_ok

    log_pts = crit["logging_observability"]["points"]
    got = sum([has_hit_rate, health_nests_ai, log_ok, trace_ok]) / 4 * log_pts
    award("logging_observability", round(got),
          f"stats_hit_rate={has_hit_rate}, health_reports_ai={health_nests_ai}, ai_log_file={log_ok}, trace_correlated={trace_ok}")

    # ---- service_separation_contract ----
    s_bad, _ = post(args.target + "/translate", {"nope": 1})
    bad_input_ok = s_bad == 400
    sep_pts = crit["service_separation_contract"]["points"]
    got = (0.5 * sep_pts if bad_input_ok else 0) + (0.5 * sep_pts if health_nests_ai else 0)
    award("service_separation_contract", round(got),
          f"400_on_bad_input={bad_input_ok}, gateway_nests_ai_health={health_nests_ai}")

    # ---- git hygiene (informational, feeds deploy_docs manual score) ----
    try:
        staged = subprocess.run(["git", "status", "--porcelain"], cwd=ROOT, capture_output=True, text=True).stdout
        bad = [l for l in staged.splitlines() if any(x in l for x in (".env", "node_modules", ".venv", ".db"))]
        widget_diff = subprocess.run(["git", "diff", "--stat", "--", "widget", "extension", "benchmark"],
                                     cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        bad, widget_diff = [], ""
    ev["hygiene_flags"] = bad
    ev["provided_files_changed"] = widget_diff

    # ---- deploy evidence (feeds deploy_docs manual score) ----
    ev["deploy_url"] = args.deploy_url or None
    if args.deploy_url:
        ds, dh = get(args.deploy_url.rstrip("/") + "/health")
        ev["deploy_health_ok"] = bool(ds == 200 and dh)
    else:
        ev["deploy_health_ok"] = None

    # ---- manual criteria: not auto-scored ----
    for c in RUBRIC["criteria"]:
        if c["type"] == "manual":
            scores.setdefault(c["id"], None)

    auto_total = sum(c["points"] for c in RUBRIC["criteria"] if c["type"] == "auto")
    auto_got = sum(scores[c["id"]] for c in RUBRIC["criteria"] if c["type"] == "auto")
    manual_total = sum(c["points"] for c in RUBRIC["criteria"] if c["type"] == "manual")

    # ---- write report.json ----
    report = {
        "assignment": RUBRIC["assignment"],
        "student": args.student,
        "video": args.video,
        "target": args.target,
        "auto_score": auto_got,
        "auto_max": auto_total,
        "manual_max": manual_total,
        "scores": scores,
        "notes": notes,
        "evidence": ev,
    }
    (HERE / "report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False))

    # ---- write REPORT.md ----
    md = []
    md.append(f"# Submission Report — {RUBRIC['assignment']}\n")
    md.append(f"- **Student:** {args.student or '_(fill in)_'}")
    md.append(f"- **Video demo:** {args.video or '_(paste your 60–90s demo link)_'}")
    md.append(f"- **Backend target:** `{args.target}`")
    md.append(f"- **Auto-graded score:** **{auto_got} / {auto_total}**  ·  manual portion: {manual_total} pts (grader)\n")
    md.append("## Rubric\n")
    md.append("| Criterion | Type | Points | Result |")
    md.append("|---|---|---|---|")
    for c in RUBRIC["criteria"]:
        sc = scores[c["id"]]
        result = notes.get(c["id"], "graded from video/evidence") if c["type"] == "auto" else "**grader** — see evidence + video"
        got = f"{sc}/{c['points']}" if sc is not None else f"—/{c['points']}"
        md.append(f"| {c['label']} | {c['type']} | {got} | {result} |")
    md.append("\n## Evidence\n")
    md.append(f"- Sample translation (`Good morning, welcome!`): **{ev.get('sample_translation')}**")
    md.append(f"- Cache latency: first `{ev.get('cache_first_ms')} ms` → second `{ev.get('cache_second_ms')} ms`")
    md.append(f"- Trace correlation (one request across both logs): {'✅ yes' if ev.get('trace_correlated') else '❌ not found'}")
    if ev.get("bench_metrics"):
        bm = ev["bench_metrics"]
        lat = bm.get("latency", {})
        md.append(f"- Benchmark: hit p95 `{lat.get('hit_p95',0):.0f} ms`, miss p95 `{lat.get('miss_p95',0):.0f} ms`, "
                  f"hit rate `{bm.get('hit_rate_pct',0):.0f}%`, throughput `{bm.get('throughput_rps',0):.0f} rps`, "
                  f"SLA **{'PASS' if bm.get('sla_pass') else 'FAIL'}**")
        cost = bm.get("cost", {})
        md.append(f"- Cost: `${cost.get('per_miss_usd',0):.6f}`/miss; monthly savings from cache `${cost.get('monthly_savings_usd',0):,.2f}`")
    if ev.get("deploy_url"):
        md.append(f"- Deploy: `{ev['deploy_url']}/health` → {'✅ ok' if ev.get('deploy_health_ok') else '❌ UNREACHABLE'}")
    else:
        md.append("- Deploy: _(no --deploy-url given; grader verifies your Fly.io URL from README/video)_")
    if ev.get("hygiene_flags"):
        md.append(f"- ⚠️ Git hygiene flags (should be empty): `{ev['hygiene_flags']}`")
    if ev.get("provided_files_changed"):
        md.append(f"- ⚠️ Provided files changed (should be empty): `{ev['provided_files_changed']}`")
    md.append("\n<details><summary>Benchmark output</summary>\n\n```\n" + ev.get("bench_tail", "") + "\n```\n</details>\n")
    (HERE / "REPORT.md").write_text("\n".join(md))
    if (HERE / "_bench.json").exists():
        (HERE / "_bench.json").unlink()

    print(f"\nAuto score: {auto_got}/{auto_total}  (+ {manual_total} manual pts from grader)")
    print(f"Wrote {HERE/'REPORT.md'} (your scorecard) and {HERE/'report.json'}.")
    print("Run /fde-live-translate-eval to fold this into PRODUCT_EVAL.md — that's your submission.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
