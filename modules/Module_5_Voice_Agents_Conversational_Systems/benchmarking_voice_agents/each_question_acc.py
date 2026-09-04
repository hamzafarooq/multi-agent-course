"""Grade every run of one arch: deterministic tools + LLM-judge answer + WER + leak.
Each of the 3 runs is graded SEPARATELY, then summarized per question.

    python each_question_acc.py --arch cascade        # or --arch s2s

Calls the OpenAI judge once per run (45 calls). Re-running is cheap: already-graded
runs are cached in the results folder and skipped.

Results only (NO code) are written under  runs/<arch>/final_metric/ :
    graded/<qid>_r<n>.json     per-run graded record (cache)
    per_question.json/.csv/.md per-question mean +/- std across the 3 runs
"""

import argparse
import csv
import json

import bench_grading as G

REPS = (1, 2, 3)


def grade_run(arch, qid, rep, graded_dir):
    out = graded_dir / f"{qid}_r{rep}.json"
    if out.exists():
        return json.loads(out.read_text(encoding="utf-8"))
    if not (G.BENCH / "runs" / arch / f"{qid}_r{rep}.json").exists():
        return None                                    # run missing (flaky s2s) — skip it
    q = G.MANIFEST[qid]
    rec = G.load_run(arch, qid, rep)
    tools = G.score_tools(rec, q)
    leak = G.check_leak(rec, q)
    ans = G.judge_response(q, rec)                     # <-- OpenAI call
    lm = rec.get("latency_measured", {})
    graded = {
        "id": qid, "arch": arch, "repeat": rep,
        "tool_accuracy": tools["tool_accuracy"],       # precision: of calls made, how many warranted
        "tool_recall": tools["tool_recall"],           # recall: of expected tools, how many fired
        "tool_verdict": tools["verdict"],
        "response_accuracy": ans["response_accuracy"],         # precision: of what it said, how much right
        "response_completeness": ans["response_completeness"], # recall: of required info/actions, how much conveyed
        "rationale": ans["rationale"],
        "wer": G.wer(q["source_text"], rec.get("transcript", "")),
        "leak_ok": leak["leak_ok"], "leaked": leak["leaked"],
        "blocked": rec.get("blocked", False),
        "cost_full": G.cost_full(rec),   # incl judge — reference only
        "cost_core": G.cost_core(rec),   # stt+agent+tts (cascade) / cost_model (s2s) — judge stripped
        "total_core": lm.get("total_core"),        # time to FINISH (judge+settle stripped)
        "ttfa_core": G.ttfa_core(rec, arch),       # time to FIRST audio (judge+settle stripped)
    }
    out.write_text(json.dumps(graded, indent=2) + "\n", encoding="utf-8")
    return graded


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default="cascade", choices=["cascade", "s2s"])
    arch = ap.parse_args().arch

    outdir = G.BENCH / "runs" / arch / "final_metric"
    graded_dir = outdir / "graded"
    graded_dir.mkdir(parents=True, exist_ok=True)

    rows = []
    print(f"Grading {arch}  (tools=deterministic, answer=LLM-judge {G.OPENAI_MODEL})\n")
    for qid, q in G.MANIFEST.items():
        gs = [g for g in (grade_run(arch, qid, r, graded_dir) for r in REPS) if g is not None]
        if not gs:
            print(f"{qid} — no runs on disk, skipped")
            continue
        tam, tas = G.mean_std([g["tool_accuracy"] for g in gs])       # tool precision
        trm, trs = G.mean_std([g["tool_recall"] for g in gs])         # tool recall
        ram, ras = G.mean_std([g["response_accuracy"] for g in gs])   # response precision
        rcm, rcs = G.mean_std([g["response_completeness"] for g in gs])  # response recall
        # cost/latency over runs that actually processed (blocked turns are pure-guardrail)
        proc = [g for g in gs if not g["blocked"]]
        cm, cs = G.mean_std([g["cost_core"] for g in proc])
        lm, ls = G.mean_std([g["total_core"] for g in proc])
        wm, _ = G.mean_std([g["wer"] for g in gs])
        print(f'{qid} [{q["category"]:<24}] tool(acc={tam} rec={trm})  '
              f'resp(acc={ram} cmp={rcm})  wer={wm}  core={lm}±{ls}s  ${cm}±{cs}')
        rows.append({
            "id": qid, "category": q["category"], "hops": q["hops"],
            "tool_acc_mean": tam, "tool_acc_std": tas,
            "tool_recall_mean": trm, "tool_recall_std": trs,
            "resp_acc_mean": ram, "resp_acc_std": ras,
            "resp_cmp_mean": rcm, "resp_cmp_std": rcs,
            "wer_mean": wm,
            "core_mean_s": lm, "core_std_s": ls,
            "cost_mean": cm, "cost_std": cs,
        })

    (outdir / "per_question.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    with open(outdir / "per_question.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    md = ["| q | category | tool acc ± | tool recall ± | resp acc ± | resp compl ± | wer | core(s) ± | cost($) ± |",
          "|:--|:--|:--|:--|:--|:--|:--|:--|:--|"]
    for r in rows:
        md.append(f"| {r['id']} | {r['category']} | {r['tool_acc_mean']}±{r['tool_acc_std']} | "
                  f"{r['tool_recall_mean']}±{r['tool_recall_std']} | "
                  f"{r['resp_acc_mean']}±{r['resp_acc_std']} | {r['resp_cmp_mean']}±{r['resp_cmp_std']} | "
                  f"{r['wer_mean']} | {r['core_mean_s']}±{r['core_std_s']} | {r['cost_mean']}±{r['cost_std']} |")
    (outdir / "per_question.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"\nwrote {outdir}\\per_question.(json|csv|md)  +  graded/ ({len(G.MANIFEST) * len(REPS)} runs)")


if __name__ == "__main__":
    main()
