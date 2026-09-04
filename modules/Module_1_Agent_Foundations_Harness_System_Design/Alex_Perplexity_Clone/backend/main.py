"""
4-level chatbot demo.

One chatbot architecture, capabilities layered on by `level`:
  1: LLM only              -> user message in, response out. No history.
  2: + conversation history-> full message list sent to the LLM.
  3: + web search tool      -> LLM can call web_search when it needs current info.
  4: + RAG                  -> query embedded, nearest chunks retrieved from a
                               prebuilt index and injected as context.

Responses stream token-by-token over SSE (`/api/chat/stream`).
"""
import json
import os
import threading

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from rag import (
    get_store,
    warm_store,
    store_status,
    document_summary,
    chunk_breakdown,
    score_all,
)
from tools import WEB_SEARCH_TOOL, web_search
import gate

load_dotenv()

MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-5")
MAX_TOKENS = 1024

client = Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))

app = FastAPI(title="Alex")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def warm_rag_index():
    """Build the PDF vector index in the background at boot, so the first
    Level 4 question during a demo doesn't wait on a 7.5MB PDF parse."""
    threading.Thread(target=warm_store, daemon=True).start()


# --- Access gate -----------------------------------------------------------
# See gate.py. Disabled entirely when APP_PASSWORD is unset, which is the local
# default, so nothing here changes how the demo runs on a laptop.
gate.install(app)


class ChatMessage(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    level: int
    message: str
    history: list[ChatMessage] = []


# --- Prompt engineering: hand-written, identical on every call, every level.
BASE_SYSTEM = (
    "You are Alex, an AI assistant built to show how an assistant is actually "
    "assembled. Be direct and concise. Prefer plain language over jargon. If "
    "you do not know something, say so plainly instead of guessing. When you "
    "are asked who you are, say you are Alex."
)

PERSONA_PART = {
    "label": "Persona & instructions",
    "kind": "Prompt engineering",
    "note": "Hand-written by us. Identical on every call, at every level.",
    "text": BASE_SYSTEM,
    "origin": "system",
}

# --- Prompt engineering for Level 3: how to use whatever the search returns.
SEARCH_RULES = (
    "You have a web_search tool. Call it only when the answer needs current, "
    "real-time, or external information you cannot be confident about "
    "otherwise. Each search result comes with a URL. When you use a result, "
    "cite it inline as a markdown link on the relevant fact, like "
    "[Source name](https://example.com). Put the link on the specific claim it "
    "supports rather than collecting links at the end. Never invent a URL — "
    "only use URLs that appear in the search results you were given."
)

SEARCH_PART = {
    "label": "Search & citation rules",
    "kind": "Prompt engineering",
    "note": "Hand-written by us. Tells the model when to search and how to cite what comes back.",
    "text": SEARCH_RULES,
    "origin": "system",
}

LEVEL3_SYSTEM = BASE_SYSTEM + "\n\n" + SEARCH_RULES

# --- Also prompt engineering: how to choose between the two sources at Level 4.
RAG_RULES = (
    "You have two sources of truth, in strict priority order.\n\n"
    "1. THE DOCUMENTS. The numbered excerpts supplied below were retrieved from "
    "the internal knowledge base - a project management reference plus the ACME "
    "program's contract, statement of work, meeting notes, and risk register. "
    "Always prefer these. Name the document you are drawing from. When you use "
    "one, cite it inline with bracket notation like [1] or [2][3], placed right "
    "after the sentence it supports.\n\n"
    "2. THE WEB. If the excerpts do not contain what was asked — a current "
    "event, or any topic this document does not cover — you MUST call the "
    "web_search tool before responding. Never tell the user you cannot answer "
    "until you have actually searched. Live data such as weather, prices, "
    "scores, and today's news IS searchable - search for it rather than "
    "declining. When you use a search result, cite it "
    "inline as a markdown link like [Source name](https://example.com), never "
    "as a bracket number.\n\n"
    "Keep the two straight: never present a web result as if it came from the "
    "document, or the reverse, and say which one you used. Only after a search "
    "has come back empty or irrelevant may you say you could not find an "
    "answer. Do not invent facts or URLs.\n\n"
    "The conversation history may be used to understand WHAT the user is "
    "referring to (for example, resolving \"it\" or \"the third one\" in a "
    "follow-up question), but never as a source of facts."
)

NO_CHUNKS_MESSAGE = (
    "(no excerpt in the knowledge base was similar enough to this question)"
)


def jsonable(value):
    """The tool-use loop keeps SDK block objects in the message list because the
    API needs them; the debug panel needs plain JSON."""
    if isinstance(value, list):
        return [jsonable(v) for v in value]
    if isinstance(value, dict):
        return {k: jsonable(v) for k, v in value.items()}
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    return value


def api_request(system, messages, tools=None) -> dict:
    """The request body as the SDK will send it.

    The debug panel shows this verbatim, because it is the whole argument: there
    is no retrieval channel and no memory field. `system` is one string that we
    concatenated, `messages` is a list we re-send in full every turn, and
    everything RAG contributes is already inside that first string.
    """
    body = {
        "model": MODEL,
        "max_tokens": MAX_TOKENS,
        "system": system,
        "messages": jsonable(messages),
    }
    if tools is not None:
        body["tools"] = tools
    return body


def format_search_results(result: dict) -> str:
    """Hand the model readable, clearly-attributed results. The URL has to be
    right next to the text it belongs to, or the model cannot cite it."""
    results = result.get("results", [])
    if not results:
        return "No results were returned for query: %s" % result.get("query", "")
    lines = ['Search results for: "%s"' % result.get("query", "")]
    if result.get("mocked"):
        lines.append("(these are MOCKED results - no TAVILY_API_KEY is configured)")
    for i, r in enumerate(results, start=1):
        lines.append(
            "\n[%d] %s\nURL: %s\n%s"
            % (i, r.get("title", "(untitled)"), r.get("url", "(no url)"), r.get("content", ""))
        )
    return "\n".join(lines)


def transcript(system_parts, messages, history_count: int = 0) -> dict:
    """The teaching payload: the literal, fully-concatenated input the model
    receives on the final call. Every level does the same thing underneath -
    it just concatenates more text into the same message list."""
    system_parts = system_parts or []
    parts = []
    for sp in system_parts:
        parts.append(
            "===== SYSTEM PROMPT · %s (%s) =====\n%s"
            % (sp["label"], sp["kind"], sp["text"])
        )
    for i, m in enumerate(messages, start=1):
        content = m["content"]
        if not isinstance(content, str):
            content = json.dumps(jsonable(content), indent=2)
        parts.append(
            "===== MESSAGE %d of %d  ROLE: %s =====\n%s"
            % (i, len(messages), m["role"].upper(), content)
        )
    text = "\n\n".join(parts)
    # Every row is tagged with where it came from, because that is the lesson:
    # nothing is remembered, it is re-sent.
    rows = []
    for sp in system_parts:
        rows.append({
            "role": "system",
            "content": sp["text"],
            "origin": sp.get("origin", "system"),
            "label": sp["label"],
            "kind": sp["kind"],
            "note": sp.get("note", ""),
        })

    for i, m in enumerate(messages):
        origin = "history" if i < history_count else "new"
        content = m["content"]
        if isinstance(content, str):
            rows.append({"role": m["role"], "content": content, "origin": origin})
            continue
        # A turn whose content is a block list: split it out so the panel can
        # label a tool request and a tool result as the separate things they are.
        for blk in jsonable(content):
            kind = blk.get("type") if isinstance(blk, dict) else None
            if kind == "text":
                rows.append({"role": m["role"], "content": blk.get("text", ""), "origin": "turn"})
            elif kind == "tool_use":
                rows.append({
                    "role": "tool_use",
                    "content": json.dumps(blk.get("input", {}), indent=2),
                    "tool": blk.get("name", ""),
                    "origin": "turn",
                })
            elif kind == "thinking":
                rows.append({"role": "thinking", "content": blk.get("thinking", ""), "origin": "turn"})
            elif kind == "redacted_thinking":
                rows.append({
                    "role": "thinking",
                    "content": "(reasoning block withheld by the API)",
                    "origin": "turn",
                })
            elif kind == "tool_result":
                rows.append({
                    "role": "tool_result",
                    "content": str(blk.get("content", "")),
                    "origin": "turn",
                })
            else:
                rows.append({"role": m["role"], "content": json.dumps(blk, indent=2), "origin": origin})
    rows = [r for r in rows if str(r.get("content", "")).strip()]
    return {
        "text": text,
        "rows": rows,
        "characters": len(text),
        "message_count": len(messages),
        "has_system_prompt": bool(system_parts),
        "approx_tokens": len(text) // 4,
    }


def sse(event_type: str, **payload) -> str:
    body = json.dumps({"type": event_type, **jsonable(payload)}, default=str)
    return f"data: {body}\n\n"


def as_dicts(history: list[ChatMessage]) -> list[dict]:
    return [{"role": m.role, "content": m.content} for m in history]


def stream_text(**kwargs):
    """Yield SSE text deltas from a streaming Claude call, then the final message."""
    with client.messages.stream(model=MODEL, max_tokens=MAX_TOKENS, **kwargs) as stream:
        for delta in stream.text_stream:
            yield sse("text", text=delta)
        final = stream.get_final_message()
    yield final  # sentinel: last item is the message object, not an SSE string


def run_tool_loop(system, messages, debug):
    """Stream the model's reply, running web_search whenever it asks, until it
    stops asking. Shared by Level 3 and Level 4 - the loop is identical, only
    the system prompt differs."""
    while True:
        final = None
        for item in stream_text(system=system, messages=messages, tools=[WEB_SEARCH_TOOL]):
            if isinstance(item, str):
                yield item
            else:
                final = item

        if final.stop_reason != "tool_use":
            break

        messages.append({"role": "assistant", "content": final.content})
        tool_results = []
        for block in final.content:
            if block.type == "tool_use" and block.name == "web_search":
                query = block.input.get("query", "")
                yield sse("tool_call", tool="web_search", query=query, status="running")
                result = web_search(query)
                call = {
                    "tool": "web_search",
                    "query": query,
                    "mocked": result.get("mocked", False),
                    "results": result.get("results", []),
                }
                debug["tool_calls"].append(call)
                yield sse(
                    "tool_call",
                    tool="web_search",
                    query=query,
                    status="done",
                    mocked=call["mocked"],
                    result_count=len(call["results"]),
                )
                tool_results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": format_search_results(result),
                    }
                )
        messages.append({"role": "user", "content": tool_results})


def run_level1(message: str):
    messages = [{"role": "user", "content": message}]
    debug = {
        "level": 1,
        "description": "Only the current message is sent. No history, no tools, no retrieval.",
        "api_request": api_request(BASE_SYSTEM, messages),
        "llm_input": transcript([PERSONA_PART], messages, 0),
        "what_got_added": "Nothing. Just the one message you typed. Level 1 never appends earlier turns, so each call starts from scratch.",
    }
    yield sse("debug", debug=debug)
    for item in stream_text(system=BASE_SYSTEM, messages=messages):
        if isinstance(item, str):
            yield item


def run_level2(message: str, history: list[ChatMessage]):
    messages = as_dicts(history)
    messages.append({"role": "user", "content": message})
    debug = {
        "level": 2,
        "description": "Full conversation history plus the current message is sent.",
        "conversation_history_included": as_dicts(history),
        "api_request": api_request(BASE_SYSTEM, messages),
        "llm_input": transcript([PERSONA_PART], messages, len(history)),
        "what_got_added": (
            "%d earlier message(s) were concatenated in front of your new one. "
            "The model has no memory - the history is simply re-sent every turn."
            % len(history)
        ),
    }
    yield sse("debug", debug=debug)
    for item in stream_text(system=BASE_SYSTEM, messages=messages):
        if isinstance(item, str):
            yield item


def run_level3(message: str, history: list[ChatMessage]):
    messages = as_dicts(history)
    messages.append({"role": "user", "content": message})

    debug = {
        "level": 3,
        "description": "History is sent along with a web_search tool the model may call.",
        "api_request": api_request(LEVEL3_SYSTEM, messages, [WEB_SEARCH_TOOL]),
        "tool_calls": [],
    }

    yield from run_tool_loop(LEVEL3_SYSTEM, messages, debug)

    debug["final_context"] = jsonable(messages)
    debug["llm_input"] = transcript([PERSONA_PART, SEARCH_PART], messages, len(history))
    if debug["tool_calls"]:
        debug["what_got_added"] = (
            "The model asked for a search, the results came back as text, and that "
            "text was appended to the same message list. Then the whole thing was "
            "sent again. A tool call is just more concatenated text."
        )
    else:
        debug["tool_calls_note"] = "No tool was called - the model answered directly."
        debug["what_got_added"] = "Nothing extra - the model chose not to search."

    yield sse("debug", debug=debug)


def build_retrieval_query(message: str, history: list[ChatMessage]) -> str:
    """Follow-ups like "what about the third one?" carry almost no retrievable
    terms on their own, so prepend the recent user turns to the search query."""
    prior = [m.content for m in history if m.role == "user"][-2:]
    return " ".join(prior + [message]) if prior else message


def run_level4(message: str, history: list[ChatMessage]):
    store = get_store()
    query = build_retrieval_query(message, history)
    retrieved = store.search(query)

    sources = [{**c, "source_number": i + 1} for i, c in enumerate(retrieved)]
    yield sse("sources", sources=sources)

    context_text = (
        "\n\n".join(
            f"[{s['source_number']}] {s.get('document', 'document')} "
            f"(section/page {s['page']}, similarity {s['score']})\n{s['text']}"
            for s in sources
        )
        or NO_CHUNKS_MESSAGE
    )

    # Prompt engineering (persona + rules) and context engineering (the
    # excerpts we just looked up) end up in the same system string.
    system_parts = [
        PERSONA_PART,
        {
            "label": "Grounding rules",
            "kind": "Prompt engineering",
            "note": "Hand-written by us. Sets the priority order: document first, web only as a fallback.",
            "text": RAG_RULES,
            "origin": "system",
        },
        {
            "label": "Retrieved excerpts",
            "kind": "Context engineering",
            "note": "Not written by us - looked up per question and pasted in as plain text.",
            "text": "Retrieved excerpts:\n" + context_text,
            "origin": "context",
        },
    ]
    system_prompt = "\n\n".join(sp["text"] for sp in system_parts)

    messages = as_dicts(history)
    messages.append({"role": "user", "content": message})

    debug = {
        "level": 4,
        "description": "Chunks are retrieved and injected as context, and web_search is still available when the document falls short.",
        "pipeline": "User Question -> Embedding -> Vector Search -> Relevant Chunks -> LLM (+ web_search fallback) -> Answer",
        "query_embedded": query,
        "query_rewritten_from_history": query != message,
        "min_similarity_threshold": store.min_score,
        "retrieved_chunks": sources,
        "system_prompt_with_context": system_prompt,
        "api_request": api_request(system_prompt, messages, [WEB_SEARCH_TOOL]),
        "tool_calls": [],
    }

    yield from run_tool_loop(system_prompt, messages, debug)

    debug["final_context"] = jsonable(messages)
    debug["llm_input"] = transcript(system_parts, messages, len(history))
    if debug["tool_calls"]:
        debug["what_got_added"] = (
            "%d excerpt(s) were pasted into the system prompt, and the document "
            "did not cover the question - so the model also searched the web and "
            "that result was appended to the message list. Both sources are just "
            "concatenated text." % len(sources)
        )
    else:
        debug["what_got_added"] = (
            "%d document excerpt(s) were pasted into the system prompt as plain text. "
            "The model did not need to search the web. There is no special "
            "'retrieval' channel - RAG is string concatenation with a search step "
            "in front of it." % len(sources)
        )
    yield sse("debug", debug=debug)


LEVELS = {1: run_level1, 2: run_level2, 3: run_level3, 4: run_level4}


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    def events():
        runner = LEVELS.get(req.level)
        if runner is None:
            yield sse("error", message="Invalid level.")
            return
        try:
            if req.level == 1:
                yield from runner(req.message)
            else:
                yield from runner(req.message, req.history)
        except Exception as exc:
            yield sse("error", message=str(exc))
        yield sse("done")

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


class ScoreRequest(BaseModel):
    query: str
    document: str | None = None


@app.get("/api/rag/chunks")
def rag_chunks(document: str, limit: int = 12):
    """How one document was split up - for the 'How RAG works' walkthrough."""
    return chunk_breakdown(document, limit=limit)


@app.post("/api/rag/score")
def rag_score(req: ScoreRequest):
    """Every chunk scored against a query, ranked, with the cutoff marked."""
    return score_all(req.query, document=req.document)


@app.get("/api/documents")
def documents():
    """What Level 4 actually has indexed - shown in the sidebar."""
    status = store_status()
    return {
        "ready": status.get("ready", False),
        "total_chunks": status.get("chunks", 0),
        "documents": document_summary(),
    }


@app.get("/api/health")
def health():
    return {"status": "ok", "model": MODEL, "rag_index": store_status()}


class NoCacheStaticFiles(StaticFiles):
    """Dev-friendly static file serving: never let the browser cache these,
    so edits to index.html/app.js/styles.css always show up on refresh."""

    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
app.mount("/", NoCacheStaticFiles(directory=frontend_dir, html=True), name="frontend")
