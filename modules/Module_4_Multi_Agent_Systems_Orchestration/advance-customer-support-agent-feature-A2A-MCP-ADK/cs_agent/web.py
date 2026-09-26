"""Minimal Perplexity-style web frontend for the customer-support agent.

Wraps the same pipeline the CLI uses — input sanitization -> A2A Security Judge ->
ADK agent (+ MCP tools, Mem0 memory) -> A2A Data Masker — behind a tiny FastAPI API,
and serves a single-page chat UI with markdown rendering and visible tool "steps".

Run it via:  ./run.sh web      (or: python -m cs_agent.web)
Requires the same services as the CLI: Postgres, MCP Toolbox (:5000), A2A (:10002/:10003).
"""

import warnings
warnings.filterwarnings("ignore")
warnings.showwarning = lambda *a, **k: None

import asyncio
import json
import logging
import os
import sys
import time
import urllib.request

logging.getLogger().setLevel(logging.ERROR)

_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
for p in (_this_dir, _project_root):
    if p not in sys.path:
        sys.path.insert(0, p)

import yaml
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from memory import mem0
from prompts import GUARDRAIL_PROMPT_INSTRUCTION, SQL_PROMPT_INSTRUCTION
from greet import authenticate_user
from cs_agent.security.sanitizer import sanitize_input
from cs_agent.a2a.client import call_a2a_agent
from telemetry import init_telemetry
from openinference.semconv.trace import SpanAttributes

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)
tracer = init_telemetry()

A2A_JUDGE_HOST = os.getenv("A2A_JUDGE_HOST", "localhost")
A2A_JUDGE_PORT = int(os.getenv("A2A_JUDGE_PORT", "10002"))
A2A_MASK_HOST = os.getenv("A2A_MASK_HOST", "localhost")
A2A_MASK_PORT = int(os.getenv("A2A_MASK_PORT", "10003"))

toolbox_client = ToolboxSyncClient(url="http://127.0.0.1:5000")
database_tools = toolbox_client.load_toolset("cs_agent_tools")

PHOENIX_URL = "http://localhost:6006"
MEMORY_TOP_K = 5
MEMORY_MIN_SCORE = 0.25
MEMORY_MAX_CHARS = 500  # Mem0's merge step can loop and produce 30k-char memories


def _tool_catalogue() -> dict:
    with open(os.path.join(_project_root, "mcp_toolbox", "tools.yaml")) as f:
        cfg = yaml.safe_load(f)
    out = {}
    for name, t in cfg["tools"].items():
        stmt = t.get("statement", "").strip()
        out[name] = {
            "kind": "MCP",
            "access": "READ" if stmt.upper().startswith("SELECT") else "WRITE",
            "path": ["Gemini function call", "ADK", "toolbox-core", "MCP tools/call", "Toolbox :5000", "PostgreSQL"],
            "runs": f"{t['kind']} on {t['source']}",
            "statement": stmt,
            "params": [p["name"] for p in t.get("parameters", [])],
        }
    return out


TOOLS = _tool_catalogue()
_phoenix_project = None


def _trace_url(trace_id: str) -> str:
    global _phoenix_project
    if _phoenix_project is None:
        try:
            with urllib.request.urlopen(f"{PHOENIX_URL}/v1/projects", timeout=2) as r:
                projects = json.load(r)["data"]
            _phoenix_project = next(p["id"] for p in projects if p["name"] == "default")
        except Exception:
            return f"{PHOENIX_URL}/projects"
    return f"{PHOENIX_URL}/projects/{_phoenix_project}/traces/{trace_id}"

session_service = InMemorySessionService()
_runners: dict[str, Runner] = {}   # user_id -> Runner

guardrail_runner = Runner(
    agent=LlmAgent(
        model="gemini-2.5-flash",
        name="guardrail_agent",
        description="Decides whether a user request is safe and in-scope for customer support.",
        instruction=GUARDRAIL_PROMPT_INSTRUCTION,
    ),
    app_name="guardrail",
    session_service=session_service,
)

app = FastAPI(title="Customer Support Agent")


class LoginReq(BaseModel):
    email: str
    password: str


class ChatReq(BaseModel):
    user_id: str
    message: str


class LogoutReq(BaseModel):
    user_id: str


_CLI_MEMORY_RULE = """1. **Search Memory (Mem0):**
   - ALWAYS use the `search_memory` function to recall past conversations and
     user preferences using the fixed USER_ID above.
   - Do not invent or change USER_ID values; it is controlled by the system."""
_WEB_MEMORY_RULE = """1. **Memory (Mem0):**
   - The system recalls memories from Mem0 before every turn. When any are relevant,
     the message starts with "Relevant memories about this customer (from Mem0):".
   - Use them for preferences and past context. For order facts (status, items,
     totals), trust the tools over memories, since memories can be out of date."""
assert _CLI_MEMORY_RULE in SQL_PROMPT_INSTRUCTION
WEB_PROMPT_INSTRUCTION = SQL_PROMPT_INSTRUCTION.replace(_CLI_MEMORY_RULE, _WEB_MEMORY_RULE)


def _build_runner(user_id: str) -> Runner:
    agent = LlmAgent(
        model="gemini-2.5-flash",
        name="customer_support_assistant",
        description="Customer support agent for order questions and requests.",
        instruction=WEB_PROMPT_INSTRUCTION.format(USER_ID=user_id),
        tools=[*database_tools],
    )
    return Runner(agent=agent, app_name="agents", session_service=session_service)


def _guardrail(span, value):
    span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
    span.set_attribute(SpanAttributes.INPUT_VALUE, value[:500])


async def _judge(text: str) -> tuple[bool, str]:
    """Return (cleared, verdict) from the Security Judge."""
    with tracer.start_as_current_span("security.a2a_judge") as span:
        _guardrail(span, text)
        verdict = await call_a2a_agent(query=text, host=A2A_JUDGE_HOST, port=A2A_JUDGE_PORT) or ""
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, verdict[:200])
        return "BLOCKED" not in verdict.upper(), verdict


async def _guardrail_check(text: str, user_id: str) -> tuple[bool, str]:
    """Same topical/safety check the CLI runs; fails open like the CLI."""
    with tracer.start_as_current_span("guardrail.check") as span:
        _guardrail(span, text)
        session = await session_service.create_session(app_name="guardrail", user_id=user_id)
        content = types.Content(role="user", parts=[types.Part(text=text)])
        final, reasoning = "", ""
        try:
            async for event in guardrail_runner.run_async(
                    user_id=user_id, session_id=session.id, new_message=content):
                if event.is_final_response() and event.content and event.content.parts:
                    final = event.content.parts[0].text or ""
            body = final.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()
            decision = json.loads(body)
            passed = str(decision.get("decision", "safe")).lower() == "safe"
            reasoning = str(decision.get("reasoning", ""))
        except Exception:
            passed, reasoning = True, "could not parse the guardrail's answer, so it failed open (allowed)"
        await session_service.delete_session(app_name="guardrail", user_id=user_id, session_id=session.id)
        span.set_attribute("guardrail.passed", passed)
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, final[:300] or ("safe" if passed else "unsafe"))
        return passed, reasoning


async def _recall(text: str, user_id: str) -> list[dict]:
    with tracer.start_as_current_span("memory.recall") as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "RETRIEVER")
        span.set_attribute(SpanAttributes.INPUT_VALUE, text)
        try:
            res = await asyncio.to_thread(mem0.search, text, filters={"user_id": user_id})
        except Exception as exc:
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"error: {exc}")
            return []
        found = []
        for m in (res.get("results") or [])[:MEMORY_TOP_K]:
            text_, score = m["memory"], round(float(m.get("score") or 0), 2)
            if len(text_) > MEMORY_MAX_CHARS:
                found.append({"memory": f"{text_[:160]}… [{len(text_):,} chars, rejected as corrupted]",
                              "score": score, "rejected": True})
            else:
                found.append({"memory": text_, "score": score})
        hits = [m for m in found if m["score"] >= MEMORY_MIN_SCORE and not m.get("rejected")]
        span.set_attribute("memory.candidates", len(found))
        span.set_attribute("memory.min_score", MEMORY_MIN_SCORE)
        for i, h in enumerate(hits):
            span.set_attribute(f"retrieval.documents.{i}.document.content", h["memory"])
            span.set_attribute(f"retrieval.documents.{i}.document.score", h["score"])
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(hits))
        return hits, found


async def _remember(user_id: str, user_msg: str) -> str:
    with tracer.start_as_current_span("memory.save") as span:
        span.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "TOOL")
        span.set_attribute(SpanAttributes.INPUT_VALUE, user_msg)
        try:
            # User turns only: saving the agent's replies lets its own mistakes become "facts".
            res = await asyncio.to_thread(mem0.add, [{"role": "user", "content": user_msg}], user_id=user_id)
        except Exception as exc:
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"error: {exc}")
            return f"save failed: {exc}"
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, json.dumps(res, default=str)[:300])
        status = res.get("status", "ok") if isinstance(res, dict) else "ok"
        return (f"sent the user's message to Mem0 (status {status}); Mem0 extracts facts in the background, "
                f"so they show up in recall after a minute or two")


async def _mask(text: str) -> tuple[str, str]:
    with tracer.start_as_current_span("security.a2a_mask") as span:
        _guardrail(span, text)
        try:
            masked = await call_a2a_agent(query=text, host=A2A_MASK_HOST, port=A2A_MASK_PORT)
        except Exception as exc:
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"mask_skipped: {exc}")
            return text, f"Masker unreachable, response sent unmasked ({exc})"
        out = masked or text
        span.set_attribute(SpanAttributes.OUTPUT_VALUE, out[:500])
        note = "no PII found, response unchanged" if out.strip() == text.strip() else "PII masked in the response"
        return out, note


@app.post("/api/login")
async def login(req: LoginReq):
    ctx = authenticate_user(email=req.email, password=req.password)
    if not ctx:
        return JSONResponse({"ok": False, "error": "Invalid email or password."}, status_code=401)
    uid = ctx["email"]
    _runners[uid] = _build_runner(uid)
    sid = f"session_{uid}"
    # Make login idempotent — a repeat login (or page reload) must not 500 on a
    # session id that already exists. Recreate it fresh.
    try:
        await session_service.delete_session(app_name="agents", user_id=uid, session_id=sid)
    except Exception:
        pass
    await session_service.create_session(app_name="agents", user_id=uid, session_id=sid)
    return {
        "ok": True,
        "user_id": uid,
        "full_name": ctx.get("full_name"),
        "is_premium": bool(ctx.get("is_premium_customer")),
        "items": ctx.get("total_items_purchased", 0),
    }


@app.post("/api/logout")
async def logout(req: LogoutReq):
    _runners.pop(req.user_id, None)
    try:
        await session_service.delete_session(
            app_name="agents", user_id=req.user_id, session_id=f"session_{req.user_id}")
    except Exception:
        pass
    return {"ok": True}


def _decode(value):
    if isinstance(value, str) and value.lstrip()[:1] in ("{", "["):
        try:
            return json.loads(value)
        except ValueError:
            pass
    return value


def _unwrap(resp):
    if isinstance(resp, dict) and set(resp) == {"result"}:
        resp = resp["result"]
    if isinstance(resp, str):
        try:
            return json.loads(resp)
        except ValueError:
            return resp
    return resp


@app.post("/api/chat")
async def chat(req: ChatReq):
    runner = _runners.get(req.user_id)
    if runner is None:
        return JSONResponse({"ok": False, "error": "Not logged in."}, status_code=401)
    return StreamingResponse(_chat_events(runner, req), media_type="application/x-ndjson")


def _ev(**kw):
    return json.dumps(kw, default=str) + "\n"


async def _chat_events(runner, req):
    with tracer.start_as_current_span("agent.turn") as turn:
        turn.set_attribute(SpanAttributes.OPENINFERENCE_SPAN_KIND, "CHAIN")
        turn.set_attribute(SpanAttributes.INPUT_VALUE, req.message)
        turn.set_attribute("user.id", req.user_id)
        trace_id = format(turn.get_span_context().trace_id, "032x")
        yield _ev(type="trace", trace_id=trace_id, url=_trace_url(trace_id), span="agent.turn")
        async for line in _turn(runner, req, turn):
            yield line


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


async def _turn(runner, req, turn):
    def blocked(stage, msg):
        turn.set_attribute("turn.blocked", True)
        turn.set_attribute(SpanAttributes.OUTPUT_VALUE, f"BLOCKED: {stage}")
        return _ev(type="final", blocked=True, stage=stage, response=msg)

    def step(key, title, ok, detail, span, t0, **extra):
        return _ev(type="step", key=key, title=title, status="passed" if ok else "blocked",
                   detail=detail, span=span, ms=_ms(t0), **extra)

    # Layer 1 — local sanitization
    yield _ev(type="stage", key="sanitize", stage="Sanitizing input")
    t0 = time.perf_counter()
    with tracer.start_as_current_span("security.sanitize") as span:
        _guardrail(span, req.message)
        try:
            clean = sanitize_input(req.message)
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, "passed")
            reason = "length and character checks passed, no blocked patterns"
        except ValueError as exc:
            reason = str(exc)
            span.set_attribute(SpanAttributes.OUTPUT_VALUE, f"blocked: {reason}")
            clean = None
    yield step("sanitize", "Sanitizer", clean is not None, reason, "security.sanitize", t0,
               kind="in-process", runs="regex blocklist in cs_agent/security/sanitizer.py")
    if clean is None:
        yield blocked("sanitizer", f"Input rejected by sanitizer: {reason}")
        return

    # Layer 2 — A2A Security Judge
    yield _ev(type="stage", key="judge", stage="A2A Security Judge")
    t0 = time.perf_counter()
    try:
        ok, verdict = await _judge(clean)
    except Exception as exc:
        yield _ev(type="error", error=f"Security Judge unreachable: {exc}")
        return
    judged = ("cleared: echoed the input back unmodified, its signal for safe (regex evaluator tool + Gemini found no injection)"
              if ok else f"returned BLOCKED: {verdict.strip()[:200]}")
    yield step("judge", "Security Judge", ok, judged, "security.a2a_judge", t0,
               kind="A2A", runs=f"ADK agent behind an A2A server at :{A2A_JUDGE_PORT}")
    if not ok:
        yield blocked("judge", "Blocked by the A2A Security Judge (possible injection/unsafe input).")
        return

    # Layer 3 — topical/safety guardrail (ADK agent, in-process)
    yield _ev(type="stage", key="guardrail", stage="Guardrail check")
    t0 = time.perf_counter()
    ok, reasoning = await _guardrail_check(clean, req.user_id)
    yield step("guardrail", "Guardrail", ok, reasoning or ("safe" if ok else "unsafe"), "guardrail.check", t0,
               kind="in-process", runs="ADK guardrail_agent (gemini-2.5-flash) with GUARDRAIL_PROMPT_INSTRUCTION")
    if not ok:
        yield blocked("guardrail", "I'm not able to help with that request. "
                                   "Please ask a safe, customer-support-related question instead.")
        return

    # Memory — recall from Mem0 and insert into the agent's context
    yield _ev(type="stage", key="recall", stage="Recalling memories from Mem0")
    t0 = time.perf_counter()
    memories, found = await _recall(clean, req.user_id)
    skipped = [m for m in found if m not in memories]
    if memories:
        recalled = (f"Mem0 returned its top {len(found)} matches; {len(memories)} cleared the {MEMORY_MIN_SCORE} "
                    f"relevance cutoff and were inserted into the agent's context"
                    + (f", {len(skipped)} skipped (below the cutoff or too long)" if skipped else ""))
    elif found:
        recalled = f"Mem0 returned {len(found)} matches, none cleared the {MEMORY_MIN_SCORE} relevance cutoff; nothing inserted"
    else:
        recalled = "no memories yet for this user; nothing inserted"
    yield step("recall", "Mem0 recall", True, recalled, "memory.recall", t0,
               kind="Python fn", runs=f"mem0.search() on the Mem0 cloud API, top {MEMORY_TOP_K}, min score {MEMORY_MIN_SCORE}",
               memories=memories, skipped=skipped)
    agent_input = clean
    if memories:
        agent_input = ("Relevant memories about this customer (from Mem0):\n"
                       + "\n".join(f"- {m['memory']}" for m in memories)
                       + f"\n\nCustomer message: {clean}")

    # Agent turn (+ MCP tools)
    yield _ev(type="stage", key="agent", stage="Agent thinking")
    content = types.Content(role="user", parts=[types.Part(text=agent_input)])
    final_text, n, t0 = "", 0, time.perf_counter()
    pending: dict[str, list[tuple[int, float]]] = {}
    async for event in runner.run_async(user_id=req.user_id, session_id=f"session_{req.user_id}",
                                        new_message=content):
        calls = event.get_function_calls() or []
        if event.author != "user" and event.content and (calls or event.is_final_response()):
            u = event.usage_metadata
            decided = (f"decided to call {', '.join(c.name for c in calls)}" if calls
                       else "wrote the final answer")
            yield _ev(type="llm", title="Gemini", detail=decided, span="call_llm",
                      model="gemini-2.5-flash", ms=_ms(t0),
                      tokens_in=getattr(u, "prompt_token_count", None),
                      tokens_out=getattr(u, "candidates_token_count", None))
        for fc in calls:
            n += 1
            pending.setdefault(fc.name, []).append((n, time.perf_counter()))
            yield _ev(type="tool_call", id=n, name=fc.name, span=f"execute_tool {fc.name}",
                      info=TOOLS.get(fc.name, {"kind": "tool"}),
                      args={k: _decode(v) for k, v in (fc.args or {}).items()})
        for fr in (event.get_function_responses() or []):
            tid, started = (pending.get(fr.name) or [(None, time.perf_counter())]).pop(0)
            yield _ev(type="tool_result", id=tid, name=fr.name, ms=_ms(started), result=_unwrap(fr.response))
            yield _ev(type="stage", key="agent", stage="Agent thinking")
            t0 = time.perf_counter()
        if event.is_final_response() and event.content and event.content.parts:
            final_text = event.content.parts[0].text or ""

    # Layer 4 — A2A Data Masker on the way out
    yield _ev(type="stage", key="mask", stage="A2A Data Masker")
    t0 = time.perf_counter()
    masked, note = await _mask(final_text)
    yield step("mask", "Data Masker", True, note, "security.a2a_mask", t0,
               kind="A2A", runs=f"ADK agent behind an A2A server at :{A2A_MASK_PORT}")
    yield _ev(type="stage", key="save", stage="Saving to Mem0")
    t0 = time.perf_counter()
    note = await _remember(req.user_id, clean)
    yield step("save", "Mem0 save", not note.startswith("save failed"), note, "memory.save", t0,
               kind="Python fn", runs="mem0.add() on the Mem0 cloud API, user message only")
    turn.set_attribute(SpanAttributes.OUTPUT_VALUE, masked)
    yield _ev(type="final", blocked=False, response=masked)


@app.get("/architecture")
def architecture_page():
    return FileResponse(os.path.join(_this_dir, "static", "architecture.html"), media_type="text/html")


@app.get("/architecture.svg")
def architecture():
    return FileResponse(os.path.join(_this_dir, "static", "architecture.svg"), media_type="image/svg+xml")


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX_HTML)


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Customer Support Agent</title>
<style>
  :root{
    --bg:#f7f8fa; --panel:#ffffff; --panel-2:#f1f3f6; --line:#e4e7ec;
    --text:#1a1d23; --muted:#6b7280; --accent:#0f9aae; --accent-2:#0c8294;
    --user:#eef1f6; --tool:#f4f6f9;
  }
  *{box-sizing:border-box}
  html,body{height:100%}
  body{margin:0;font:15px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
       background:var(--bg);color:var(--text);height:100vh;display:flex;flex-direction:column;overflow:hidden}
  header{padding:14px 20px;border-bottom:1px solid var(--line);display:flex;align-items:center;gap:10px}
  header .dot{width:9px;height:9px;border-radius:50%;background:var(--accent);box-shadow:0 0 10px var(--accent)}
  header h1{font-size:15px;font-weight:600;margin:0;letter-spacing:.2px}
  header .who{margin-left:auto;color:var(--muted);font-size:13px}
  header .logout{margin-left:14px;background:transparent;color:var(--muted);border:1px solid var(--line);
       border-radius:9px;padding:5px 12px;font-size:13px;font-weight:500;cursor:pointer}
  header .logout:hover{color:var(--text);border-color:var(--muted)}
  main{flex:1;min-height:0;overflow-y:auto;-webkit-overflow-scrolling:touch}
  .col{width:100%;max-width:760px;margin:0 auto;padding:24px 20px 150px}
  .msg{margin:0 0 22px}
  .msg .role{font-size:12px;text-transform:uppercase;letter-spacing:.8px;color:var(--muted);margin-bottom:6px}
  .bubble{padding:14px 16px;border-radius:14px;border:1px solid var(--line)}
  .user .bubble{background:var(--user)}
  .assistant .bubble{background:var(--panel)}
  .assistant .bubble :first-child{margin-top:0}
  .assistant .bubble :last-child{margin-bottom:0}
  .bubble h1,.bubble h2,.bubble h3{font-size:1.05em;margin:.6em 0 .3em}
  .bubble ul,.bubble ol{margin:.3em 0;padding-left:1.3em}
  .bubble code{background:#eef1f6;padding:2px 6px;border-radius:6px;font-size:.9em}
  .bubble pre{background:#eef1f6;padding:12px;border-radius:10px;overflow:auto}
  .steps{margin:10px 0 0;border:1px solid var(--line);border-radius:12px;background:var(--tool);overflow:hidden}
  .steps summary{cursor:pointer;padding:9px 13px;color:var(--muted);font-size:13px;user-select:none;list-style:none}
  .steps summary::-webkit-details-marker{display:none}
  .steps summary .pill{display:inline-block;background:var(--panel-2);border:1px solid var(--line);
       border-radius:999px;padding:1px 9px;margin-left:6px;font-size:12px;color:var(--accent)}
  .step{padding:10px 14px;border-top:1px solid var(--line);font-size:13px}
  .step .call{color:var(--accent)}
  .step .res{color:var(--muted);white-space:pre-wrap;word-break:break-word;margin-top:4px;
       font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
  .step .res.text{font-family:inherit}
  header .who+.logout{margin-left:14px}
  header a.logout{text-decoration:none;display:inline-block}
  .step .call{display:flex;align-items:center;gap:8px}
  .step .state{margin-left:auto;font-size:11px;color:var(--muted)}
  .step .call b{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-weight:600;color:var(--text)}
  .steps summary{display:flex;align-items:center;gap:6px}
  .steps .trace-link{margin-left:auto;color:var(--accent);text-decoration:none;font-weight:600}
  .steps .trace-link:hover{text-decoration:underline}
  .step.bad{background:#fdf3f2}
  .ic{width:14px;text-align:center;font-weight:700;flex:none}
  .ic.ok{color:#1f7a3a}.ic.no{color:#a23b30}
  .kb{display:inline-block;font-size:10px;font-weight:700;letter-spacing:.4px;padding:1px 7px;border-radius:5px;flex:none}
  .kb-mcp{background:#e0f0ff;color:#1f5f99}.kb-py{background:#efe9fb;color:#5b3d99}
  .kb-a2a{background:#e3f6f8;color:#0c6f7e}.kb-local{background:#eef1f6;color:#4b5563}
  .kb-llm{background:#fff4d6;color:#8a6100}
  .kb-read{background:#e3f6e8;color:#1f7a3a}.kb-write{background:#fde8e6;color:#a23b30}
  .what{margin:5px 0 0 22px;color:var(--text)}
  .sub{margin:4px 0 0 22px;font-size:11.5px;color:var(--muted);display:flex;flex-wrap:wrap;gap:4px 10px}
  .sub .meta{margin-left:auto}
  .sub code{font-size:11px;background:var(--panel-2);padding:0 5px;border-radius:4px}
  .path{margin:5px 0 0 22px;font-size:12px;color:var(--muted)}
  .path .arr{color:var(--accent)}
  .step .args{margin-left:22px}
  .sql{margin:6px 0 0 22px;font-size:12px}
  .sql summary{cursor:pointer;color:var(--muted);list-style:none}
  .sql summary::-webkit-details-marker{display:none}
  .sql .legend{margin-left:8px;font-size:11px;opacity:.8}
  .sql pre{margin:6px 0 0;padding:10px;background:var(--panel);border:1px solid var(--line);border-radius:8px;
       font:11.5px/1.5 ui-monospace,SFMono-Regular,Menlo,monospace;white-space:pre-wrap}
  .sql mark{background:#fff4d6;color:#8a6100;border-radius:3px;padding:0 2px}
  .step > div:has(.rtable){margin-left:22px}
  .mems{margin:6px 0 0 22px;padding:0;list-style:none;font-size:12.5px}
  .skipped{margin:6px 0 0 22px;font-size:12px;color:var(--muted)}
  .skipped summary{cursor:pointer;list-style:none}
  .skipped summary::-webkit-details-marker{display:none}
  .skipped .mems{margin-left:0;opacity:.6}
  .mems li{display:flex;gap:8px;padding:4px 8px;background:var(--panel);border:1px solid var(--line);border-radius:7px;margin-top:4px}
  .mems .score{flex:none;font:600 11px ui-monospace,SFMono-Regular,Menlo,monospace;color:#5b3d99;background:#efe9fb;border-radius:4px;padding:1px 5px;height:fit-content}
  .args{display:grid;grid-template-columns:max-content 1fr;gap:3px 14px;margin:6px 0 0 19px;font-size:12.5px}
  .args .k{color:var(--muted)}
  .args .v{color:var(--text);word-break:break-word}
  .args.nested{margin:0;padding-left:10px;border-left:2px solid var(--line)}
  .spin{width:11px;height:11px;border:2px solid var(--line);border-top-color:var(--accent);border-radius:50%;
       animation:spin .7s linear infinite;flex:none}
  @keyframes spin{to{transform:rotate(360deg)}}
  .typing .spin{display:inline-block;vertical-align:-1px;margin-right:6px}
  .rtable{width:100%;border-collapse:collapse;margin-top:8px;font-size:12.5px;background:var(--panel);
       border:1px solid var(--line);border-radius:8px;overflow:hidden}
  .rtable th{text-align:left;font-weight:600;color:var(--muted);font-size:11px;text-transform:uppercase;
       letter-spacing:.5px;padding:6px 10px;background:var(--panel-2);border-bottom:1px solid var(--line)}
  .rtable td{padding:6px 10px;border-bottom:1px solid var(--line);vertical-align:top}
  .rtable tr:last-child td{border-bottom:0}
  .rtable td.num{text-align:right;font-variant-numeric:tabular-nums}
  .badge{display:inline-block;padding:1px 8px;border-radius:999px;font-size:11px;font-weight:600;letter-spacing:.3px}
  .b-PROCESSING{background:#fff4d6;color:#8a6100}.b-SHIPPED{background:#e0f0ff;color:#1f5f99}
  .b-DELIVERED{background:#e3f6e8;color:#1f7a3a}.b-CANCELLED{background:#fde8e6;color:#a23b30}
  .b-RETURNED{background:#efe9fb;color:#5b3d99}
  .raw{margin-top:6px;font-size:11.5px;color:var(--muted)}
  .raw summary{cursor:pointer;list-style:none}
  .raw pre{margin:6px 0 0;padding:10px;background:var(--panel);border:1px solid var(--line);border-radius:8px;
       max-height:260px;overflow:auto;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .blocked .bubble{border-color:#e0a59f;background:#fdecea;color:#a23b30}
  footer{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(transparent,var(--bg) 22%);padding:18px 20px 22px}
  .inwrap{max-width:760px;margin:0 auto;display:flex;gap:10px;align-items:flex-end;
       background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:8px 8px 8px 14px}
  textarea{flex:1;resize:none;border:0;outline:0;background:transparent;color:var(--text);font:inherit;max-height:140px;padding:6px 0}
  button{background:var(--accent);color:#ffffff;border:0;border-radius:11px;padding:10px 16px;font-weight:700;cursor:pointer}
  button:disabled{opacity:.5;cursor:default}
  .hint{max-width:760px;margin:8px auto 0;color:var(--muted);font-size:12px;text-align:center}
  .chips{display:flex;flex-wrap:wrap;gap:8px;margin:14px 0 0}
  .chips .label{flex-basis:100%;color:var(--muted);font-size:12px;text-transform:uppercase;letter-spacing:.6px;margin-bottom:2px}
  .chip{background:var(--panel);border:1px solid var(--line);border-radius:999px;padding:8px 14px;
       font-size:13px;color:var(--text);cursor:pointer;transition:border-color .15s,color .15s}
  .chip:hover{border-color:var(--accent);color:var(--accent)}
  /* login */
  .login{margin:auto;max-width:380px;width:100%;background:var(--panel);border:1px solid var(--line);
       border-radius:16px;padding:26px}
  .login h2{margin:0 0 4px;font-size:18px}
  .login p{margin:0 0 18px;color:var(--muted);font-size:13px}
  .login input{width:100%;padding:11px 13px;margin:6px 0;background:var(--panel-2);border:1px solid var(--line);
       border-radius:10px;color:var(--text);font:inherit;outline:0}
  .login button{width:100%;margin-top:10px;padding:12px}
  .err{color:#ff9a90;font-size:13px;margin-top:8px;min-height:18px}
  .seed{margin-top:14px;color:var(--muted);font-size:12px;line-height:1.7}
  .seed code{background:var(--panel-2);padding:1px 6px;border-radius:5px}
  .typing{color:var(--muted);font-size:13px}
</style>
</head>
<body>
<header>
  <span class="dot"></span>
  <h1>Customer Support Agent</h1>
  <span class="who" id="who"></span>
  <a id="archLink" class="logout" href="/architecture" target="arch">Architecture ↗</a>
  <button id="logout" class="logout" style="display:none">Sign out</button>
</header>


<main>
  <div class="col" id="col">
    <div class="login" id="login">
      <h2>Sign in</h2>
      <p>Use a seeded demo account. Password is the first name, lowercase.</p>
      <input id="email" placeholder="email" value="alice.jones@example.com" autocomplete="off"/>
      <input id="password" placeholder="password" type="password" value="alice"/>
      <button id="loginBtn">Sign in</button>
      <div class="err" id="loginErr"></div>
      <div class="seed">Try: <code>alice.jones@example.com</code> / <code>alice</code> ·
        <code>bob.smith@techmail.com</code> / <code>bob</code> ·
        <code>julia.child@kitchen.com</code> / <code>julia</code></div>
    </div>
  </div>
</main>

<footer id="footer" style="display:none">
  <div class="inwrap">
    <textarea id="input" rows="1" placeholder="Ask about your orders…"></textarea>
    <button id="send">Send</button>
  </div>
  <div class="hint">Pipeline: sanitize → A2A Security Judge → guardrail → Mem0 recall → agent + MCP tools → A2A Data Masker → Mem0 save</div>
</footer>

<script>
// Tiny self-contained markdown renderer (no external CDN — works offline/behind CSP).
function md(src){
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const inline=s=>esc(s)
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*]+)\*/g,'$1<em>$2</em>');
  const lines=(src||'').split(/\r?\n/);
  let html='',list=null;
  const closeList=()=>{if(list){html+=`</${list}>`;list=null;}};
  for(let raw of lines){
    const line=raw.trimEnd();
    let m;
    if(!line.trim()){closeList();continue;}
    if(m=line.match(/^(#{1,3})\s+(.*)$/)){closeList();const n=m[1].length;html+=`<h${n}>${inline(m[2])}</h${n}>`;continue;}
    if(m=line.match(/^\s*[-*]\s+(.*)$/)){if(list!=='ul'){closeList();list='ul';html+='<ul>';}html+=`<li>${inline(m[1])}</li>`;continue;}
    if(m=line.match(/^\s*\d+\.\s+(.*)$/)){if(list!=='ol'){closeList();list='ol';html+='<ol>';}html+=`<li>${inline(m[1])}</li>`;continue;}
    closeList();html+=`<p>${inline(line)}</p>`;
  }
  closeList();
  return html;
}
let USER=null;
const col=document.getElementById('col');
const footer=document.getElementById('footer');
const who=document.getElementById('who');

function el(html){const t=document.createElement('template');t.innerHTML=html.trim();return t.content.firstChild;}
function scroll(){const m=document.querySelector('main');requestAnimationFrame(()=>{m.scrollTop=m.scrollHeight;});}

function addUser(text){
  col.appendChild(el(`<div class="msg user"><div class="role">You</div><div class="bubble"></div></div>`));
  col.lastChild.querySelector('.bubble').textContent=text; scroll();
}
function addAssistant(){
  const node=el(`<div class="msg assistant"><div class="role">Agent</div><div class="steps-host"></div><div class="bubble"><span class="typing">thinking…</span></div></div>`);
  col.appendChild(node); scroll(); return node;
}
function esc(v){return String(v).replace(/[&<>"]/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[m]));}
function label(k){return k.replace(/_/g,' ');}
function cell(k,v){
  if(v==null) return '<td>–</td>';
  if(k==='status') return `<td><span class="badge b-${esc(v)}">${esc(v)}</span></td>`;
  if(/amount|price|total/.test(k)&&!isNaN(v)) return `<td class="num">$${Number(v).toFixed(2)}</td>`;
  if(/date|timestamp/.test(k)&&!isNaN(Date.parse(v))) return `<td>${new Date(v).toLocaleDateString(undefined,{month:'short',day:'numeric',year:'numeric'})}</td>`;
  if(Array.isArray(v)) return `<td>${v.map(i=>i&&i.product?`${i.qty||1}× ${esc(i.product)}`:esc(JSON.stringify(i))).join('<br>')}</td>`;
  if(typeof v==='object') return `<td>${esc(JSON.stringify(v))}</td>`;
  return `<td${typeof v==='number'?' class="num"':''}>${esc(v)}</td>`;
}
function table(rows){
  const keys=[...new Set(rows.flatMap(r=>Object.keys(r)))];
  return `<table class="rtable"><thead><tr>${keys.map(k=>`<th>${esc(label(k))}</th>`).join('')}</tr></thead><tbody>${
    rows.map(r=>`<tr>${keys.map(k=>cell(k,r[k])).join('')}</tr>`).join('')}</tbody></table>`;
}
function renderResult(res){
  const wrap=document.createElement('div');
  let html;
  if(Array.isArray(res)&&res.length&&res.every(r=>r&&typeof r==='object')) html=table(res);
  else if(res&&typeof res==='object'&&!Array.isArray(res)) html=table([res]);
  else if(Array.isArray(res)&&!res.length) html='<div class="res text">No results</div>';
  else html=`<div class="res text">${esc(res)}</div>`;
  wrap.innerHTML=html+(typeof res==='object'?`<details class="raw"><summary>Raw JSON</summary><pre>${esc(JSON.stringify(res,null,2))}</pre></details>`:'');
  return wrap;
}
function stepsPanel(node){
  let d=node.querySelector('.steps');
  if(!d){
    d=el(`<details class="steps" open><summary><span>What happened</span><span class="pill">0</span><a class="trace-link" target="phoenix" style="display:none">View trace in Phoenix ↗</a></summary></details>`);
    d.querySelector('.trace-link').addEventListener('click',e=>e.stopPropagation());
    node.querySelector('.steps-host').appendChild(d);
  }
  return d;
}
function setTrace(node,t){
  const a=stepsPanel(node).querySelector('.trace-link');
  a.href=t.url; a.style.display='inline'; a.title=`trace ${t.trace_id}`;
}
function argVal(v){
  if(v==null) return '–';
  if(Array.isArray(v)) return v.map(i=>i&&i.product?`${i.qty||1}× ${esc(i.product)}`:esc(typeof i==='object'?JSON.stringify(i):i)).join(', ');
  if(typeof v==='object') return `<div class="args nested">${argRows(v)}</div>`;
  return esc(v);
}
function argRows(o){return Object.entries(o).map(([k,v])=>`<div class="k">${esc(label(k))}</div><div class="v">${argVal(v)}</div>`).join('');}
const KIND_CLASS={'MCP':'mcp','Python fn':'py','A2A':'a2a','in-process':'local','LLM':'llm'};
function badge(t){return `<span class="kb kb-${KIND_CLASS[t]||'local'}">${esc(t)}</span>`;}
function meta(span,ms,extra){
  return `<span class="meta">${extra?esc(extra)+' · ':''}${ms!=null?ms.toLocaleString()+' ms · ':''}span <code>${esc(span)}</code></span>`;
}
function addRow(node,html,key){
  const d=stepsPanel(node);
  const row=el(`<div class="step"${key?` data-key="${key}"`:''}>${html}</div>`);
  d.appendChild(row);
  d.querySelector('.pill').textContent=d.querySelectorAll('.step').length;
  scroll(); return row;
}
const STAGE_ROWS={sanitize:['Sanitizer','in-process'],judge:['Security Judge','A2A'],guardrail:['Guardrail','in-process'],
  recall:['Mem0 recall','Python fn'],mask:['Data Masker','A2A'],save:['Mem0 save','Python fn']};
function stageStart(node,e){
  const r=STAGE_ROWS[e.key]; if(!r) return;
  addRow(node,`<div class="call"><span class="spin"></span>${badge(r[1])}<b>${r[0]}</b><span class="state">running…</span></div>`,e.key);
}
function stageDone(node,e){
  const row=[...node.querySelectorAll(`.step[data-key="${e.key}"]`)].pop()||addRow(node,'',e.key);
  const ok=e.status==='passed';
  row.classList.toggle('bad',!ok);
  row.innerHTML=`<div class="call"><span class="ic ${ok?'ok':'no'}">${ok?'✓':'✕'}</span>${badge(e.kind)}<b>${esc(e.title)}</b><span class="state">${ok?'passed':'blocked'}</span></div>
    <div class="what">${esc(e.detail)}</div>
    ${e.memories&&e.memories.length?`<ul class="mems">${e.memories.map(m=>`<li><span class="score">${m.score.toFixed(2)}</span>${esc(m.memory)}</li>`).join('')}</ul>`:''}
    ${e.skipped&&e.skipped.length?`<details class="skipped"><summary>${e.skipped.length} not inserted (below cutoff or too long)</summary><ul class="mems">${e.skipped.map(m=>`<li><span class="score">${m.score.toFixed(2)}</span>${esc(m.memory)}</li>`).join('')}</ul></details>`:''}
    <div class="sub">${esc(e.runs||'')}${meta(e.span,e.ms)}</div>`;
}
function addLLM(node,e){
  const tok=e.tokens_in!=null?`${e.tokens_in.toLocaleString()} in / ${(e.tokens_out||0).toLocaleString()} out tokens`:'';
  addRow(node,`<div class="call"><span class="ic ok">✓</span>${badge('LLM')}<b>${esc(e.model)}</b><span class="state">done</span></div>
    <div class="what">${esc(e.detail)}</div>
    <div class="sub">Support Agent model call${meta(e.span,e.ms,tok)}</div>`);
}
function sqlWithArgs(info,args){
  const params=info.params||[];
  let sql=esc(info.statement).replace(/\$(\d+)/g,(m,i)=>{const n=params[i-1];const v=args[n];
    return `<mark title="${esc(n)}">${esc(typeof v==='object'?JSON.stringify(v):JSON.stringify(v))}</mark>`;});
  const legend=params.map((n,i)=>`$${i+1} = ${esc(n)}`).join(' · ');
  return `<details class="sql"><summary>SQL the Toolbox ran <span class="legend">${legend}</span></summary><pre>${sql}</pre></details>`;
}
function addToolCall(node,c){
  const info=c.info||{};
  const has=Object.keys(c.args||{}).length;
  const path=(info.path||[]).map(esc).join(' <span class="arr">→</span> ');
  const access=info.access?`<span class="kb kb-${info.access==='WRITE'?'write':'read'}">${info.access}</span>`:'';
  const row=addRow(node,`<div class="call"><span class="spin"></span>${badge(info.kind||'tool')}${access}<b>${esc(c.name)}</b><span class="state">running…</span></div>
    ${path?`<div class="path">${path}</div>`:''}
    ${has?`<div class="args">${argRows(c.args)}</div>`:''}
    ${info.statement?sqlWithArgs(info,c.args||{}):''}
    <div class="sub">${esc(info.runs||'')}${meta(c.span,null)}</div>`);
  row.dataset.id=c.id;
}
function addToolResult(node,r){
  const step=node.querySelector(`.step[data-id="${r.id}"]`)||[...node.querySelectorAll('.step[data-id]')].reverse().find(s=>!s.dataset.done);
  if(!step) return;
  step.dataset.done=1;
  const sp=step.querySelector('.spin'); if(sp) sp.outerHTML='<span class="ic ok">✓</span>';
  step.querySelector('.state').textContent=`${(r.ms||0).toLocaleString()} ms`;
  const n=Array.isArray(r.result)?`returned ${r.result.length} row${r.result.length===1?'':'s'}`:r.result&&typeof r.result==='object'?'returned 1 row':'returned a result';
  step.appendChild(el(`<div class="what">${n}</div>`));
  if(r.result!=null) step.appendChild(renderResult(r.result));
  scroll();
}

const archBus=new BroadcastChannel('cs-agent');
const archEvent=e=>archBus.postMessage(e);

async function login(){
  const email=document.getElementById('email').value.trim();
  const password=document.getElementById('password').value;
  const err=document.getElementById('loginErr'); err.textContent='';
  const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},
    body:JSON.stringify({email,password})});
  const d=await r.json();
  if(!d.ok){err.textContent=d.error||'Login failed';return;}
  USER=d.user_id;
  who.textContent=`${d.full_name}${d.is_premium?' · premium':''}`;
  document.getElementById('login').remove();
  document.getElementById('logout').style.display='inline-block';
  footer.style.display='block';
  col.appendChild(el(`<div class="msg assistant"><div class="role">Agent</div><div class="bubble">Hi ${d.full_name}! Ask me about your orders — status, history, cancellations, or address changes.</div></div>`));
  renderChips();
  document.getElementById('input').focus();
}

const SAMPLES=[
  "Where is my last order?",
  "Show me all my orders",
  "Cancel my processing order",
  "I want to return order 1",
  "'; DROP TABLE users; --"
];
function renderChips(){
  const wrap=el(`<div class="chips" id="chips"><div class="label">Try asking</div></div>`);
  SAMPLES.forEach(q=>{
    const c=el(`<button class="chip"></button>`); c.textContent=q;
    c.onclick=()=>{ const i=document.getElementById('input'); i.value=q; send(); };
    wrap.appendChild(c);
  });
  col.appendChild(wrap); scroll();
}

async function send(){
  const input=document.getElementById('input');
  const text=input.value.trim(); if(!text||!USER) return;
  const chips=document.getElementById('chips'); if(chips) chips.remove();
  input.value=''; input.style.height='auto';
  document.getElementById('send').disabled=true;
  addUser(text);
  const node=addAssistant();
  const bubble=node.querySelector('.bubble');
  const status=t=>{bubble.innerHTML=`<span class="typing"><span class="spin"></span>${esc(t)}…</span>`;};
  status('Sending');
  try{
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user_id:USER,message:text})});
    if(!r.ok){const d=await r.json().catch(()=>({}));bubble.textContent=d.error||'Error';}
    else{
      const reader=r.body.getReader(), dec=new TextDecoder(); let buf='';
      archEvent({type:'start',message:text});
      const handle=e=>{
        archEvent(e);
        if(e.type==='stage'){ status(e.stage); stageStart(node,e); }
        else if(e.type==='trace') setTrace(node,e);
        else if(e.type==='step') stageDone(node,e);
        else if(e.type==='llm') addLLM(node,e);
        else if(e.type==='tool_call') addToolCall(node,e);
        else if(e.type==='tool_result') addToolResult(node,e);
        else if(e.type==='error') bubble.textContent=e.error;
        else if(e.type==='final'){ if(e.blocked) node.classList.add('blocked'); bubble.innerHTML=md(e.response||''); }
      };
      for(;;){
        const {value,done}=await reader.read(); if(done) break;
        buf+=dec.decode(value,{stream:true});
        let i; while((i=buf.indexOf('\n'))>=0){const line=buf.slice(0,i).trim(); buf=buf.slice(i+1); if(line) handle(JSON.parse(line));}
      }
      if(buf.trim()) handle(JSON.parse(buf));
    }
  }catch(e){bubble.textContent='Network error: '+e;}
  document.getElementById('send').disabled=false; scroll();
  input.focus();
}

async function logout(){
  try{ if(USER) await fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:USER})}); }
  catch(e){}
  location.reload();
}
document.getElementById('logout').onclick=logout;
document.getElementById('loginBtn').onclick=login;
document.getElementById('password').addEventListener('keydown',e=>{if(e.key==='Enter')login();});
document.getElementById('send').onclick=send;
const inp=document.getElementById('input');
inp.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
inp.addEventListener('input',()=>{inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,140)+'px';});
</script>
</body>
</html>"""


def main():
    import uvicorn
    host = os.getenv("WEB_HOST", "127.0.0.1")
    port = int(os.getenv("WEB_PORT", "8000"))
    print(f"Customer Support web UI → http://{host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
