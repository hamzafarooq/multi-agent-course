"""Cross-arch comparison: read both final_metrics.json, emit a table image + a clean
chart. Reproducible — run after final_metrics.py has produced both arch summaries.

    python compare.py

Outputs (benchmark/comparison/):
    comparison_table.png     the full metric table, winner highlighted
    comparison_chart.png     grouped bars for the key metrics
"""

import json
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

HERE = Path(__file__).resolve().parent
OUT = HERE / "comparison"
OUT.mkdir(exist_ok=True)

C = json.loads((HERE / "runs/cascade/final_metric/final_metrics.json").read_text(encoding="utf-8"))
S = json.loads((HERE / "runs/s2s/final_metric/final_metrics.json").read_text(encoding="utf-8"))

CAS = "#2A9D8F"   # cascade — teal
S2S = "#E76F51"   # s2s — coral
INK = "#264653"


def hi(a, b): return "cascade" if a > b else ("s2s" if b > a else "tie")
def lo(a, b): return "cascade" if a < b else ("s2s" if b < a else "tie")


# ------------------------------- TABLE IMAGE -------------------------------
rows = [
    ("Tool accuracy (precision)", f"{C['tool_acc_mean']:.2f} ± {C['tool_acc_std']:.2f}",
                               f"{S['tool_acc_mean']:.2f} ± {S['tool_acc_std']:.2f}",
                               hi(C['tool_acc_mean'], S['tool_acc_mean'])),
    ("Tool recall",            f"{C['tool_recall_mean']:.2f} ± {C['tool_recall_std']:.2f}",
                               f"{S['tool_recall_mean']:.2f} ± {S['tool_recall_std']:.2f}",
                               hi(C['tool_recall_mean'], S['tool_recall_mean'])),
    ("Response accuracy (precision)", f"{C['response_acc_mean']:.2f} ± {C['response_acc_std']:.2f}",
                               f"{S['response_acc_mean']:.2f} ± {S['response_acc_std']:.2f}",
                               hi(C['response_acc_mean'], S['response_acc_mean'])),
    ("Response completeness (recall)", f"{C['response_compl_mean']:.2f} ± {C['response_compl_std']:.2f}",
                               f"{S['response_compl_mean']:.2f} ± {S['response_compl_std']:.2f}",
                               hi(C['response_compl_mean'], S['response_compl_mean'])),
    ("STT / recognition WER",  f"{C['stt_wer_mean']:.3f}", f"{S['stt_wer_mean']:.3f}",
                               lo(C['stt_wer_mean'], S['stt_wer_mean'])),
    ("Latency — to 1st audio (s)", f"{C['ttfa_mean_s']:.1f} ± {C['ttfa_std_s']:.1f}",
                               f"{S['ttfa_mean_s']:.1f} ± {S['ttfa_std_s']:.1f}",
                               lo(C['ttfa_mean_s'], S['ttfa_mean_s'])),
    ("Latency — to finish (s)", f"{C['latency_core_mean_s']:.1f} ± {C['latency_core_std_s']:.1f}",
                               f"{S['latency_core_mean_s']:.1f} ± {S['latency_core_std_s']:.1f}",
                               lo(C['latency_core_mean_s'], S['latency_core_mean_s'])),
    ("Cost / turn ($)",        f"${C['cost_core_mean_usd']:.4f}", f"${S['cost_core_mean_usd']:.4f}",
                               lo(C['cost_core_mean_usd'], S['cost_core_mean_usd'])),
    ("Cost total ($)",         f"${C['cost_core_total_usd']:.2f}", f"${S['cost_core_total_usd']:.2f}",
                               lo(C['cost_core_total_usd'], S['cost_core_total_usd'])),
    ("Data-isolation leaks",   f"{C['leaks']}", f"{S['leaks']}", lo(C['leaks'], S['leaks'])),
]
WIN_LABEL = {"cascade": "Cascade", "s2s": "S2S", "tie": "~ tie"}

fig, ax = plt.subplots(figsize=(9.2, 4.6))
ax.axis("off")
ax.set_title("Voice Agent Benchmark — Cascade vs Speech-to-Speech\n"
             "15 audio queries × 3 runs · tools = deterministic · answers = LLM-judge (gpt-5)",
             fontsize=13, fontweight="bold", color=INK, pad=18)

cells = [[r[0], r[1], r[2], WIN_LABEL[r[3]]] for r in rows]
tbl = ax.table(cellText=cells, colLabels=["Metric", "Cascade", "Speech-to-Speech", "Better"],
               cellLoc="center", loc="center", colWidths=[0.34, 0.24, 0.26, 0.16])
tbl.auto_set_font_size(False)
tbl.set_fontsize(10.5)
tbl.scale(1, 1.7)
for j in range(4):
    c = tbl[0, j]
    c.set_facecolor(INK)
    c.set_text_props(color="white", fontweight="bold")
for i, r in enumerate(rows, start=1):
    tbl[i, 0].set_text_props(fontweight="bold", ha="left")
    tbl[i, 0].PAD = 0.04
    for j in range(3):
        tbl[i, j].set_facecolor("#f4f6f6" if i % 2 else "#ffffff")
    win = r[3]
    wc = tbl[i, 3]
    if win == "cascade":
        wc.set_facecolor(CAS); wc.set_text_props(color="white", fontweight="bold")
    elif win == "s2s":
        wc.set_facecolor(S2S); wc.set_text_props(color="white", fontweight="bold")
    else:
        wc.set_facecolor("#e9ecef")
fig.tight_layout()
fig.savefig(OUT / "comparison_table.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)


# ------------------------------- CHART -------------------------------
def twobar(ax, cval, sval, title, fmt, cerr=None, serr=None):
    bars = ax.bar(["Cascade", "S2S"], [cval, sval], width=0.6, color=[CAS, S2S],
                  yerr=[cerr, serr] if cerr is not None else None, capsize=4,
                  error_kw={"ecolor": "#888", "elinewidth": 1})
    ax.set_title(title, fontweight="bold", fontsize=11, color=INK)
    ax.bar_label(bars, labels=[fmt.format(cval), fmt.format(sval)], padding=3, fontsize=10)
    ax.spines[["top", "right"]].set_visible(False)
    ax.margins(y=0.18)


fig, axes = plt.subplots(2, 2, figsize=(13, 9.6))
fig.suptitle("Cascade vs Speech-to-Speech — key metrics", fontsize=15, fontweight="bold", color=INK, y=0.99)

# (0,0) quality — grouped 0–1: tool & response, each precision + recall
qa = axes[0, 0]
labels = ["Tool\nacc", "Tool\nrecall", "Resp\nacc", "Resp\ncompl"]
cv = [C['tool_acc_mean'], C['tool_recall_mean'], C['response_acc_mean'], C['response_compl_mean']]
sv = [S['tool_acc_mean'], S['tool_recall_mean'], S['response_acc_mean'], S['response_compl_mean']]
ce = [C['tool_acc_std'], C['tool_recall_std'], C['response_acc_std'], C['response_compl_std']]
se = [S['tool_acc_std'], S['tool_recall_std'], S['response_acc_std'], S['response_compl_std']]
x = np.arange(len(labels)); w = 0.36
b1 = qa.bar(x - w / 2, cv, w, yerr=ce, capsize=3, color=CAS, label="Cascade", error_kw={"ecolor": "#888", "elinewidth": 1})
b2 = qa.bar(x + w / 2, sv, w, yerr=se, capsize=3, color=S2S, label="S2S", error_kw={"ecolor": "#888", "elinewidth": 1})
qa.set_xticks(x); qa.set_xticklabels(labels)
qa.set_title("Accuracy & quality  (higher = better)", fontweight="bold", fontsize=11, color=INK)
qa.set_ylabel("score (0–1)"); qa.set_ylim(0, 1.42)
qa.bar_label(b1, labels=[f"{v:.2f}" for v in cv], padding=2, fontsize=8)
qa.bar_label(b2, labels=[f"{v:.2f}" for v in sv], padding=2, fontsize=8)
qa.legend(fontsize=9, loc="upper right"); qa.spines[["top", "right"]].set_visible(False)

twobar(axes[0, 1], C['stt_wer_mean'], S['stt_wer_mean'], "STT / recognition WER  (lower = better)", "{:.3f}")

# latency — grouped: to-first-audio (responsiveness) vs to-finish
la = axes[1, 0]
labels2 = ["To 1st audio", "To finish"]
cv2 = [C['ttfa_mean_s'], C['latency_core_mean_s']]
sv2 = [S['ttfa_mean_s'], S['latency_core_mean_s']]
ce2 = [C['ttfa_std_s'], C['latency_core_std_s']]
se2 = [S['ttfa_std_s'], S['latency_core_std_s']]
x2 = np.arange(2)
lb1 = la.bar(x2 - w / 2, cv2, w, yerr=ce2, capsize=3, color=CAS, label="Cascade", error_kw={"ecolor": "#888", "elinewidth": 1})
lb2 = la.bar(x2 + w / 2, sv2, w, yerr=se2, capsize=3, color=S2S, label="S2S", error_kw={"ecolor": "#888", "elinewidth": 1})
la.set_xticks(x2); la.set_xticklabels(labels2)
la.set_title("Latency, seconds  (lower = better)", fontweight="bold", fontsize=11, color=INK)
la.set_ylabel("seconds")
la.bar_label(lb1, labels=[f"{v:.1f}" for v in cv2], padding=2, fontsize=8)
la.bar_label(lb2, labels=[f"{v:.1f}" for v in sv2], padding=2, fontsize=8)
la.legend(fontsize=9); la.spines[["top", "right"]].set_visible(False); la.margins(y=0.18)

twobar(axes[1, 1], C['cost_core_mean_usd'], S['cost_core_mean_usd'], "Cost per turn, USD  (lower = better)",
       "${:.4f}", cerr=C['cost_core_std_usd'], serr=S['cost_core_std_usd'])

fig.text(0.5, 0.005,
         f"Data-isolation leaks  —  Cascade: {C['leaks']}   ·   S2S: {S['leaks']}   "
         "(lower = better; a leak = revealed another user's data)",
         ha="center", fontsize=11, fontweight="bold", color="#a23b30")
fig.tight_layout(rect=[0, 0.03, 1, 0.97])
fig.savefig(OUT / "comparison_chart.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)


# --------------------- STANDALONE ACCURACY / QUALITY CHART ---------------------
# Just the four precision/recall quality bars, on their own — same data as the (0,0)
# panel of comparison_chart.png but as a single focused figure.
fig, ax = plt.subplots(figsize=(10.5, 6.4))
qlabels = ["Tool\naccuracy", "Tool\nrecall", "Response\naccuracy", "Response\ncompleteness"]
qcv = [C['tool_acc_mean'], C['tool_recall_mean'], C['response_acc_mean'], C['response_compl_mean']]
qsv = [S['tool_acc_mean'], S['tool_recall_mean'], S['response_acc_mean'], S['response_compl_mean']]
qce = [C['tool_acc_std'], C['tool_recall_std'], C['response_acc_std'], C['response_compl_std']]
qse = [S['tool_acc_std'], S['tool_recall_std'], S['response_acc_std'], S['response_compl_std']]
qx = np.arange(len(qlabels)); qw = 0.36
qb1 = ax.bar(qx - qw / 2, qcv, qw, yerr=qce, capsize=4, color=CAS, label="Cascade",
             error_kw={"ecolor": "#888", "elinewidth": 1})
qb2 = ax.bar(qx + qw / 2, qsv, qw, yerr=qse, capsize=4, color=S2S, label="S2S",
             error_kw={"ecolor": "#888", "elinewidth": 1})
ax.set_xticks(qx); ax.set_xticklabels(qlabels, fontsize=10)
ax.set_title("Agentic quality — precision & recall  (higher = better)\n"
             "15 audio queries × 3 runs · tools = deterministic · response = LLM-judge (sees tool calls)",
             fontsize=12.5, fontweight="bold", color=INK, pad=14)
ax.set_ylabel("score (0–1)"); ax.set_ylim(0, 1.45)
ax.bar_label(qb1, labels=[f"{v:.2f}" for v in qcv], padding=3, fontsize=10)
ax.bar_label(qb2, labels=[f"{v:.2f}" for v in qsv], padding=3, fontsize=10)
ax.legend(fontsize=10, loc="lower right")
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(OUT / "comparison_accuracy.png", dpi=200, bbox_inches="tight", facecolor="white")
plt.close(fig)

print("wrote:", OUT / "comparison_table.png")
print("wrote:", OUT / "comparison_chart.png")
print("wrote:", OUT / "comparison_accuracy.png")
