"""Standalone voice (speech-to-speech) web app for the customer-support agent.

This is a SEPARATE FastAPI app from ``cs_agent/web.py`` — it runs on its own port
(default 8001) and imports the shared building blocks (auth, MCP tools, Mem0,
prompts, A2A client) rather than duplicating them. The text CLI (``agent_cli.py``)
and the text web UI (``web.py``) are left completely untouched, so they keep working
exactly as before.

Run it:  ./run.sh voice        (or: python -m cs_agent.web)
Needs the same services as the text UI: Postgres, MCP Toolbox (:5000), A2A (:10002/:10003),
plus a GOOGLE_API_KEY whose project has access to the Gemini Live model (see voice.py:VOICE_MODEL).

Browser note: microphone capture requires a secure context — http://127.0.0.1 / localhost
qualifies; a bare LAN IP over http does not (browsers block getUserMedia there).
"""

import warnings
warnings.filterwarnings("ignore")
warnings.showwarning = lambda *a, **k: None

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
from fastapi import FastAPI, WebSocket
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from toolbox_core import ToolboxSyncClient

from memory import search_memory, save_memory
from greet import authenticate_user
from cs_agent.voice import make_voice_agent, run_voice_session, VOICE_MODEL, VOICE_NAME
from telemetry import get_tracer

load_dotenv()
os.environ.pop("GOOGLE_GENAI_USE_VERTEXAI", None)

# Observability (Phoenix). No-op unless TELEMETRY=true — see telemetry.py / .env.
# Init here so the Live model calls in voice.py are auto-instrumented for both
# typed and spoken turns (they share this process).
get_tracer()

logger = logging.getLogger(__name__)

# s2s profile — its OWN MCP Toolbox on 5001 (cascade uses 5000), so both run at once.
toolbox_client = ToolboxSyncClient(url="http://127.0.0.1:5001")
database_tools = toolbox_client.load_toolset("cs_agent_tools")

session_service = InMemorySessionService()
_runners: dict[str, Runner] = {}   # user_id -> Runner (Live model)
_transcripts: dict[str, list] = {}  # user_id -> running [{role, content}] for this session,
                                    # flushed to Mem0 on logout (mirrors the CLI's save-on-quit)


def _record(user_id: str, role: str, content: str) -> None:
    """Append one message to this user's session transcript (persisted on logout)."""
    if user_id and content:
        _transcripts.setdefault(user_id, []).append({"role": role, "content": content})


app = FastAPI(title="Customer Support Voice Agent")


class LoginReq(BaseModel):
    email: str
    password: str


class LogoutReq(BaseModel):
    user_id: str


def _build_runner(user_id: str) -> Runner:
    agent = make_voice_agent(user_id, [*database_tools, search_memory])
    return Runner(agent=agent, app_name="voice_agents", session_service=session_service)


@app.post("/api/login")
async def login(req: LoginReq):
    ctx = authenticate_user(email=req.email, password=req.password)
    if not ctx:
        return JSONResponse({"ok": False, "error": "Invalid email or password."}, status_code=401)
    uid = ctx["email"]
    _runners[uid] = _build_runner(uid)
    _transcripts[uid] = []            # fresh session transcript (drop any stale unsaved buffer)
    return {
        "ok": True,
        "user_id": uid,
        "full_name": ctx.get("full_name"),
        "is_premium": bool(ctx.get("is_premium_customer")),
        "items": ctx.get("total_items_purchased", 0),
        "model": VOICE_MODEL,
        "voice": VOICE_NAME,
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
            app_name="voice_agents", user_id=req.user_id, session_id=f"voice_{req.user_id}")
    except Exception:
        pass
    return {"ok": True}


@app.websocket("/api/voice")
async def voice_ws(websocket: WebSocket):
    await websocket.accept()
    user_id = websocket.query_params.get("user_id", "")
    runner = _runners.get(user_id)
    if runner is None:
        await websocket.send_json({"type": "error", "text": "Not logged in. Sign in first."})
        await websocket.close()
        return

    session_id = f"voice_{user_id}"
    # Fresh session per connection so a reconnect/reload doesn't 500 on a dup id.
    try:
        await session_service.delete_session(
            app_name="voice_agents", user_id=user_id, session_id=session_id)
    except Exception:
        pass
    await session_service.create_session(
        app_name="voice_agents", user_id=user_id, session_id=session_id)

    await websocket.send_json({"type": "ready"})
    try:
        await run_voice_session(websocket, runner, user_id, session_id, record=_record)
    except Exception as exc:  # noqa: BLE001
        logger.exception("voice_ws error: %s", exc)
    finally:
        try:
            await websocket.close()
        except Exception:
            pass


@app.get("/", response_class=HTMLResponse)
def index():
    return HTMLResponse(INDEX_HTML)


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>Customer Support · Voice</title>
<style>
  :root{
    --bg:#f7f8fa; --panel:#ffffff; --panel-2:#f1f3f6; --line:#e4e7ec;
    --text:#1a1d23; --muted:#6b7280; --accent:#0f9aae; --accent-2:#0c8294;
    --user:#eef1f6; --tool:#f4f6f9; --live:#e5484d;
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
  .col{width:100%;max-width:760px;margin:0 auto;padding:24px 20px 170px}
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
  .steps{margin:0 0 10px;border:1px solid var(--line);border-radius:12px;background:var(--tool);overflow:hidden}
  .steps summary{cursor:pointer;padding:9px 13px;color:var(--muted);font-size:13px;user-select:none;list-style:none}
  .steps summary::-webkit-details-marker{display:none}
  .steps summary .pill{display:inline-block;background:var(--panel-2);border:1px solid var(--line);
       border-radius:999px;padding:1px 9px;margin-left:6px;font-size:12px;color:var(--accent)}
  .step{padding:10px 14px;border-top:1px solid var(--line);font-size:13px}
  .step .call{color:var(--accent)}
  .step .res{color:var(--muted);white-space:pre-wrap;word-break:break-word;margin-top:4px;
       font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:12px}
  .blocked .bubble{border-color:#e0a59f;background:#fdecea;color:#a23b30}
  .latency{margin-top:8px;color:var(--muted);font-size:12px;font-family:ui-monospace,SFMono-Regular,Menlo,monospace}
  .latency .lat-line{margin-top:3px;line-height:1.5}
  .latency b{color:var(--text);font-weight:700}
  .typing{color:var(--muted);font-size:13px}
  .typing::after{content:'';animation:dots 1.2s steps(4,end) infinite}
  @keyframes dots{0%{content:''}25%{content:'.'}50%{content:'..'}75%{content:'...'}}
  footer{position:fixed;bottom:0;left:0;right:0;background:linear-gradient(transparent,var(--bg) 22%);padding:14px 20px 18px}
  .inwrap{max-width:760px;margin:0 auto;display:flex;gap:8px;align-items:flex-end;
       background:var(--panel);border:1px solid var(--line);border-radius:16px;padding:8px 8px 8px 14px}
  textarea{flex:1;resize:none;border:0;outline:0;background:transparent;color:var(--text);font:inherit;max-height:140px;padding:8px 0}
  .vbtn{flex:0 0 auto;background:var(--panel-2);color:var(--text);border:1px solid var(--line);
       border-radius:11px;padding:10px 14px;font-size:15px;font-weight:600;cursor:pointer}
  .vbtn:hover{border-color:var(--accent)}
  .mic.live{background:var(--accent);border-color:var(--accent);color:#fff}
  .hold.on{background:#e0a59f;border-color:#e0a59f;color:#7a2d24}
  .send{background:var(--accent);color:#fff;border:0;border-radius:11px;padding:10px 16px;font-weight:700;cursor:pointer}
  .send:disabled{opacity:.5;cursor:default}
  .status{max-width:760px;margin:8px auto 0;color:var(--muted);font-size:13px;text-align:center;min-height:18px}
  .hint{max-width:760px;margin:2px auto 0;color:var(--muted);font-size:12px;text-align:center}
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
  .login button{width:100%;margin-top:10px;padding:12px;background:var(--accent);color:#fff;border:0;
       border-radius:11px;font-weight:700;cursor:pointer}
  .err{color:#a23b30;font-size:13px;margin-top:8px;min-height:18px}
  .seed{margin-top:14px;color:var(--muted);font-size:12px;line-height:1.7}
  .seed code{background:var(--panel-2);padding:1px 6px;border-radius:5px}
</style>
</head>
<body>
<header>
  <span class="dot"></span>
  <h1>Customer Support Agent · speech to speech voice agent</h1>
  <span class="who" id="who"></span>
  <button id="logout" class="logout" style="display:none">Sign out</button>
</header>

<main>
  <div class="col" id="col">
    <div class="login" id="login">
      <h2>Sign in</h2>
      <p>Seeded demo account. Password is the first name, lowercase.</p>
      <input id="email" placeholder="email" value="alice.jones@example.com" autocomplete="off"/>
      <input id="password" placeholder="password" type="password" value="alice"/>
      <button id="loginBtn">Sign in</button>
      <div class="err" id="loginErr"></div>
      <div class="seed">Try: <code>alice.jones@example.com</code> / <code>alice</code> ·
        <code>bob.smith@techmail.com</code> / <code>bob</code></div>
    </div>
  </div>
</main>

<footer id="footer" style="display:none">
  <div class="inwrap">
    <textarea id="input" rows="1" placeholder="Ask about your orders… or tap the mic"></textarea>
    <button id="hold" class="vbtn hold" title="Hold: mute mic but keep the session" style="display:none">Hold</button>
    <button id="mic" class="vbtn mic" title="Talk (start/stop voice)"><svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="vertical-align:middle" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg></button>
    <button id="send" class="send">Send</button>
  </div>
  <div class="status" id="status"></div>
  <div class="hint">Real-time speech-to-speech · sanitize is transcript-based here (post-hoc A2A Judge) · MCP tools + Mem0 active</div>
</footer>

<script>
// ---- tiny self-contained markdown renderer (no CDN) ----
function md(src){
  const esc=s=>s.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
  const inline=s=>esc(s)
    .replace(/`([^`]+)`/g,'<code>$1</code>')
    .replace(/\*\*([^*]+)\*\*/g,'<strong>$1</strong>')
    .replace(/(^|[^*])\*([^*]+)\*/g,'$1<em>$2</em>');
  const lines=(src||'').split(/\r?\n/); let html='',list=null;
  const closeList=()=>{if(list){html+=`</${list}>`;list=null;}};
  for(let raw of lines){ const line=raw.trimEnd(); let m;
    if(!line.trim()){closeList();continue;}
    if(m=line.match(/^(#{1,3})\s+(.*)$/)){closeList();const n=m[1].length;html+=`<h${n}>${inline(m[2])}</h${n}>`;continue;}
    if(m=line.match(/^\s*[-*]\s+(.*)$/)){if(list!=='ul'){closeList();list='ul';html+='<ul>';}html+=`<li>${inline(m[1])}</li>`;continue;}
    if(m=line.match(/^\s*\d+\.\s+(.*)$/)){if(list!=='ol'){closeList();list='ol';html+='<ol>';}html+=`<li>${inline(m[1])}</li>`;continue;}
    closeList();html+=`<p>${inline(line)}</p>`; }
  closeList(); return html;
}

// ---- state ----
let USER=null, MODEL=null;
let ws=null, wsResolve=null;
let live=false, held=false;                 // live = voice session on; held = mic muted
let capCtx=null, playCtx=null, capNode=null, playNode=null, micStream=null;
let curAgent=null, lastAgent=null, txtAgent='', toolBuffer=[];

const col=document.getElementById('col');
const footer=document.getElementById('footer');
const who=document.getElementById('who');
const statusEl=document.getElementById('status');
const micBtn=document.getElementById('mic');
const MIC_SVG='<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="vertical-align:middle" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
const holdBtn=document.getElementById('hold');
const input=document.getElementById('input');

function el(html){const t=document.createElement('template');t.innerHTML=html.trim();return t.content.firstChild;}
function scroll(){const m=document.querySelector('main');requestAnimationFrame(()=>{m.scrollTop=m.scrollHeight;});}
function setStatus(html){statusEl.innerHTML=html||'';}

// ---- chat bubbles ----
function addUser(text){
  const n=el(`<div class="msg user"><div class="role">You</div><div class="bubble"></div></div>`);
  n.querySelector('.bubble').textContent=text; col.appendChild(n); scroll();
}
function addBlocked(text){
  const n=el(`<div class="msg blocked"><div class="role">Blocked</div><div class="bubble">⚠️ ${text}</div></div>`);
  col.appendChild(n); scroll();
}
// Metrics block (2 lines) appended to an agent message at turn end.
function ensureLatency(node){
  let l=node.querySelector('.latency');
  if(!l){ l=el(`<div class="latency"></div>`); node.appendChild(l); }
  return l;
}
// Agent turn: create a bubble with a "thinking…" indicator; stream text in; on
// turn end, render collapsed tool steps (like the text web UI) and markdown.
function startAgentTurn(){
  if(curAgent) return;
  curAgent=el(`<div class="msg assistant"><div class="role">Agent</div><div class="steps-host"></div><div class="bubble"><span class="typing">thinking</span></div></div>`);
  col.appendChild(curAgent); lastAgent=curAgent; txtAgent=''; toolBuffer=[]; if(live) setStatus('🎙 thinking…'); scroll();
}
function agentAppend(text){
  startAgentTurn();
  const b=curAgent.querySelector('.bubble');
  const typ=b.querySelector('.typing'); if(typ) b.textContent='';   // drop "thinking…" on first token
  txtAgent+=text; b.textContent=txtAgent; scroll();
}
function renderSteps(host){
  if(!toolBuffer.length) return;
  const nCalls=toolBuffer.filter(c=>c.phase==='call').length||toolBuffer.length;
  const d=el(`<details class="steps"><summary>Tool steps<span class="pill">${nCalls}</span></summary></details>`);  // collapsed by default
  toolBuffer.forEach(c=>{
    const arrow=c.phase==='call'?'→':'←';
    const step=el(`<div class="step"><div class="call">${arrow} ${c.name}(${c.detail||''})</div></div>`);
    d.appendChild(step);
  });
  host.appendChild(d);
}
function finishAgentTurn(){
  if(!curAgent) return;
  renderSteps(curAgent.querySelector('.steps-host'));      // tool steps AFTER the response, collapsed
  const b=curAgent.querySelector('.bubble');
  if(txtAgent) b.innerHTML=md(txtAgent);
  else { const typ=b.querySelector('.typing'); if(typ) b.textContent='(no spoken response)'; }
  curAgent=null; txtAgent=''; toolBuffer=[]; scroll();
}

// ---- audio worklets (Blob URLs; page stays self-contained) ----
const CAPTURE_WORKLET=`
class CaptureProcessor extends AudioWorkletProcessor{
  process(inputs){ const ch=inputs[0][0]; if(ch) this.port.postMessage(ch.slice(0)); return true; }
}
registerProcessor('capture-processor', CaptureProcessor);`;
const PLAYER_WORKLET=`
class PlayerProcessor extends AudioWorkletProcessor{
  constructor(){ super(); this.q=[]; this.cur=null; this.pos=0;
    this.port.onmessage=(e)=>{ if(e.data==='flush'){this.q=[];this.cur=null;this.pos=0;} else {this.q.push(e.data);} }; }
  process(_, outputs){ const out=outputs[0][0]; let i=0;
    while(i<out.length){ if(!this.cur){ if(!this.q.length){ while(i<out.length) out[i++]=0; break; } this.cur=this.q.shift(); this.pos=0; }
      out[i++]=this.cur[this.pos++]; if(this.pos>=this.cur.length) this.cur=null; } return true; }
}
registerProcessor('player-processor', PlayerProcessor);`;
function workletURL(code){ return URL.createObjectURL(new Blob([code],{type:'application/javascript'})); }

async function startPlayback(){
  if(playCtx) return;
  playCtx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:24000});
  await playCtx.audioWorklet.addModule(workletURL(PLAYER_WORKLET));
  playNode=new AudioWorkletNode(playCtx,'player-processor');
  playNode.connect(playCtx.destination);
}
async function startCapture(){
  micStream=await navigator.mediaDevices.getUserMedia({audio:{channelCount:1,echoCancellation:true,noiseSuppression:true}});
  capCtx=new (window.AudioContext||window.webkitAudioContext)({sampleRate:16000});
  await capCtx.audioWorklet.addModule(workletURL(CAPTURE_WORKLET));
  const src=capCtx.createMediaStreamSource(micStream);
  capNode=new AudioWorkletNode(capCtx,'capture-processor');
  const sink=capCtx.createGain(); sink.gain.value=0;              // keep node alive, no echo
  src.connect(capNode); capNode.connect(sink); sink.connect(capCtx.destination);
  let batch=[], n=0;
  capNode.port.onmessage=(e)=>{
    if(!live || held) return;                                     // Hold mutes the mic
    const f=e.data; batch.push(f); n+=f.length;
    if(n>=1600 && ws && ws.readyState===1){                       // ~100 ms @16k
      const buf=new Int16Array(n); let o=0;
      for(const fr of batch){ for(let i=0;i<fr.length;i++){ let s=Math.max(-1,Math.min(1,fr[i])); buf[o++]=s<0?s*0x8000:s*0x7FFF; } }
      ws.send(buf.buffer); batch=[]; n=0;
    }
  };
}
function stopCapture(){ try{micStream&&micStream.getTracks().forEach(t=>t.stop());}catch(e){} try{capCtx&&capCtx.close();}catch(e){} capCtx=capNode=micStream=null; }
function stopPlayback(){ try{playCtx&&playCtx.close();}catch(e){} playCtx=playNode=null; }
function playChunk(arrbuf){
  if(!playNode) return;
  const i16=new Int16Array(arrbuf); const f32=new Float32Array(i16.length);
  for(let i=0;i<i16.length;i++) f32[i]=i16[i]/0x8000;
  playNode.port.postMessage(f32);
}

// ---- websocket ----
function ensureWS(){
  if(ws && ws.readyState===1) return Promise.resolve();
  return new Promise(async (resolve)=>{
    await startPlayback();                                        // so typed turns can also speak
    const proto=location.protocol==='https:'?'wss':'ws';
    ws=new WebSocket(`${proto}://${location.host}/api/voice?user_id=${encodeURIComponent(USER)}`);
    ws.binaryType='arraybuffer';
    ws.onmessage=onWSMessage;
    ws.onclose=()=>onWSClosed();
    ws.onerror=()=>setStatus('Connection error');
    wsResolve=resolve;
  });
}
function onWSClosed(){
  if(live){ live=false; held=false; micBtn.classList.remove('live'); micBtn.innerHTML=MIC_SVG; holdBtn.style.display='none'; }
  stopCapture(); stopPlayback(); ws=null;
}
function onWSMessage(e){
  if(typeof e.data!=='string'){ playChunk(e.data); if(live) setStatus('🎙 speaking…'); return; }
  const m=JSON.parse(e.data);
  if(m.type==='ready'){ if(wsResolve){wsResolve();wsResolve=null;} setStatus(live?'🎙 listening…':'Connected'); }
  else if(m.type==='transcript'){
    if(m.role==='user'){ if(m.mode==='final' && (m.text||'').trim()){ finishAgentTurn(); addUser(m.text.trim()); startAgentTurn(); } }
    else { if(m.mode==='append') agentAppend(m.text); }
  }
  else if(m.type==='tool'){ toolBuffer.push(m); }
  else if(m.type==='timing'){
    // latency & cost metrics intentionally not rendered in the UI (event still consumed).
  }
  else if(m.type==='turn_complete'){ finishAgentTurn(); setStatus(live?(held?'🎙 on hold (muted)':'🎙 listening…'):''); }
  else if(m.type==='blocked'){
    if(curAgent && !txtAgent){ curAgent.remove(); curAgent=null; toolBuffer=[]; }  // drop empty "thinking…"
    else finishAgentTurn();
    addBlocked(m.text); setStatus(live?'🎙 listening…':'');
  }
  else if(m.type==='flush'){ if(playNode) playNode.port.postMessage('flush'); finishAgentTurn(); }
  else if(m.type==='error'){ setStatus('Error: '+m.text); }
}

// ---- controls ----
async function toggleMic(){
  if(!live){
    micBtn.disabled=true; setStatus('Connecting…');
    try{ await ensureWS(); await startCapture(); }
    catch(e){ setStatus('Mic/audio error: '+e.message); micBtn.disabled=false; return; }
    live=true; held=false;
    micBtn.classList.add('live'); micBtn.disabled=false; micBtn.title='Stop voice';
    holdBtn.style.display='inline-block'; holdBtn.textContent='Hold'; holdBtn.classList.remove('on');
    setStatus('🎙 listening…');
  }else{ endSession(); }
}
function endSession(){
  live=false; held=false;
  micBtn.classList.remove('live'); micBtn.title='Talk (start/stop voice)';
  holdBtn.style.display='none';
  try{ ws&&ws.readyState===1&&ws.send(JSON.stringify({type:'end'})); }catch(e){}
  try{ ws&&ws.close(); }catch(e){}
  stopCapture(); setStatus('Voice ended — tap the mic to talk again');
}
function toggleHold(){
  if(!live) return;
  held=!held;
  // Mic stays "on" (session active) during hold — only the audio is muted.
  if(held){ holdBtn.textContent='Resume'; holdBtn.classList.add('on'); setStatus('🎙 on hold (muted)'); }
  else{ holdBtn.textContent='Hold'; holdBtn.classList.remove('on'); setStatus('🎙 listening…'); }
}
async function sendText(){
  const text=input.value.trim(); if(!text||!USER) return;
  const chips=document.getElementById('chips'); if(chips) chips.remove();
  input.value=''; input.style.height='auto';
  finishAgentTurn(); addUser(text);
  try{ await ensureWS(); ws.send(JSON.stringify({type:'text',text})); startAgentTurn(); }
  catch(e){ setStatus('Connection error'); }
}

// ---- login ----
async function login(){
  const email=document.getElementById('email').value.trim();
  const password=document.getElementById('password').value;
  const err=document.getElementById('loginErr'); err.textContent='';
  const r=await fetch('/api/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({email,password})});
  const d=await r.json();
  if(!d.ok){err.textContent=d.error||'Login failed';return;}
  USER=d.user_id; MODEL=d.model;
  who.textContent=`${d.full_name}${d.is_premium?' · premium':''} · ${d.model}`;
  document.getElementById('login').remove();
  document.getElementById('logout').style.display='inline-block';
  footer.style.display='block';
  col.appendChild(el(`<div class="msg assistant"><div class="role">Agent</div><div class="bubble">Hi ${d.full_name}! Tap the mic to talk, or type below. Ask about your orders — status, history, cancellations, or address changes.</div></div>`));
  renderChips(); input.focus();
}
const SAMPLES=["Where is my last order?","Show me all my orders","Cancel my processing order","I want to return order 1"];
function renderChips(){
  const wrap=el(`<div class="chips" id="chips"><div class="label">Try asking</div></div>`);
  SAMPLES.forEach(q=>{ const c=el(`<button class="chip"></button>`); c.textContent=q; c.onclick=()=>{ input.value=q; sendText(); }; wrap.appendChild(c); });
  col.appendChild(wrap); scroll();
}
async function logout(){
  try{ endSession(); }catch(e){}
  try{ if(USER) await fetch('/api/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({user_id:USER})}); }catch(e){}
  location.reload();
}

document.getElementById('logout').onclick=logout;
// Closing the tab / navigating away is a session end too — flush memory via a beacon
// (guaranteed to send during page unload) so voice + typed turns get saved like Sign out.
window.addEventListener('pagehide',()=>{
  if(USER){ try{ navigator.sendBeacon('/api/logout', new Blob([JSON.stringify({user_id:USER})],{type:'application/json'})); }catch(e){} }
});
document.getElementById('loginBtn').onclick=login;
document.getElementById('password').addEventListener('keydown',e=>{if(e.key==='Enter')login();});
document.getElementById('send').onclick=sendText;
micBtn.onclick=toggleMic;
holdBtn.onclick=toggleHold;
input.addEventListener('keydown',e=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendText();}});
input.addEventListener('input',()=>{input.style.height='auto';input.style.height=Math.min(input.scrollHeight,140)+'px';});
</script>
</body>
</html>"""


def main():
    import uvicorn
    host = "127.0.0.1"
    port = 8001                       # s2s profile (cascade uses 8000)
    print(f"Customer Support VOICE UI -> http://{host}:{port}  (model: {VOICE_MODEL}, voice: {VOICE_NAME})")
    uvicorn.run(app, host=host, port=port, log_level="warning")


if __name__ == "__main__":
    main()
