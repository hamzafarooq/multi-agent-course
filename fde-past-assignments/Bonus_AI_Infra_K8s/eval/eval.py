#!/usr/bin/env python3
"""Automated checks for Assignment 3: AI Infra on Kubernetes.

Run BEFORE teardown, against the live cluster:

    python eval/eval.py [--namespace default] [--deployment vllm] [--service vllm]

Writes eval/REPORT.md with a pass/fail table for the automated rubric criteria.
Manual criteria (writeup, video, teardown proof) are graded from your submission.
Requires: kubectl configured for the cluster, and curl.
"""
import argparse, json, pathlib, subprocess, sys

def sh(cmd, timeout=30):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return 124, "", "timeout"

def kjson(args, ns):
    code, out, _ = sh(f"kubectl -n {ns} get {args} -o json")
    if code != 0:
        return None
    try:
        return json.loads(out)
    except json.JSONDecodeError:
        return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--namespace", default="default")
    ap.add_argument("--deployment", default="vllm")
    ap.add_argument("--service", default="vllm")
    a = ap.parse_args()
    ns, dep, svc = a.namespace, a.deployment, a.service
    results = []

    def add(cid, ok, evidence):
        results.append((cid, bool(ok), evidence))
        print(f"[{'PASS' if ok else 'FAIL'}] {cid}: {evidence}")

    code, out, err = sh("kubectl cluster-info")
    add("cluster_reachable", code == 0, out.splitlines()[0] if out else err)

    nodes = kjson("nodes", ns) or {"items": []}
    gpu_nodes = [n["metadata"]["name"] for n in nodes["items"]
                 if "nvidia.com/gpu" in n.get("status", {}).get("capacity", {})]
    add("gpu_nodes", gpu_nodes, f"GPU nodes: {gpu_nodes or 'none found'}")

    d = kjson(f"deployment {dep}", ns)
    if not d:
        add("fleet_replicas", False, f"deployment {dep} not found in namespace {ns}")
        add("readiness_probe", False, "no deployment")
        add("gpu_request", False, "no deployment")
        add("zero_drop_rollout", False, "no deployment")
    else:
        want = d["spec"].get("replicas", 0)
        ready = d.get("status", {}).get("readyReplicas", 0)
        add("fleet_replicas", want >= 2 and ready == want,
            f"replicas wanted={want} ready={ready}")

        c = d["spec"]["template"]["spec"]["containers"][0]
        probe = c.get("readinessProbe", {})
        http = probe.get("httpGet", {})
        add("readiness_probe",
            http.get("path") == "/health" and str(http.get("port")) == "8000",
            f"readinessProbe={probe or 'missing'}")

        gpu = c.get("resources", {}).get("limits", {}).get("nvidia.com/gpu")
        add("gpu_request", str(gpu) == "1", f"nvidia.com/gpu limit={gpu}")

        ru = d["spec"].get("strategy", {}).get("rollingUpdate", {})
        add("zero_drop_rollout",
            str(ru.get("maxUnavailable")) in ("0", "0%") and ru.get("maxSurge") not in (None, 0, "0"),
            f"rollingUpdate={ru or 'missing'}")

    s = kjson(f"service {svc}", ns)
    ip = ""
    if s:
        ing = s.get("status", {}).get("loadBalancer", {}).get("ingress", [])
        ip = (ing[0].get("ip") or ing[0].get("hostname")) if ing else ""
    add("front_door", bool(ip), f"external endpoint: {ip or 'none'}")

    if ip:
        body = json.dumps({"model": "Qwen/Qwen2.5-VL-7B-Instruct",
                           "messages": [{"role": "user", "content": "Say ready."}],
                           "max_tokens": 8})
        code, out, err = sh(
            f"curl -s -m 60 http://{ip}/v1/chat/completions "
            f"-H 'Content-Type: application/json' -d '{body}'", timeout=70)
        ok = code == 0 and '"choices"' in out
        add("tokens_flow", ok, (out[:120] + "...") if ok else (err or out[:120] or "no response"))
    else:
        add("tokens_flow", False, "no external endpoint to test")

    rubric = json.loads((pathlib.Path(__file__).parent / "rubric.json").read_text())
    pts = {c["id"]: c["points"] for c in rubric["automated"]}
    earned = sum(pts.get(cid, 0) for cid, ok, _ in results if ok)
    total = sum(pts.values())

    lines = ["# Assignment 3 automated scorecard", "",
             f"Automated score: **{earned} / {total}** "
             "(manual criteria graded from writeup, video, and teardown proof)", "",
             "| Check | Result | Evidence |", "|---|---|---|"]
    for cid, ok, ev in results:
        lines.append(f"| {cid} | {'PASS' if ok else 'FAIL'} | {ev.replace('|', '/')} |")
    lines += ["", "Reminder: tear the cluster down after this run. GPUs bill while idle."]
    report = pathlib.Path(__file__).parent / "REPORT.md"
    report.write_text("\n".join(lines) + "\n")
    print(f"\nAutomated: {earned}/{total}. Wrote {report}")
    sys.exit(0 if earned == total else 1)

if __name__ == "__main__":
    main()
