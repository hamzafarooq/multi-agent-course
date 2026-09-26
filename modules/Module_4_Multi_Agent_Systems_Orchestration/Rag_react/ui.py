"""Shared by the Streamlit pages: pricing, markdown escaping, the how-it-works diagrams, saved-run scoring."""

import json
import os
import re

import react_agent as ra

HERE = os.path.dirname(os.path.abspath(__file__))
# gpt-5.6-luna list prices, USD per 1M tokens (OpenAI, as of 2026-07-30): input, cached input, output.
PRICE_IN, PRICE_CACHED, PRICE_OUT = 0.20, 0.02, 1.20


def cost(usage):
    """USD for one agent's token tally; None for runs recorded before token counting."""
    if not usage or not usage.get("calls"):
        return None
    fresh = usage["input"] - usage["cached"]
    return (fresh * PRICE_IN + usage["cached"] * PRICE_CACHED + usage["output"] * PRICE_OUT) / 1e6


def md(text: str) -> str:
    """Turn the model's \\[ \\] / \\( \\) LaTeX into Streamlit's $$ / $, and escape $ amounts outside it."""
    out = []
    for part in re.split(r"(\\\[.*?\\\]|\\\(.*?\\\))", text, flags=re.S):
        if part.startswith("\\["):
            out.append(f"$${part[2:-2]}$$")
        elif part.startswith("\\("):
            out.append(f"${part[2:-2]}$")
        else:
            out.append(part.replace("$", r"\$"))
    return "".join(out)


def tools_used(events) -> list:
    return [m.group(1).strip() for _, kind, text, _ in events
            if kind == "reply" and "Final Answer:" not in text
            for m in [re.search(r"Action:\s*(.+)", text)] if m]


def saved_results() -> list:
    """[(gold, run, rag_checks, react_checks, react_tools)] for each question with a saved run."""
    golden, out = ra.load_golden(), []
    demo_dir = os.environ.get("DEMO_DIR", os.path.join(HERE, "demo_runs"))
    for q in ra.HARD_QUESTIONS:
        gold = golden.get(q)
        try:
            with open(os.path.join(demo_dir, f"{gold['id']}.json")) as f:
                run = json.load(f)
        except (OSError, ValueError, TypeError):
            continue
        out.append((gold, run, ra.check_answer(run["rag"]["answer"], gold),
                    ra.check_answer(run["react"]["answer"], gold), tools_used(run["react"]["events"])))
    return out


def facts(results: list, i: int) -> tuple:
    """(passed, total) key facts across results, for column i (2 = RAG, 3 = ReAct)."""
    return sum(sum(p for _, p in r[i]) for r in results), sum(len(r[i]) for r in results)


DOT_STYLE = ('bgcolor="transparent"; nodesep=0.3; ranksep=0.32; '
             'node [shape=box, style="rounded,filled", fontname="Helvetica", fontsize=11, '
             'color="#E2E8F0", fillcolor="#FFFFFF", fontcolor="#0F172A", penwidth=1.2, margin="0.18,0.08"]; '
             'edge [color="#94A3B8", arrowsize=0.7, fontname="Helvetica", fontsize=9, fontcolor="#64748B"];')

RAG_HOW = f"""digraph {{ {DOT_STYLE}
  q [label="Question"];
  router [label="Router (LLM)\\npicks ONE source", fillcolor="#E0F2FE", color="#7DD3FC"];
  src [label="10-K  ·  OpenAI docs  ·  web", fillcolor="#F8FAFC"];
  top [label="One retrieval: top-3 chunks"];
  llm [label="LLM writes the answer"];
  a [label="Answer", fillcolor="#DCFCE7", color="#86EFAC"];
  q -> router -> src -> top -> llm -> a;
}}"""

REACT_HOW = f"""digraph {{ {DOT_STYLE}
  q [label="Question"];
  t [label="Thought\\nwhat do I still need?", fillcolor="#F3E8FF", color="#D8B4FE"];
  act [label="Action: call ONE tool\\nsearch_10k · docs · web · calculator", fillcolor="#DBEAFE", color="#93C5FD"];
  o [label="Observation\\nraw chunks / web results / number", fillcolor="#FEF3C7", color="#FCD34D"];
  a [label="Final answer\\n(every figure from an Observation)", fillcolor="#DCFCE7", color="#86EFAC"];
  q -> t -> act -> o;
  o -> t [label=" repeat", style=dashed, color="#A855F7", fontcolor="#7E22CE", constraint=false];
  o -> a [style=invis];
  t -> a [label=" enough to answer", constraint=false];
}}"""
