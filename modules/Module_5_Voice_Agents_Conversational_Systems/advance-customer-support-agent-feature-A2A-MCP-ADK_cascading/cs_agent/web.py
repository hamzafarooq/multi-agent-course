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

import json
import logging
import os
import sys

logging.getLogger().setLevel(logging.ERROR)

_this_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_this_dir)
for p in (_this_dir, _project_root):
    if p not in sys.path:
        sys.path.insert(0, p)

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from pydantic import BaseModel
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from memory import search_memory, save_memory
from prompts import SQL_PROMPT_INSTRUCTION
from greet import authenticate_user
from cs_agent.security.sanitizer import sanitize_input
from cs_agent.a2a.client import call_a2a_agent
from telemetry import get_tracer, ATTR

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

# Observability (Phoenix). No-op unless TELEMETRY=true — see telemetry.py / .env.
tracer = get_tracer()

# Cascade profile — hard-coded ports (kept distinct from the s2s app so both can run
# at once). A2A Judge/Mask, and the MCP Toolbox this app talks to.
A2A_JUDGE_HOST = "localhost"
A2A_JUDGE_PORT = 10002
A2A_MASK_HOST = "localhost"
A2A_MASK_PORT = 10003

toolbox_client = ToolboxSyncClient(url="http://127.0.0.1:5000")
database_tools = toolbox_client.load_toolset("cs_agent_tools")

session_service = InMemorySessionService()
_runners: dict[str, Runner] = {}   # user_id -> Runner
_transcripts: dict[str, list] = {}  # user_id -> running [{role, content}] for this session,
                                    # flushed to Mem0 on logout (mirrors the CLI's save-on-quit)


def _record(user_id: str, role: str, content: str) -> None:
    """Append one message to this user's session transcript (persisted on logout)."""
    if user_id and content:
        _transcripts.setdefault(user_id, []).append({"role": role, "content": content})


app = FastAPI(title="Customer Support Agent")


class LoginReq(BaseModel):
    email: str
    password: str


class ChatReq(BaseModel):
    user_id: str
    message: str


class LogoutReq(BaseModel):
    user_id: str


def _build_runner(user_id: str) -> Runner:
    agent = LlmAgent(
        model="gemini-2.5-flash",
        name="customer_support_assistant",
        description="Customer support agent for order questions and requests.",
        instruction=SQL_PROMPT_INSTRUCTION.format(USER_ID=user_id),
        tools=[*database_tools, search_memory],
    )
    return Runner(agent=agent, app_name="agents", session_service=session_service)


async def _judge(text: str) -> bool:
    """Return True if the Security Judge clears the input."""
    verdict = await call_a2a_agent(query=text, host=A2A_JUDGE_HOST, port=A2A_JUDGE_PORT)
    return "BLOCKED" not in (verdict or "").upper()


# MASK=false skips the A2A Masker entirely (no round-trip, no latency). Default true.
MASK_ENABLED = os.getenv("MASK", "true").strip().lower() in ("1", "true", "yes", "on")


async def _mask(text: str) -> str:
    if not MASK_ENABLED:
        return text
    try:
        masked = await call_a2a_agent(query=text, host=A2A_MASK_HOST, port=A2A_MASK_PORT)
        return (masked or text).lower() if masked else text
    except Exception:
        return text


@app.post("/api/login")
async def login(req: LoginReq):
    ctx = authenticate_user(email=req.email, password=req.password)
    if not ctx:
        return JSONResponse({"ok": False, "error": "Invalid email or password."}, status_code=401)
    uid = ctx["email"]
    _runners[uid] = _build_runner(uid)
    _transcripts[uid] = []            # fresh session transcript (drop any stale unsaved buffer)
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
    # Persist this session's conversation to Mem0 — the web equivalent of the CLI's
    # save_memory(...) on `quit`. Fired by the Sign-out button AND by the browser tab
    # closing (sendBeacon -> /api/logout). pop() makes it save-once even if both fire.
    messages = _transcripts.pop(req.user_id, None)
    if messages:
        try:
            save_memory(messages, req.user_id)
        except Exception:
            pass
    try:
        await session_service.delete_session(
            app_name="agents", user_id=req.user_id, session_id=f"session_{req.user_id}")
    except Exception:
        pass
    return {"ok": True}


@app.post("/api/chat")
async def chat(req: ChatReq):
    runner = _runners.get(req.user_id)
    if runner is None:
        return JSONResponse({"ok": False, "error": "Not logged in."}, status_code=401)

    # One trace span per turn (text path). Sub-spans mirror the CLI: sanitize ->
    # judge -> per-tool -> mask. The agent's own model call is auto-instrumented.
    with tracer.start_as_current_span("agent.turn") as turn_span:
        turn_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "CHAIN")
        turn_span.set_attribute(ATTR.INPUT_VALUE, req.message)
        turn_span.set_attribute("user.id", req.user_id)
        turn_span.set_attribute("turn.channel", "text")

        # Layer 1 — local sanitization
        with tracer.start_as_current_span("security.sanitize") as s_span:
            s_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            s_span.set_attribute(ATTR.INPUT_VALUE, req.message)
            try:
                clean = sanitize_input(req.message)
                s_span.set_attribute(ATTR.OUTPUT_VALUE, "passed")
            except ValueError as exc:
                s_span.set_attribute(ATTR.OUTPUT_VALUE, f"blocked: {exc}")
                turn_span.set_attribute("turn.blocked", True)
                turn_span.set_attribute("turn.block_reason", "sanitizer")
                return {"ok": True, "blocked": True, "stage": "sanitizer",
                        "response": f"Input rejected by sanitizer: {exc}", "tool_calls": []}

        # Layer 2 — A2A Security Judge
        with tracer.start_as_current_span("security.a2a_judge") as j_span:
            j_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            j_span.set_attribute(ATTR.INPUT_VALUE, clean)
            try:
                passed = await _judge(clean)
            except Exception as exc:
                j_span.set_attribute(ATTR.OUTPUT_VALUE, f"error: {exc}")
                return JSONResponse({"ok": False, "error": f"Security Judge unreachable: {exc}"}, status_code=502)
            j_span.set_attribute(ATTR.OUTPUT_VALUE, "passed" if passed else "blocked")
        if not passed:
            turn_span.set_attribute("turn.blocked", True)
            turn_span.set_attribute("turn.block_reason", "judge")
            turn_span.set_attribute(ATTR.OUTPUT_VALUE, "BLOCKED: judge")
            return {"ok": True, "blocked": True, "stage": "judge",
                    "response": "Blocked by the A2A Security Judge (possible injection/unsafe input).",
                    "tool_calls": []}

        # Agent turn (+ MCP tools)
        content = types.Content(role="user", parts=[types.Part(text=clean)])
        tool_calls, final_text = [], ""
        for event in runner.run(user_id=req.user_id, session_id=f"session_{req.user_id}", new_message=content):
            for fc in (event.get_function_calls() or []):
                tool_calls.append({"name": fc.name, "args": dict(fc.args or {}), "result": None})
            for fr in (event.get_function_responses() or []):
                rs = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                for tc in reversed(tool_calls):
                    if tc["name"] == fr.name and tc["result"] is None:
                        tc["result"] = rs[:800]
                        with tracer.start_as_current_span(f"tool.{fr.name}") as tc_span:
                            tc_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
                            tc_span.set_attribute(ATTR.TOOL_NAME, fr.name)
                            tc_span.set_attribute(ATTR.INPUT_VALUE, json.dumps(tc["args"]))
                            tc_span.set_attribute(ATTR.OUTPUT_VALUE, tc["result"])
                        break
            if event.is_final_response() and event.content:
                final_text = event.content.parts[0].text

        # Layer 3 — A2A Data Masker on the way out
        with tracer.start_as_current_span("security.a2a_mask") as m_span:
            m_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            m_span.set_attribute(ATTR.INPUT_VALUE, final_text[:500])
            masked = await _mask(final_text)
            m_span.set_attribute(ATTR.OUTPUT_VALUE, masked[:500])

        if tool_calls:
            turn_span.set_attribute("llm.tool_calls", json.dumps([t["name"] for t in tool_calls]))
        turn_span.set_attribute(ATTR.OUTPUT_VALUE, masked)
        _record(req.user_id, "user", req.message)
        _record(req.user_id, "assistant", masked)
        return {"ok": True, "blocked": False, "response": masked, "tool_calls": tool_calls}


@app.post("/api/chat/stream")
async def chat_stream(req: ChatReq):
    """Same pipeline as /api/chat, but streams the reply as newline-delimited JSON.

    Emits: {"type":"tool_call"|"delta"|"final"|"blocked"|"error", ...}.
    `delta` carries the cumulative text so far (the client just re-renders it).
    Streaming only happens when MASK is off — you can't stream a reply you must
    mask as a whole, so with MASK=true this sends a single `final` chunk instead.
    """
    runner = _runners.get(req.user_id)
    if runner is None:
        return JSONResponse({"ok": False, "error": "Not logged in."}, status_code=401)

    async def gen():
      # One trace span per streamed turn (text path). No-op unless TELEMETRY=true.
      with tracer.start_as_current_span("agent.turn") as turn_span:
        turn_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "CHAIN")
        turn_span.set_attribute(ATTR.INPUT_VALUE, req.message)
        turn_span.set_attribute("user.id", req.user_id)
        turn_span.set_attribute("turn.channel", "text-stream")

        # Layer 1 — local sanitization
        with tracer.start_as_current_span("security.sanitize") as s_span:
            s_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            s_span.set_attribute(ATTR.INPUT_VALUE, req.message)
            try:
                clean = sanitize_input(req.message)
                s_span.set_attribute(ATTR.OUTPUT_VALUE, "passed")
            except ValueError as exc:
                s_span.set_attribute(ATTR.OUTPUT_VALUE, f"blocked: {exc}")
                turn_span.set_attribute("turn.blocked", True)
                yield json.dumps({"type": "blocked", "stage": "sanitizer",
                                  "response": f"Input rejected by sanitizer: {exc}"}) + "\n"
                return

        # Layer 2 — A2A Security Judge
        with tracer.start_as_current_span("security.a2a_judge") as j_span:
            j_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
            j_span.set_attribute(ATTR.INPUT_VALUE, clean)
            try:
                passed = await _judge(clean)
            except Exception as exc:
                j_span.set_attribute(ATTR.OUTPUT_VALUE, f"error: {exc}")
                yield json.dumps({"type": "error", "message": f"Security Judge unreachable: {exc}"}) + "\n"
                return
            j_span.set_attribute(ATTR.OUTPUT_VALUE, "passed" if passed else "blocked")
        if not passed:
            turn_span.set_attribute("turn.blocked", True)
            turn_span.set_attribute("turn.block_reason", "judge")
            yield json.dumps({"type": "blocked", "stage": "judge",
                              "response": "Blocked by the A2A Security Judge "
                                          "(possible injection/unsafe input)."}) + "\n"
            return

        content = types.Content(role="user", parts=[types.Part(text=clean)])
        tool_calls, display = [], ""

        if not MASK_ENABLED:
            # STREAM: push each partial delta as the agent generates it.
            seen_partial = False
            async for event in runner.run_async(
                    user_id=req.user_id, session_id=f"session_{req.user_id}",
                    new_message=content, run_config=RunConfig(streaming_mode=StreamingMode.SSE)):
                for fc in (event.get_function_calls() or []):
                    tool_calls.append({"name": fc.name, "args": dict(fc.args or {}), "result": None})
                    yield json.dumps({"type": "tool_call", "name": fc.name,
                                      "args": dict(fc.args or {})}) + "\n"
                for fr in (event.get_function_responses() or []):
                    rs = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                    for tc in reversed(tool_calls):
                        if tc["name"] == fr.name and tc["result"] is None:
                            tc["result"] = rs[:800]
                            with tracer.start_as_current_span(f"tool.{fr.name}") as tc_span:
                                tc_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
                                tc_span.set_attribute(ATTR.TOOL_NAME, fr.name)
                                tc_span.set_attribute(ATTR.INPUT_VALUE, json.dumps(tc["args"]))
                                tc_span.set_attribute(ATTR.OUTPUT_VALUE, tc["result"])
                            break
                txt = None
                if event.content and event.content.parts and event.content.parts[0].text:
                    txt = event.content.parts[0].text
                if txt is None:
                    continue
                if getattr(event, "partial", False):
                    seen_partial = True
                elif seen_partial:
                    continue          # redundant final aggregate that repeats the partials
                display += txt
                yield json.dumps({"type": "delta", "text": display}) + "\n"
            turn_span.set_attribute(ATTR.OUTPUT_VALUE, display)
            _record(req.user_id, "user", req.message)
            _record(req.user_id, "assistant", display)
            yield json.dumps({"type": "final", "text": display, "tool_calls": tool_calls}) + "\n"
        else:
            # MASK on -> can't stream; run to completion, mask, send one final chunk.
            async for event in runner.run_async(
                    user_id=req.user_id, session_id=f"session_{req.user_id}", new_message=content):
                for fc in (event.get_function_calls() or []):
                    tool_calls.append({"name": fc.name, "args": dict(fc.args or {}), "result": None})
                for fr in (event.get_function_responses() or []):
                    rs = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                    for tc in reversed(tool_calls):
                        if tc["name"] == fr.name and tc["result"] is None:
                            tc["result"] = rs[:800]
                            with tracer.start_as_current_span(f"tool.{fr.name}") as tc_span:
                                tc_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
                                tc_span.set_attribute(ATTR.TOOL_NAME, fr.name)
                                tc_span.set_attribute(ATTR.INPUT_VALUE, json.dumps(tc["args"]))
                                tc_span.set_attribute(ATTR.OUTPUT_VALUE, tc["result"])
                            break
                if event.is_final_response() and event.content:
                    display = event.content.parts[0].text or ""
            with tracer.start_as_current_span("security.a2a_mask") as m_span:
                m_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
                m_span.set_attribute(ATTR.INPUT_VALUE, display[:500])
                masked = await _mask(display)
                m_span.set_attribute(ATTR.OUTPUT_VALUE, masked[:500])
            turn_span.set_attribute(ATTR.OUTPUT_VALUE, masked)
            _record(req.user_id, "user", req.message)
            _record(req.user_id, "assistant", masked)
            yield json.dumps({"type": "final", "text": masked, "tool_calls": tool_calls}) + "\n"

    return StreamingResponse(gen(), media_type="application/x-ndjson")


# Voice cascade (STT -> same pipeline as /api/chat -> TTS) — all logic lives in
# cs_agent/voice/; we only hand it the existing pipeline objects.
from cs_agent.voice.router import make_voice_router
app.include_router(make_voice_router(
    runners=_runners, session_service=session_service, judge=_judge, mask=_mask, record=_record))


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
  <h1>Customer Support Agent · cascading voice agent</h1>
  <span class="who" id="who"></span>
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
  <div class="hint">Pipeline: sanitize → A2A Security Judge → agent + MCP tools → A2A Data Masker</div>
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
function renderSteps(host,calls){
  if(!calls||!calls.length) return;
  host.innerHTML='';   // idempotent: replace the block, never stack duplicates
  const d=el(`<details class="steps"><summary>Tool steps<span class="pill">${calls.length}</span></summary></details>`);
  calls.forEach(c=>{
    const args=Object.entries(c.args||{}).map(([k,v])=>`${k}=${JSON.stringify(v)}`).join(', ');
    const step=el(`<div class="step"><div class="call">→ ${c.name}(${args})</div></div>`);
    if(c.result){const r=document.createElement('div');r.className='res';r.textContent='← '+c.result;step.appendChild(r);}
    d.appendChild(step);
  });
  host.appendChild(d);
}

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
  try{
    const r=await fetch('/api/chat/stream',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user_id:USER,message:text})});
    if(!r.ok){ const d=await r.json().catch(()=>({})); bubble.textContent=d.error||'Error'; }
    else{
      const reader=r.body.getReader(), dec=new TextDecoder();
      let buf='', calls=[];
      // Read the newline-delimited JSON stream; re-render the bubble on each delta.
      while(true){
        const {done,value}=await reader.read();
        if(done) break;
        buf+=dec.decode(value,{stream:true});
        let nl;
        while((nl=buf.indexOf('\n'))>=0){
          const line=buf.slice(0,nl).trim(); buf=buf.slice(nl+1);
          if(!line) continue;
          let d; try{ d=JSON.parse(line); }catch(e){ continue; }
          if(d.type==='tool_call'){ calls.push({name:d.name,args:d.args,result:null}); }
          else if(d.type==='delta'){ bubble.innerHTML=md(d.text||''); scroll(); }
          else if(d.type==='final'){
            const host=node.querySelector('.steps-host'); host.innerHTML='';
            renderSteps(host, d.tool_calls||calls);
            bubble.innerHTML=md(d.text||''); scroll();
          }
          else if(d.type==='blocked'){ node.classList.add('blocked'); bubble.textContent=d.response; }
          else if(d.type==='error'){ bubble.textContent='Error: '+d.message; }
        }
      }
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
// Closing the tab / navigating away is a session end too — flush memory via a beacon
// (guaranteed to send during page unload) so voice + chat get saved just like Sign out.
window.addEventListener('pagehide',()=>{
  if(USER){ try{ navigator.sendBeacon('/api/logout', new Blob([JSON.stringify({user_id:USER})],{type:'application/json'})); }catch(e){} }
});
document.getElementById('loginBtn').onclick=login;
document.getElementById('password').addEventListener('keydown',e=>{if(e.key==='Enter')login();});
document.getElementById('send').onclick=send;
const inp=document.getElementById('input');
inp.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();send();}});
inp.addEventListener('input',()=>{inp.style.height='auto';inp.style.height=Math.min(inp.scrollHeight,140)+'px';});
</script>
<script src="/voice/ui.js"></script>
</body>
</html>"""


def main():
    import uvicorn
    from cs_agent.voice.router import print_config_warnings
    host = "127.0.0.1"
    port = 8000                       # cascade profile (s2s uses 8001)
    print(f"Customer Support web UI -> http://{host}:{port}")
    print_config_warnings()
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
