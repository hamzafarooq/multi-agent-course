"""Roll the per-run graded files into ONE final table for an arch. No API calls
(reads the graded/ folder produced by each_question_acc.py). Run that first.

    python final_metrics.py --arch cascade      # or --arch s2s

Results only are written under  runs/<arch>/final_metric/ :
    final_metrics.json / .csv / .md
"""

import argparse
import csv
import json

import bench_grading as G


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arch", default="cascade", choices=["cascade", "s2s"])
    arch = ap.parse_args().arch

    outdir = G.BENCH / "runs" / arch / "final_metric"
    files = sorted((outdir / "graded").glob("*.json"))
    if not files:
        raise SystemExit(f"no graded files in {outdir/'graded'} — run "
                         f"`python each_question_acc.py --arch {arch}` first")
    graded = [json.loads(p.read_text(encoding="utf-8")) for p in files]

    # Accuracy over ALL runs (blocked/refused turns still count for correctness).
    # Two axes each, precision/recall style:
    #   tool_acc  = precision (of calls made, how many warranted / right-args)
    #   tool_rec  = recall    (of expected tools, how many fired)
    #   resp_acc  = precision (of what it said, how much correct — incl. not lying about actions)
    #   resp_cmp  = recall    (of required info/actions, how much conveyed/done)
    tacc_m, tacc_s = G.mean_std([g["tool_accuracy"] for g in graded])
    trec_m, trec_s = G.mean_std([g["tool_recall"] for g in graded])
    racc_m, racc_s = G.mean_std([g["response_accuracy"] for g in graded])
    rcmp_m, rcmp_s = G.mean_std([g["response_completeness"] for g in graded])
    wer_m, _ = G.mean_std([g["wer"] for g in graded])

    # Latency & cost over PROCESSED turns only (judge & settle already excluded via
    # total_core / cost_core; blocked turns are pure-guardrail with no agent/TTS, so
    # they'd distort a "pipeline speed/cost" number — keep them out of it).
    proc = [g for g in graded if not g["blocked"]]
    core_m, core_s = G.mean_std([g["total_core"] for g in proc])
    ttfa_m, ttfa_s = G.mean_std([g.get("ttfa_core") for g in proc])
    costs = [g["cost_core"] for g in proc if g["cost_core"] is not None]
    cost_m, cost_s = G.mean_std(costs)
    total_cost = round(sum(costs), 5)

    n = len(graded)
    leaks = sum(1 for g in graded if not g["leak_ok"])

    summary = {
        "arch": arch, "n_runs": n, "n_clips": n // 3, "n_processed": len(proc),
        "tool_acc_mean": tacc_m, "tool_acc_std": tacc_s,           # tool PRECISION
        "tool_recall_mean": trec_m, "tool_recall_std": trec_s,     # tool RECALL
        "response_acc_mean": racc_m, "response_acc_std": racc_s,           # response PRECISION
        "response_compl_mean": rcmp_m, "response_compl_std": rcmp_s,       # response RECALL (completeness)
        "stt_wer_mean": wer_m,
        "ttfa_mean_s": ttfa_m, "ttfa_std_s": ttfa_s,                 # time to FIRST audio
        "latency_core_mean_s": core_m, "latency_core_std_s": core_s,  # time to FINISH
        "cost_core_mean_usd": cost_m, "cost_core_std_usd": cost_s,
        "cost_core_total_usd": total_cost,
        "leaks": leaks,
    }
    (outdir / "final_metrics.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    with open(outdir / "final_metrics.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["metric", "value"])
        for k, v in summary.items():
            w.writerow([k, v])

    md = [
        f"# {arch.upper()} — final benchmark metrics",
        f"_{n} runs ({n // 3} clips x 3), judge = {G.OPENAI_MODEL}_",
        "",
        "| Metric | Value |",
        "|:--|:--|",
        f"| **Tool accuracy** (precision — of calls made, how many warranted) | **{tacc_m} ± {tacc_s}** |",
        f"| **Tool recall** (of expected tools, how many fired) | **{trec_m} ± {trec_s}** |",
        f"| **Response accuracy** (precision — of what it said, how much right) | **{racc_m} ± {racc_s}** |",
        f"| **Response completeness** (recall — of required info/actions, how much conveyed) | **{rcmp_m} ± {rcmp_s}** |",
        f"| STT word error rate | {wer_m} |",
        f"| **Latency — time to FIRST audio** (responsiveness) | **{ttfa_m} ± {ttfa_s} s** |",
        f"| Latency — time to FINISH (STT+agent+TTS, no judge/settle) | {core_m} ± {core_s} s |",
        f"| Cost — core per turn (STT+agent+TTS, no judge) | ${cost_m} ± {cost_s} |",
        f"| Cost — core total ({len(proc)} processed turns) | ${total_cost} |",
        f"| Data-isolation leaks | {leaks} |",
        "",
        f"Quality metrics are over all {n} runs; latency & cost over the {len(proc)} processed "
        "(non-blocked) turns. ± is population std (variance = std²). Tools are scored "
        "deterministically (accuracy = precision, recall as defined); the response is scored by "
        "the LLM judge, which is shown the ACTUAL tool calls so a reply that *claims* an action "
        "it never performed is penalised on accuracy. Excluded everywhere: `search_memory`, the "
        "judge (time & cost), and the 1.5s settle wait — so latency/cost are pure STT+agent+TTS.",
    ]
    (outdir / "final_metrics.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    print("\n".join(md))
    print(f"\nwrote {outdir}\\final_metrics.(json|csv|md)")


if __name__ == "__main__":
    main()
