"""
Minimal ReAct (Reason + Act) loop on top of the Agentic RAG pipeline in rag_helpers.py.

The plain RAG router makes ONE routing decision, runs ONE retrieval and writes ONE answer.
The ReAct agent instead loops:

    Thought  -> what do I still need to know?
    Action   -> call a tool (10-K search, OpenAI docs search, web search, calculator)
    Observation -> the tool's result, fed back to the model
    ... repeat ...
    Final Answer

Usage (in the notebook, after init_rag(...) has run):

    from react_agent import react_agent, HARD_QUESTIONS
    react_agent(HARD_QUESTIONS[0])
"""

import asyncio
import inspect
import re

from qdrant_client import models

import rag_helpers

MODEL = "gpt-5.6-luna"  # same model the notebook uses
MAX_STEPS = 10


# ── Tools ─────────────────────────────────────────────────────────────────────
# Each tool takes a string and returns a string. They reuse the existing RAG pipeline's
# embedder and Qdrant client, but return the RAW retrieved chunks rather than an LLM
# summary of them: a summarising LLM can slip memorised figures into the Observation.

COMPANIES = {"uber": "Uber Technologies, Inc.", "lyft": "Lyft, Inc."}
# Fiscal years labelled in the 10k_data collection (metadata.fiscal_year).
TEN_K_YEARS = {"Uber Technologies, Inc.": [2021], "Lyft, Inc.": [2020, 2021, 2022]}


def _run(result):
    """rag_helpers mixes sync and async functions; handle both."""
    return asyncio.run(result) if inspect.iscoroutine(result) else result


def _search_chunks(collection: str, query: str, conditions=None, limit: int = 3) -> str:
    hits = _run(rag_helpers._qdrant.query_points(
        collection_name=collection,
        query=rag_helpers._get_text_embeddings(query),
        query_filter=models.Filter(must=conditions) if conditions else None,
        limit=limit,
    ))
    if not hits.points:
        return "No matching chunks."
    chunks = []
    for i, p in enumerate(hits.points, 1):
        meta = p.payload.get("metadata", {})
        label = f"{meta['company']} FY{meta.get('fiscal_year') or '?'}" if "company" in meta else "OpenAI docs"
        chunks.append(f"[{i}] ({label}) {' '.join(p.payload['content'].split())}")
    return "\n\n".join(chunks)


def search_10k(query: str) -> str:
    """Filtered to ONE company, and to the latest fiscal year named in the query (if any)."""
    companies = [name for key, name in COMPANIES.items() if key in query.lower()]
    if len(companies) != 1:
        return "Error: name exactly ONE company (Uber or Lyft) in each search."
    company = companies[0]
    conditions = [models.FieldCondition(key="metadata.company", match=models.MatchValue(value=company))]

    years = [int(y) for y in re.findall(r"\b(20\d\d)\b", query)]
    if years:
        year = max(years)  # a 10-K also reports the prior years, so use the latest one named
        if year not in TEN_K_YEARS[company]:
            return (f"There is no {company} 10-K for fiscal year {year} in the collection. "
                    f"Available fiscal years: {TEN_K_YEARS[company]}.")
        conditions.append(models.FieldCondition(key="metadata.fiscal_year", match=models.MatchValue(value=year)))

    return _search_chunks("10k_data", query, conditions, limit=6)  # top 3 often cut off the right chunk


def search_openai_docs(query: str) -> str:
    return _search_chunks("opnai_data", query)


def search_web(query: str) -> str:
    return str(_run(rag_helpers.get_internet_content(query)))


def calculator(expression: str) -> str:
    if not re.fullmatch(r"[\d\s.+\-*/()%]+", expression):
        return "Error: only numbers and + - * / ( ) % are allowed."
    try:
        return str(eval(expression, {"__builtins__": {}}))
    except Exception as e:
        return f"Error: {e}"


TOOLS = {
    "search_10k": (search_10k, "Search the 10-K filings (Uber FY2021; Lyft FY2020-FY2022). Returns raw excerpts. "
                               "Search for ONE fact per call with a SHORT query: ONE company, the fiscal year and a few "
                               "key words, e.g. 'Lyft 2022 total revenue'."),
    "search_openai_docs": (search_openai_docs, "Search the OpenAI Agents SDK documentation."),
    "search_web": (search_web, "Search the live internet for current or external information."),
    "calculator": (calculator, "Evaluate an arithmetic expression, e.g. (17455 - 11139) / 11139 * 100"),
}


# ── Prompt ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = f"""You are a ReAct agent. Answer the question by reasoning step by step and using tools.

Tools:
{chr(10).join(f"- {name}: {desc}" for name, (_, desc) in TOOLS.items())}

On every turn, respond in EXACTLY one of these two formats and nothing else:

Thought: <your reasoning about what to do next>
Action: <one tool name from the list>
Action Input: <the input for the tool>

or, once you have enough information:

Thought: <your final reasoning>
Final Answer: <the answer to the original question>

Rules:
- Do ONE action per turn, then stop. The Observation will be given to you.
- Never write an Observation yourself.
- Break multi-part questions into several focused searches.
- Use the calculator for any arithmetic instead of doing it in your head.
- In calculations, use the exact figures from the financial statements (e.g. revenue 17,455 in $ millions),
  not rounded figures from the narrative text (e.g. "$17.5 billion").
- In the Final Answer, state every figure you used (with its source) as well as the result.
- Always use at least one tool before a Final Answer. Never answer from memory.
- Only state facts and figures that appear in an Observation. If the documents don't contain
  something, say so plainly (or use search_web when current or external data is appropriate).
- If an Observation doesn't contain what you need, rephrase and search again (e.g. use the
  filing's own wording) before concluding the information isn't there.
"""


# ── The loop ──────────────────────────────────────────────────────────────────

def _parse(text: str):
    """Return ('final', answer) or ('action', tool, tool_input) or ('error', msg)."""
    final = re.search(r"Final Answer:\s*(.*)", text, re.DOTALL)
    if final:
        return ("final", final.group(1).strip())
    action = re.search(r"Action:\s*(.+)", text)
    action_input = re.search(r"Action Input:\s*(.*)", text, re.DOTALL)
    if action and action_input:
        return ("action", action.group(1).strip(), action_input.group(1).strip())
    return ("error", "Could not parse. Use the Thought/Action/Action Input or Final Answer format.")


# A Final Answer saying the documents lack something, e.g. "the excerpt does not state the purchase price".
GAVE_UP = re.compile(r"(?i)(does|do|did) not (state|provide|contain|include|disclose)|not (available|provided|stated)"
                     r"|cannot be (calculated|determined)|unable to (determine|find|calculate)")


def react_agent(question: str, max_steps: int = MAX_STEPS, verbose: bool = True, on_step=None) -> str:
    """on_step(step, kind, text), if given, is called with kind 'reply' or 'observation' (used by app.py)."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Question: {question}"},
    ]
    if verbose:
        print(f"\n{'=' * 70}\n❓ {question}\n{'=' * 70}")

    used_tool, searches = False, 0
    for step in range(1, max_steps + 1):
        try:
            reply = rag_helpers._openaiclient.chat.completions.create(
                model=MODEL, messages=messages
            ).choices[0].message.content
        except Exception as e:  # e.g. rate limit or a rejected request: stop cleanly, keep the trace
            return f"Stopped: model API error at step {step}: {e}"

        # If the model runs ahead and writes its own Observation, cut it off.
        reply = reply.split("Observation:")[0].strip()
        messages.append({"role": "assistant", "content": reply})

        if verbose:
            print(f"\n--- Step {step} ---\n{reply}")
        if on_step:
            on_step(step, "reply", reply)

        parsed = _parse(reply)
        if parsed[0] == "final" and not used_tool:
            parsed = ("error", "You have not used any tool yet. Call a tool before giving a Final Answer.")
        elif parsed[0] == "final" and searches < 3 and GAVE_UP.search(parsed[1]):
            parsed = ("error", "Before concluding the documents don't contain it, search again with a SHORT, "
                               "differently-worded query that uses the filing's own wording.")
        if parsed[0] == "final":
            if verbose:
                print(f"\n✅ Done in {step} step(s).")
            return parsed[1]

        if parsed[0] == "error":
            observation = parsed[1]
        else:
            _, tool, tool_input = parsed
            if tool not in TOOLS:
                observation = f"Unknown tool '{tool}'. Choose from: {', '.join(TOOLS)}"
            else:
                used_tool = True
                searches += tool.startswith("search_")
                try:
                    observation = TOOLS[tool][0](tool_input)
                except Exception as e:
                    observation = f"Tool error: {e}"

        observation = observation[:13000]  # room for 6 raw chunks, but keep the context small
        if verbose:
            print(f"\nObservation: {observation}")
        if on_step:
            on_step(step, "observation", observation)
        messages.append({"role": "user", "content": f"Observation: {observation}"})

    return "Stopped: reached max steps without a final answer."


# ── Questions a single-shot RAG call can't answer well, but a ReAct loop can ──────
# Each needs several retrievals, retrievals from different sources, and/or arithmetic.

HARD_QUESTIONS = [
    # Chained: find WHICH company was acquired, then its price, then revenue, then divide.
    # (One retrieval on the full question doesn't return the acquisition chunk.)
    "According to Uber's 2021 10-K, which freight logistics company did Uber acquire in 2021, how much did "
    "Uber pay for it, and what percentage of Uber's 2021 revenue was that price?",

    # Chained: the answer to part 1 (which company) decides what to look up in part 2.
    "Which company reported higher annual revenue in its 10-K: Uber (2021) or Lyft (2022)? For that company, "
    "find its research and development expense for the same year and express it as a percentage of its revenue.",

    # Two figures from different sections of the filing (debt note + income statement), then arithmetic.
    # Obscure enough that the model can't fill the gap from memory.
    "According to Lyft's 2022 10-K, what was Lyft's long-term debt, net of current portion, at "
    "December 31, 2022, and what percentage of Lyft's 2022 revenue is that?",

    # Mixes the 10-K collection with live web data. The router picks only ONE source.
    "Uber reported its 2021 revenue in its 10-K. Using Uber's current market cap from the web, "
    "what is its approximate price-to-sales ratio against that 2021 revenue?",

    # Mixes OpenAI docs with 10-K content: design question grounded in two sources.
    "Name two risk factors from Uber's 2021 10-K, then explain which OpenAI Agents SDK feature "
    "(e.g. guardrails, handoffs, tracing) would help an agent that answers questions about those risks.",

    # 10-K figure first, then a web lookup that builds on it, then arithmetic.
    "According to its FY2021 10-K, how many MAPCs did Uber have in Q4 2021? Then look up on the web how many "
    "MAPCs Uber reported for Q2 2026, and calculate how much that metric has grown since Q4 2021.",
]


# ── Golden answers ────────────────────────────────────────────────────────────
# golden_answers.json holds the expected answer, key facts (as regexes) and 10-K quotes
# for each question. check_answer() reports which key facts an answer contains.

def load_golden(path: str = None) -> dict:
    import json, os
    path = path or os.path.join(os.path.dirname(os.path.abspath(__file__)), "golden_answers.json")
    return {g["question"]: g for g in json.load(open(path))["questions"]}


def check_answer(answer: str, gold: dict) -> list:
    """[(fact, passed)] for each key fact; a fact passes when >= fact['min'] of its regexes match."""
    text = answer.replace("**", "").replace("\\$", "$").replace("\\%", "%")
    return [(f, sum(bool(re.search(p, text)) for p in f["accept"]) >= f.get("min", 1)) for f in gold["key_facts"]]


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv

    load_dotenv()
    rag_helpers.init_rag(
        openai_api_key=os.getenv("openai_api_key") or os.getenv("OPENAI_API_KEY"),
        serp_api_key=os.getenv("serp_api_key") or os.getenv("SERP_API_KEY"),
        qdrant_path=os.path.join(os.getcwd(), "Agentic_RAG", "qdrant_data"),
    )
    for q in HARD_QUESTIONS[:2]:
        print(f"\n🧾 FINAL: {react_agent(q)}")
