"""All six saved demo runs on one page: RAG vs ReAct, scored against the golden answers."""

import streamlit as st

import react_agent as ra
from ui import cost, facts, md, saved_results

runs = saved_results()
st.title("Results: RAG vs ReAct")
st.caption(f"The six saved demo runs (`demo_runs/`), scored against `golden_answers.json`. Model: {ra.MODEL}.")
if not runs:
    st.error("No saved runs found in demo_runs/.")
    st.stop()

(rag_ok, n), (react_ok, _) = facts(runs, 2), facts(runs, 3)
c1, c2, c3, c4 = st.columns(4)
c1.metric("RAG key facts", f"{rag_ok}/{n}", f"{rag_ok / n:.0%}", delta_color="off", delta_arrow="off")
c2.metric("ReAct key facts", f"{react_ok}/{n}", f"{react_ok / n:.0%}", delta_color="off", delta_arrow="off")
c3.metric("Avg time (RAG → ReAct)",
          f"{sum(r[1]['rag']['seconds'] for r in runs) / len(runs):.1f}s → "
          f"{sum(r[1]['react']['seconds'] for r in runs) / len(runs):.1f}s")
metered = [r for r in runs if cost(r[1]["rag"].get("usage")) and cost(r[1]["react"].get("usage"))]
if metered:
    rag_cost, react_cost = (sum(cost(r[1][w]["usage"]) for r in metered) for w in ("rag", "react"))
    label = "Total cost" if len(metered) == len(runs) else f"Cost · {', '.join(r[0]['id'] for r in metered)}"
    c4.metric(f"{label} (RAG → ReAct)", f"${rag_cost:.4f} → ${react_cost:.4f}",
              f"{react_cost / rag_cost:.1f}× RAG", delta_color="off", delta_arrow="off",
              help="Only runs recorded with token counting; any others show n/a.")
else:
    c4.metric("Cost", "n/a", help="These runs were recorded before token counting was added.")

st.dataframe([{
    "Q": gold["id"],
    "RAG route": run["rag"]["route"].get("action", "INTERNET_QUERY"),
    "RAG facts": f"{sum(p for _, p in rag_res)}/{len(rag_res)}",
    "ReAct facts": f"{sum(p for _, p in react_res)}/{len(react_res)}",
    "ReAct tools": " → ".join(tools),
    "RAG time": f"{run['rag']['seconds']:.1f}s",
    "ReAct time": f"{run['react']['seconds']:.1f}s",
    **{f"{name} cost": "n/a" if (c := cost(run[who].get("usage"))) is None else f"${c:.4f}"
       for who, name in (("rag", "RAG"), ("react", "ReAct"))},
} for gold, run, rag_res, react_res, tools in runs], hide_index=True, width="stretch")
st.caption("RAG always makes one route decision and one retrieval. ⏱ facts come from the live web "
           "(recorded 2026-09-23) and can legitimately change.")

st.subheader("Question by question")
for gold, run, rag_res, react_res, tools in runs:
    rag_s, react_s = sum(p for _, p in rag_res), sum(p for _, p in react_res)
    with st.expander(f"**{gold['id']}** · RAG {rag_s}/{len(rag_res)} · ReAct {react_s}/{len(react_res)} — "
                     f"{run['question']}"):
        st.markdown(f"**Golden answer:** {md(gold['answer'])}")
        st.table([{"Key fact": f["label"] + (" ⏱" if f.get("time_dependent") else ""),
                   "RAG": "✅" if rag_res[i][1] else "❌", "ReAct": "✅" if react_res[i][1] else "❌"}
                  for i, (f, _) in enumerate(rag_res)])
        left, right = st.columns(2, gap="large")
        with left.container(border=True):
            st.markdown(f"**RAG** · `{run['rag']['route'].get('action', 'INTERNET_QUERY')}` · 1 retrieval")
            st.markdown(md(run["rag"]["answer"]))
        with right.container(border=True):
            st.markdown(f"**ReAct** · {len(tools)} tool calls: {' → '.join(tools)}")
            st.markdown(md(run["react"]["answer"]))
