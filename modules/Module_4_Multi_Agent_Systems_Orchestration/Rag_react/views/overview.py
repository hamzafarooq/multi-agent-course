"""Landing page: the problem, the two architectures, the six questions, and the headline eval."""

import streamlit as st

import react_agent as ra
from ui import RAG_HOW, REACT_HOW, cost, facts, md, saved_results

WHY = {
    "Q1": ("Chained", "Find *which* company, then its price, then revenue, then divide. "
                      "One search on the whole question never returns the price chunk."),
    "Q2": ("Chained", "Part 1's answer (which company) decides what part 2 looks up."),
    "Q3": ("Two sections", "Debt (balance sheet) and revenue (income statement), obscure enough "
                           "that the model can't recall them."),
    "Q4": ("10-K + web", "Filed revenue plus a live market cap. The router picks only one source."),
    "Q5": ("10-K + docs", "Risk factors plus Agents SDK features. The router picks only one source."),
    "Q6": ("10-K → web → math", "The web lookup builds on a 10-K figure, then arithmetic."),
}
CAVEAT = {
    "Q4": "Finance caveat: this ratio divides today's market cap by 2021 revenue, so the periods don't match. "
          "An analyst would use trailing-twelve-month revenue. The question is kept as written because it tests "
          "combining two sources, not because the ratio is meaningful.",
}

st.title("RAG vs ReAct")
st.markdown("#### When retrieval misses, one-shot RAG doesn't say *I don't know*. It answers from memory, "
            "and still cites the documents.")
st.markdown("Same model, same data, same questions. The only difference is the control flow: a router that "
            "retrieves **once**, or a loop that decides what to look up **next** based on what it just saw.")

runs = saved_results()
if runs:
    (rag_ok, n), (react_ok, _) = facts(runs, 2), facts(runs, 3)
    c1, c2, c3 = st.columns(3)
    c1.metric("One-shot RAG · key facts correct", f"{rag_ok}/{n}", f"{rag_ok / n:.0%}",
              delta_color="off", delta_arrow="off")
    c2.metric("ReAct · key facts correct", f"{react_ok}/{n}", f"{react_ok / n:.0%}",
              delta_color="off", delta_arrow="off")
    metered = [r for r in runs if cost(r[1]["rag"].get("usage")) and cost(r[1]["react"].get("usage"))]
    if metered:
        ratio = sum(cost(r[1]["react"]["usage"]) for r in metered) / sum(cost(r[1]["rag"]["usage"]) for r in metered)
        c3.metric("What the loop costs", f"{ratio:.1f}× RAG's cost",
                  f"{sum(len(r[4]) for r in runs) / len(runs):.1f} tool calls per question on average",
                  delta_color="off", delta_arrow="off")
    st.caption(f"Scored against golden answers with 10-K quotes, over {len(runs)} saved runs "
               f"on {ra.MODEL}. Full breakdown on the Results page.")

st.divider()
left, right = st.columns(2, gap="large")
with left:
    st.subheader("One-shot RAG")
    st.markdown("Route to one source → top-3 chunks → write. If the right chunk isn't in those three, "
                "the model fills the gap from what it memorised.")
    st.graphviz_chart(RAG_HOW, width="content")
with right:
    st.subheader("ReAct")
    st.markdown("Thought → Action → Observation, repeated. One focused search per fact, "
                "a calculator for the maths, and the next step depends on the last result.")
    st.graphviz_chart(REACT_HOW, width="content")

st.subheader("Why the loop alone isn't enough")
st.markdown("""
Three choices in the tools and prompt matter as much as the loop:

1. **Tools return raw chunks, not an LLM summary.** A summarising step slipped a memorised "$2.25B" into Q1's Observation.
2. **`search_10k` filters to one filing** and says when a filing isn't there. Without it, "Lyft 2024" questions got figures from memory.
3. **Only figures that appear in an Observation may be stated,** and a Final Answer that gives up after fewer than three searches is sent back to search again.
""")

st.subheader("The six questions")
st.caption("Expected answer from the 10-K (and the live web for ⏱ facts), then what each agent actually said. "
           "An answer is correct only when every key fact matches. Each answer was also checked by hand against "
           "the filing text, including claims the automatic check doesn't cover.")


def verdict(where, checks):
    missed = [f["label"] + (" ⏱" if f.get("time_dependent") else "") for f, passed in checks if not passed]
    if not missed:
        where.success(f"Correct · {len(checks)}/{len(checks)} key facts")
    else:
        where.error(f"Wrong · {len(checks) - len(missed)}/{len(checks)} key facts. Missed: {'; '.join(missed)}")


def audited(where, audit, who):
    if audit:
        where.caption(f"🔎 **Checked against the filing ({audit['date']}):** {md(audit[who])}")
    else:
        where.caption("🔎 Not checked by hand: this run was recorded after the last manual audit.")


for gold, run, rag_res, react_res, tools in runs:
    kind, why = WHY.get(gold["id"], ("", ""))
    with st.container(border=True):
        st.markdown(f"### {gold['id']} · {kind}")
        st.markdown(f"**{md(run['question'])}**")
        st.caption(f"Why one-shot RAG struggles: {why}")
        st.info(f"**Expected:** {md(gold['answer'])}")
        if gold["id"] in CAVEAT:
            st.warning(CAVEAT[gold["id"]])
        audit = run.get("audit")
        left, right = st.columns(2, gap="large")
        with left:
            st.markdown(f"**One-shot RAG** · routed to `{run['rag']['route'].get('action', 'INTERNET_QUERY')}`, "
                        f"1 retrieval")
            verdict(st, rag_res)
            st.markdown(md(run["rag"]["answer"]))
            audited(st, audit, "rag")
        with right:
            st.markdown(f"**ReAct** · {' → '.join(tools)}")
            verdict(st, react_res)
            st.markdown(md(run["react"]["answer"]))
            audited(st, audit, "react")

st.subheader("What it doesn't fix")
st.markdown("""
- **Source quality.** ReAct checks that a figure came from a tool, not that the tool's source is any good. The web tool returns whatever ranks, social posts included.
- **Live facts drift.** Market cap and latest MAPCs (⏱) change, so those golden figures date.
- **It costs more.** Several LLM calls per question instead of two.
- **Gaps in the data.** 414 Lyft chunks (mostly risk-factor text) have no fiscal year attached, so a year-filtered search never sees them. None of the six questions depends on them.
- **The automatic check tests key figures only.** It can't catch a wrong side claim (RAG's "in cash" in Q1), which is why every saved answer was also checked by hand.
""")

a, b = st.columns(2)
a.page_link("app.py", label="Compare the two agents on one question", icon="🧭")
b.page_link("views/results.py", label="See every result", icon="📊")
