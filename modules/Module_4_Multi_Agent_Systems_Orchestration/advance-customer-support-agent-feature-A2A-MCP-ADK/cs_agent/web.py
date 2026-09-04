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
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from google.genai import types
from google.adk.agents.llm_agent import LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from memory import search_memory
from prompts import SQL_PROMPT_INSTRUCTION
from greet import authenticate_user
from cs_agent.security.sanitizer import sanitize_input
from cs_agent.a2a.client import call_a2a_agent

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

A2A_JUDGE_HOST = os.getenv("A2A_JUDGE_HOST", "localhost")
A2A_JUDGE_PORT = int(os.getenv("A2A_JUDGE_PORT", "10002"))
A2A_MASK_HOST = os.getenv("A2A_MASK_HOST", "localhost")
A2A_MASK_PORT = int(os.getenv("A2A_MASK_PORT", "10003"))

toolbox_client = ToolboxSyncClient(url="http://127.0.0.1:5000")
database_tools = toolbox_client.load_toolset("cs_agent_tools")

session_service = InMemorySessionService()
_runners: dict[str, Runner] = {}   # user_id -> Runner

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


async def _mask(text: str) -> str:
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


@app.post("/api/chat")
async def chat(req: ChatReq):
    runner = _runners.get(req.user_id)
    if runner is None:
        return JSONResponse({"ok": False, "error": "Not logged in."}, status_code=401)

    # Layer 1 — local sanitization
    try:
        clean = sanitize_input(req.message)
    except ValueError as exc:
        return {"ok": True, "blocked": True, "stage": "sanitizer",
                "response": f"Input rejected by sanitizer: {exc}", "tool_calls": []}

    # Layer 2 — A2A Security Judge
    try:
        if not await _judge(clean):
            return {"ok": True, "blocked": True, "stage": "judge",
                    "response": "Blocked by the A2A Security Judge (possible injection/unsafe input).",
                    "tool_calls": []}
    except Exception as exc:
        return JSONResponse({"ok": False, "error": f"Security Judge unreachable: {exc}"}, status_code=502)

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
                    break
        if event.is_final_response() and event.content:
            final_text = event.content.parts[0].text

    # Layer 3 — A2A Data Masker on the way out
    masked = await _mask(final_text)
    return {"ok": True, "blocked": False, "response": masked, "tool_calls": tool_calls}


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
  <h1>Customer Support Agent</h1>
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
    const r=await fetch('/api/chat',{method:'POST',headers:{'Content-Type':'application/json'},
      body:JSON.stringify({user_id:USER,message:text})});
    const d=await r.json();
    if(!d.ok){bubble.textContent=d.error||'Error';}
    else{
      if(d.blocked) node.classList.add('blocked');
      renderSteps(node.querySelector('.steps-host'),d.tool_calls);
      bubble.innerHTML=md(d.response||'');
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
