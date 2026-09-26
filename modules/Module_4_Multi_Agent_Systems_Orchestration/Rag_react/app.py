"""
Streamlit demo: the same question sent to the RAG router (one shot)
and to the ReAct agent (Thought -> Action -> Observation loop), side by side,
then checked against the golden answers in golden_answers.json.

This is the Compare page of the app; main.py adds the Overview and Results pages.
Run from this folder (needs .env, rag_helpers.py, react_agent.py, Agentic_RAG/qdrant_data):
    .venv/bin/streamlit run main.py
"""

import asyncio
import hashlib
import html
import json
import os
import re
import threading
import time

import streamlit as st
from dotenv import load_dotenv
from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx

import rag_helpers
import react_agent as ra
from ui import DOT_STYLE, PRICE_CACHED, PRICE_IN, PRICE_OUT, RAG_HOW, REACT_HOW, cost, md

HERE = os.path.dirname(os.path.abspath(__file__))
COLLECTIONS = {"OPENAI_QUERY": "opnai_data", "10K_DOCUMENT_QUERY": "10k_data"}
DEMO_DIR = os.environ.get("DEMO_DIR", os.path.join(HERE, "demo_runs"))  # saved runs for demo mode
# Each agent runs in its own thread, so each gets its own token tally. Kept on rag_helpers because
# Streamlit re-executes this file on every rerun, while the wrapped client (and module) persist.
_meter = rag_helpers.__dict__.setdefault("_app_token_meter", threading.local())

st.set_page_config(page_title="RAG vs ReAct", page_icon="🧭", layout="wide")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [data-testid="stAppViewContainer"], .stMarkdown, button, input, textarea {
  font-family: 'Inter', system-ui, sans-serif !important;
}
.block-container { max-width: 1240px; padding-top: 2.2rem; padding-bottom: 4rem; }
h1 {
  display: inline-block; font-weight: 800 !important; letter-spacing: -0.035em; line-height: 1.1 !important;
  background: linear-gradient(90deg, #4F46E5, #9333EA 55%, #DB2777);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
}
.hero-sub { color: #475569; font-size: 1.05rem; margin: -0.4rem 0 0.9rem; max-width: 760px; }
.chips { display: flex; flex-wrap: wrap; gap: .5rem; margin-bottom: 1.4rem; }
.chip { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 999px;
        padding: .28rem .8rem; font-size: .8rem; color: #334155; }
.chip b { color: #4F46E5; font-weight: 600; }

/* Cards: st.container(border=True) */
div[data-testid="stVerticalBlockBorderWrapper"] {
  border-radius: 18px !important; border-color: #E6E9F2 !important; background: #FFFFFF;
  box-shadow: 0 1px 2px rgba(15, 23, 42, .04), 0 10px 30px rgba(15, 23, 42, .06);
}
.panel-head { display: flex; align-items: center; justify-content: space-between; gap: .5rem; }
.panel-title { font-size: 1.15rem; font-weight: 700; color: #0F172A; }
.panel-sub { color: #64748B; font-size: .85rem; margin: .1rem 0 .6rem; }
.head-right { display: flex; align-items: center; gap: .45rem; }
.clock { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .8rem; font-weight: 600;
         padding: .18rem .55rem; border-radius: 999px; background: #F1F5F9; color: #475569;
         font-variant-numeric: tabular-nums; }
.clock-done { background: #DCFCE7; color: #15803D; }
.clock-stopped { background: #FEE2E2; color: #B91C1C; }
.tag { font-size: .7rem; font-weight: 700; letter-spacing: .04em; text-transform: uppercase;
       padding: .22rem .6rem; border-radius: 999px; white-space: nowrap; }
.tag-plain { background: #E0F2FE; color: #0369A1; }
.tag-react { background: #F3E8FF; color: #7E22CE; }
.route { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .78rem;
         background: #EEF2FF; color: #4338CA; padding: .15rem .5rem; border-radius: 7px; }
.reason { color: #64748B; font-size: .85rem; }

/* ReAct timeline */
.step { display: flex; gap: .65rem; align-items: flex-start; margin: .7rem 0 .2rem; }
.step-n { flex: none; width: 1.65rem; height: 1.65rem; border-radius: 50%;
          background: linear-gradient(135deg, #6366F1, #A855F7); color: #fff;
          font-size: .75rem; font-weight: 700; display: flex; align-items: center; justify-content: center;
          box-shadow: 0 4px 10px rgba(99, 102, 241, .35); }
.thought { color: #1E293B; font-size: .9rem; line-height: 1.5; padding-top: .12rem; }
.action { margin: .3rem 0 0 2.3rem; font-size: .82rem; color: #475569; line-height: 1.5; }
.tool { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; font-size: .76rem; font-weight: 600;
        padding: .12rem .5rem; border-radius: 7px; margin-right: .35rem; }
.tool-search_10k { background: #DBEAFE; color: #1D4ED8; }
.tool-search_openai_docs { background: #DCFCE7; color: #15803D; }
.tool-search_web { background: #FFEDD5; color: #C2410C; }
.tool-calculator { background: #FCE7F3; color: #BE185D; }
.saved { font-size: .8rem; color: #64748B; }
.saved b { color: #059669; }
.final-label { font-size: .75rem; font-weight: 700; letter-spacing: .05em; text-transform: uppercase;
               color: #0369A1; margin: 1rem 0 .2rem; }

/* Buttons, inputs, metrics, tables */
.stButton button[kind="primary"] {
  border: 0; border-radius: 12px; padding: .62rem 1.3rem; font-weight: 600;
  background: linear-gradient(90deg, #4F46E5, #9333EA); box-shadow: 0 6px 18px rgba(99, 102, 241, .35);
}
.stButton button[kind="primary"]:disabled { background: #CBD5E1; box-shadow: none; }
[data-testid="stTextArea"] textarea, [data-baseweb="select"] > div { border-radius: 12px !important; }
[data-testid="stMetric"] { background: #F8FAFF; border: 1px solid #E6E9F2; border-radius: 14px; padding: .7rem .9rem; }
[data-testid="stMetricValue"] { font-weight: 700; }
[data-testid="stTable"] table { border-radius: 12px; overflow: hidden; font-size: .88rem; }
[data-testid="stExpander"] details { border-radius: 12px; }
</style>
"""


@st.cache_resource(show_spinner="Loading embedding model and vector database…")
def init():
    load_dotenv(os.path.join(HERE, ".env"))
    rag_helpers.init_rag(
        openai_api_key=os.getenv("openai_api_key") or os.getenv("OPENAI_API_KEY"),
        serp_api_key=os.getenv("serp_api_key") or os.getenv("SERP_API_KEY"),
        qdrant_path=os.path.join(HERE, "Agentic_RAG", "qdrant_data"),
    )
    return True


def meter_tokens(client) -> None:
    """Wrap chat.completions.create so every call adds its usage to the calling thread's tally."""
    if client is None or getattr(client.chat.completions.create, "metered", False):
        return
    create = client.chat.completions.create

    def metered(*args, **kwargs):
        response = create(*args, **kwargs)
        tally, usage = getattr(_meter, "tally", None), getattr(response, "usage", None)
        if tally is not None and usage is not None:
            details = getattr(usage, "prompt_tokens_details", None)
            tally["calls"] += 1
            tally["input"] += usage.prompt_tokens or 0
            tally["cached"] += getattr(details, "cached_tokens", 0) or 0
            tally["output"] += usage.completion_tokens or 0
        return response

    metered.metered = True
    client.chat.completions.create = metered


def start_tally(rec: dict) -> None:
    rec["usage"] = _meter.tally = {"calls": 0, "input": 0, "cached": 0, "output": 0}


def field(name: str, text: str) -> str:
    m = re.search(rf"{name}:\s*(.*?)(?=\n\s*(?:Thought|Action|Action Input|Final Answer):|\Z)", text, re.S)
    return m.group(1).strip() if m else ""


def html_md(markup: str, where=st) -> None:
    where.markdown(markup, unsafe_allow_html=True)


def panel_head(box, title: str, tag: str, tag_class: str, sub: str):
    """Draw a panel's header; returns clock(text, state) that redraws it with a timer in the corner."""
    head = box.empty()

    def clock(text: str = "", state: str = "") -> None:
        timer = f"<span class='clock clock-{state}'>{text}</span>" if text else ""
        html_md(f"<div class='panel-head'><span class='panel-title'>{title}</span>"
                f"<span class='head-right'>{timer}<span class='tag {tag_class}'>{tag}</span></span></div>"
                f"<div class='panel-sub'>{sub}</div>", head)

    clock()
    return clock


# ── Demo mode: every good live run is saved; demo mode replays it without any API call ──

def run_key(question: str) -> str:
    gold = GOLDEN.get(question)
    return gold["id"] if gold else "custom-" + hashlib.sha1(question.encode()).hexdigest()[:10]


def load_run(question: str):
    try:
        with open(os.path.join(DEMO_DIR, run_key(question) + ".json")) as f:
            run = json.load(f)
        return run if run.get("question") == question else None
    except (OSError, ValueError):
        return None


def save_run(run: dict) -> None:
    os.makedirs(DEMO_DIR, exist_ok=True)
    path = os.path.join(DEMO_DIR, run_key(run["question"]) + ".json")
    with open(path + ".tmp", "w") as f:
        json.dump(run, f, indent=1)
    os.replace(path + ".tmp", path)  # never leave a half-written recording


def side_by_side(jobs, clocks, final_seconds=None):
    """Run each job in its own thread so both panels fill at once; return (result, seconds) per job.
    The threads get this run's Streamlit context, so they can draw into their own containers.
    Meanwhile this thread ticks each panel's clock, freezing it with ✓ as soon as that job is done
    (at final_seconds[i] if given: demo mode shows the recorded time, not the replay's)."""
    ctx, out = get_script_run_ctx(), [None] * len(jobs)

    def work(i, job):
        t = time.perf_counter()
        try:
            out[i] = (job(), time.perf_counter() - t, None)
        except BaseException as e:  # re-raised on the script thread below
            out[i] = (None, time.perf_counter() - t, e)

    threads = [add_script_run_ctx(threading.Thread(target=work, args=(i, job), daemon=True), ctx)
               for i, job in enumerate(jobs)]
    t0 = time.perf_counter()
    for th in threads:
        th.start()
    frozen = set()
    while len(frozen) < len(jobs):
        for i, clock in enumerate(clocks):
            if i in frozen:
                continue
            if out[i] is None:
                clock(f"⏱ {time.perf_counter() - t0:.1f}s", "running")
                continue
            res, secs, err = out[i]
            secs = final_seconds[i] if final_seconds else secs
            bad = err is not None or str(res).startswith("Stopped:")
            clock(f"{'✕' if bad else '✓'} {secs:.1f}s", "stopped" if bad else "done")
            frozen.add(i)
        time.sleep(0.1)
    for _, _, err in out:
        if err:
            raise err
    return [(res, secs) for res, secs, _ in out]


def pause(seconds: float) -> None:
    """Replay pacing: follow the recorded timing, but keep each pause between 0.35s and 2s."""
    time.sleep(max(0.35, min(seconds, 2.0)))


def plain_rag(question: str, box, rec: dict, replay: dict = None) -> str:
    """The notebook's _run_rag_pipeline, unrolled so each stage can be shown (and recorded)."""
    start_tally(rec)
    with box.status("Routing…", expanded=True) as status:
        t = time.perf_counter()
        if replay:
            pause(replay["t_route"])
            route = replay["route"]
        else:
            route = rag_helpers.route_query(question)
        rec["route"], rec["t_route"] = route, time.perf_counter() - t
        action = route.get("action", "INTERNET_QUERY")
        html_md(f"<span class='route'>{html.escape(action)}</span> "
                f"<span class='reason'>{html.escape(route.get('reason', ''))}</span>")

        t = time.perf_counter()
        if action in COLLECTIONS:
            status.update(label="Retrieving (one search, top 3 chunks)…")
            if replay:
                chunks = replay["chunks"]
            else:
                hits = asyncio.run(rag_helpers._qdrant.query_points(
                    collection_name=COLLECTIONS[action],
                    query=rag_helpers._get_text_embeddings(question), limit=3))
                chunks = [{"label": f"{p.payload.get('metadata', {}).get('company', 'OpenAI docs')} "
                                    f"FY{p.payload.get('metadata', {}).get('fiscal_year') or '?'}",
                           "text": p.payload["content"]} for p in hits.points]
            rec["chunks"] = chunks
            with st.expander("The 3 chunks it retrieved: is the answer actually in them?"):
                for c in chunks:
                    st.caption(c["label"])
                    st.text(" ".join(c["text"].split())[:1200])
            status.update(label="Writing the answer…")
            if replay:
                pause(replay["t_answer"])
                answer = replay["answer"]
            else:
                answer = rag_helpers._rag_formatted_response(question, [c["text"] for c in chunks])
        else:
            status.update(label="Searching the web…")
            if replay:
                pause(replay["t_answer"])
                answer = replay["answer"]
            else:
                answer = rag_helpers.get_internet_content(question)
        rec["answer"], rec["t_answer"] = answer, time.perf_counter() - t
        status.update(label="Done: one route, one retrieval, one answer", state="complete", expanded=True)
    html_md("<div class='final-label'>Answer</div>", box)
    box.markdown(md(answer))
    return answer


def react(question: str, box, stats: dict, rec: dict, replay: dict = None) -> str:
    status = box.status("Thinking…", expanded=True)
    rec["events"], t0 = [], time.perf_counter()
    start_tally(rec)

    def on_step(step, kind, text):
        rec["events"].append([step, kind, text, time.perf_counter() - t0])
        stats["steps"] = step
        with status:
            if kind == "reply":
                thought = field("Thought", text) or "…"
                html_md(f"<div class='step'><span class='step-n'>{step}</span>"
                        f"<span class='thought'>{html.escape(thought)}</span></div>")
                if "Final Answer:" not in text:
                    if action := field("Action", text):
                        stats["tools"] = stats.get("tools", 0) + 1
                        stats.setdefault("path", []).append((step, action, field("Action Input", text)))
                        html_md(f"<div class='action'><span class='tool tool-{html.escape(action)}'>"
                                f"{html.escape(action)}</span>{html.escape(field('Action Input', text))}</div>")
                        status.update(label=f"Step {step}: {action}…")
                    else:
                        st.warning("Couldn't parse this reply; the loop will ask the model to fix its format.")
            else:
                with st.expander(f"Observation · {len(text):,} chars"):
                    st.text(text)

    if replay:
        previous = 0.0
        for step, kind, text, at in replay["events"]:
            pause(at - previous)
            previous = at
            on_step(step, kind, text)
        answer = replay["answer"]
    else:
        answer = ra.react_agent(question, verbose=False, on_step=on_step)
    rec["answer"] = answer
    stopped = answer.startswith("Stopped:")
    status.update(label="Stopped" if stopped else f"Done in {stats.get('steps', 0)} steps",
                  state="error" if stopped else "complete", expanded=True)
    (box.error if stopped else box.success)("Final answer")
    box.markdown(md(answer))
    return answer


def golden(question: str, answers: dict) -> None:
    gold = GOLDEN.get(question)
    if not gold:
        return
    with st.container(border=True):
        st.subheader(f"📏 Golden answer ({gold['id']})")
        st.markdown(md(gold["answer"]))

        checks = {who: ra.check_answer(ans, gold) for who, ans in answers.items()}
        for col, (who, res) in zip(st.columns(len(checks)), checks.items()):
            passed = sum(p for _, p in res)
            missed = len(res) - passed
            col.metric(who, f"{passed}/{len(res)} key facts", "all correct" if not missed else f"-{missed} missed")

        st.table([{"Key fact": fact["label"] + (" ⏱" if fact.get("time_dependent") else ""),
                   **{who: "✅" if res[i][1] else "❌" for who, res in checks.items()}}
                  for i, (fact, _) in enumerate(ra.check_answer("", gold))])
        if any(f.get("time_dependent") for f in gold["key_facts"]):
            st.caption("⏱ comes from the live web and was recorded on 2026-09-23, so it can legitimately change.")
        with st.expander("Evidence: where the golden answer comes from"):
            for src in gold["sources"]:
                st.markdown(f"**{src['filing']}:** “{md(src['quote'])}”")
            st.caption(md(gold["notes"]))


# ── Diagrams (Graphviz DOT, rendered in the browser: works offline in demo mode too) ──

TOOL_COLORS = {"search_10k": ("#DBEAFE", "#1D4ED8"), "search_openai_docs": ("#DCFCE7", "#15803D"),
               "search_web": ("#FFEDD5", "#C2410C"), "calculator": ("#FCE7F3", "#BE185D")}
def dot_label(text: str, limit: int = 38) -> str:
    text = " ".join(str(text).split())
    text = text if len(text) <= limit else text[:limit - 1] + "…"
    return text.replace("\\", "\\\\").replace('"', '\\"')


def rag_path_dot(route: dict) -> str:
    action = route.get("action", "INTERNET_QUERY")
    source = {"10K_DOCUMENT_QUERY": "10-K collection: top-3 chunks", "OPENAI_QUERY": "OpenAI docs: top-3 chunks"}.get(
        action, "Web search: one query")
    return f"""digraph {{ {DOT_STYLE}
  q [label="Question"];
  r [label="Router → {dot_label(action)}", fillcolor="#E0F2FE", color="#7DD3FC"];
  s [label="{source}"];
  a [label="Answer (1 retrieval)", fillcolor="#DCFCE7", color="#86EFAC"];
  q -> r -> s -> a;
}}"""


def react_path_dot(path: list, answer: str) -> str:
    nodes, prev = ['q [label="Question"];'], "q"
    for i, (step, action, action_input) in enumerate(path):
        fill, font = TOOL_COLORS.get(action, ("#F1F5F9", "#334155"))
        nodes.append(f'n{i} [label="{step} · {dot_label(action)}\\n{dot_label(action_input)}", '
                     f'fillcolor="{fill}", fontcolor="{font}", color="{fill}"];')
        nodes.append(f"{prev} -> n{i};")
        prev = f"n{i}"
    stopped = answer.startswith("Stopped:")
    nodes.append(f'a [label="{"Stopped" if stopped else "Final answer"}", '
                 f'fillcolor="{"#FEE2E2" if stopped else "#DCFCE7"}", color="{"#FCA5A5" if stopped else "#86EFAC"}"];')
    nodes.append(f"{prev} -> a;")
    return f"digraph {{ {DOT_STYLE}\n  " + "\n  ".join(nodes) + "\n}"


# ── Page ──────────────────────────────────────────────────────────────────────

html_md(CSS)
GOLDEN = ra.load_golden()
EXAMPLES = {f"Q{i}. {q}": q for i, q in enumerate(ra.HARD_QUESTIONS, 1)}
try:
    init()
    meter_tokens(rag_helpers._openaiclient)  # idempotent; also covers a client swapped in after init
    live_ok = True
except Exception as e:  # no network / model / DB: demo mode still works
    live_ok = False
    st.warning(f"Live mode is unavailable ({type(e).__name__}); turn on Demo mode to replay saved runs.")


def use_example():
    if st.session_state.example:
        st.session_state.question = EXAMPLES[st.session_state.example]


st.title("RAG vs ReAct")
html_md(f"""
<div class='hero-sub'>Ask one question and watch two agents answer it: a one-shot router that retrieves once,
and a ReAct agent that reasons, searches, checks and calculates in a loop.</div>
<div class='chips'>
  <span class='chip'>🧠 <b>{ra.MODEL}</b></span>
  <span class='chip'>📄 Uber FY2021 · Lyft FY2020–22 10-Ks</span>
  <span class='chip'>🔧 10-K search · docs search · web · calculator</span>
  <span class='chip'>📏 golden answers for Q1–Q6</span>
</div>""")

with st.container(border=True):
    st.selectbox("Example questions (each needs several lookups, more than one source, or a result that decides the next lookup)",
                 [""] + list(EXAMPLES), key="example", on_change=use_example, format_func=lambda s: s or "Pick one…")
    question = st.text_area("Question", key="question", height=90, placeholder="…or type your own")
    saved = load_run(question.strip()) if question.strip() else None
    b, mode, _ = st.columns([1.2, 1, 2.2], vertical_alignment="center")
    demo = mode.toggle("🎬 Demo mode", key="demo", help="Replay the saved run for this question: no API calls.")
    run = b.button("Ask both agents  →", type="primary", width="stretch",
                   disabled=not question.strip() or (demo and not saved) or (not demo and not live_ok))

with st.expander("🗺️ How the two agents work"):
    how_rag, how_react = st.columns(2, gap="large")
    how_rag.markdown("**RAG**: one route, one retrieval, one answer")
    how_rag.graphviz_chart(RAG_HOW, width="content")
    how_react.markdown("**ReAct**: reason, act, observe, repeat")
    how_react.graphviz_chart(REACT_HOW, width="content")

left, right = st.columns(2, gap="large")
left_box, right_box = left.container(border=True), right.container(border=True)
rag_clock = panel_head(left_box, "RAG", "One shot", "tag-plain", "One route → one retrieval → one answer")
react_clock = panel_head(right_box, "ReAct agent", "Loop", "tag-react",
                         "Thought → Action → Observation, until it can answer")

if run:
    q = question.strip()
    replay = saved if demo else None
    rec = {"question": q, "rag": {}, "react": {}}
    stats = {}
    (plain_answer, rag_secs), (react_answer, react_secs) = side_by_side(
        [lambda: plain_rag(q, left_box, rec["rag"], replay and replay["rag"]),
         lambda: react(q, right_box, stats, rec["react"], replay and replay["react"])],
        [rag_clock, react_clock],
        replay and [replay["rag"]["seconds"], replay["react"]["seconds"]])
    rec["rag"]["seconds"] = replay["rag"]["seconds"] if replay else rag_secs
    rec["react"]["seconds"] = replay["react"]["seconds"] if replay else react_secs
    if replay:  # recordings made before token metering have no usage
        for who in ("rag", "react"):
            rec[who]["usage"] = replay[who].get("usage")

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("RAG time · 1 retrieval", f"{rec['rag']['seconds']:.1f}s")
    m2.metric(f"ReAct time · {stats.get('steps', 0)} steps · {stats.get('tools', 0)} tools",
              f"{rec['react']['seconds']:.1f}s")
    usage = {who: rec[who].get("usage") for who in ("rag", "react")}
    for col, who, name in ((m3, "rag", "RAG"), (m4, "react", "ReAct")):
        u = usage[who]
        if not u or not u["calls"]:
            col.metric(f"{name} cost", "n/a", help="This saved run was recorded before token counting was added.")
            continue
        note = f"{u['input'] + u['output']:,} tokens"
        if who == "react" and usage["rag"] and usage["rag"]["calls"] and cost(usage["rag"]):
            note += f" · {cost(u) / cost(usage['rag']):.0f}× RAG"
        col.metric(f"{name} cost · {u['calls']} LLM calls", f"${cost(u):.4f}", note,
                   delta_color="off", delta_arrow="off",
                   help=f"{u['input']:,} input ({u['cached']:,} cached) + {u['output']:,} output tokens "
                        f"at ${PRICE_IN}/${PRICE_CACHED}/${PRICE_OUT} per 1M (input/cached/output).")

    with st.container(border=True):
        st.subheader("🧭 The path each agent took")
        path_rag, path_react = st.columns([1, 1.4], gap="large")
        path_rag.caption("RAG")
        path_rag.graphviz_chart(rag_path_dot(rec["rag"]["route"]), width="content")
        path_react.caption(f"ReAct · {stats.get('tools', 0)} tool calls")
        path_react.graphviz_chart(react_path_dot(stats.get("path", []), react_answer), width="content")

    golden(q, {"RAG": plain_answer, "ReAct": react_answer})

    if not replay:
        gold = GOLDEN.get(q)
        good = not react_answer.startswith("Stopped:") and (
            gold is None or all(passed for _, passed in ra.check_answer(react_answer, gold)))
        if good:  # saved silently; a run that misses a golden fact never replaces a good recording
            save_run(rec)
