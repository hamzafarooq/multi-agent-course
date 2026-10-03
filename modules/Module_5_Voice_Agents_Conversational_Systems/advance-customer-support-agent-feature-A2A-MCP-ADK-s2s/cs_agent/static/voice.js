/* Speech-to-speech client (Gemini Live) for the customer-support agent.
 *
 * One full-duplex WebSocket (/api/voice): mic audio streams UP while agent audio streams
 * DOWN, so barge-in is native. Typed messages ride the same Live session, so this script
 * takes over the page's Send button (setSendImpl) — every turn, spoken or typed, goes
 * through the Live model.
 *
 * Every pipeline event the server sends (stage / step / llm / tool_call / tool_result /
 * trace / final) goes through the page's renderEvent(), so each answer gets the same
 * "What happened" panel as the cascade and Module 4 web UIs. Reuses the page's globals:
 * USER, col, el, scroll, md, addUser, addAssistant, renderEvent, setStatus, setSendImpl.
 */
(function () {
  let ws = null, wsResolve = null;
  let live = false, held = false;                 // live = voice session on; held = mic muted
  let capCtx = null, playCtx = null, capNode = null, playNode = null, micStream = null;
  let curAgent = null, lastAgent = null, txtAgent = '';

  // ---- self-injected UI ---------------------------------------------------
  const inwrap = document.querySelector('.inwrap');
  if (!inwrap) return;
  const MIC_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="vertical-align:middle" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
  const holdBtn = document.createElement('button');
  holdBtn.id = 'hold'; holdBtn.className = 'vbtn'; holdBtn.textContent = 'Hold';
  holdBtn.title = 'Hold: mute mic but keep the session'; holdBtn.style.display = 'none';
  inwrap.insertBefore(holdBtn, document.getElementById('send'));
  const micBtn = document.createElement('button');
  micBtn.id = 'mic'; micBtn.className = 'vbtn'; micBtn.innerHTML = MIC_SVG; micBtn.title = 'Talk (start/stop voice)';
  inwrap.insertBefore(micBtn, document.getElementById('send'));
  const statusEl = document.getElementById('voiceStatus');
  function setVoiceStatus(s) { statusEl.textContent = s || ''; micBtn.classList.toggle('live', live); }

  // ---- agent turn bubbles ----------------------------------------------------
  // Create the agent message for a turn; stream its transcript in; render markdown at
  // the end. The "What happened" rows attach to the same message via renderEvent().
  function startAgentTurn(channel) {
    if (curAgent) return curAgent;
    curAgent = addAssistant(channel); lastAgent = curAgent; txtAgent = '';
    if (live) setVoiceStatus('🎙 thinking…');
    return curAgent;
  }
  function agentAppend(text) {
    startAgentTurn('voice');
    const b = curAgent.querySelector('.bubble');
    if (b.querySelector('.typing')) b.textContent = '';   // drop "thinking…" on first token
    txtAgent += text; b.textContent = txtAgent; scroll();
  }
  function finishAgentTurn() {
    if (!curAgent) return;
    const b = curAgent.querySelector('.bubble');
    if (txtAgent) b.innerHTML = md(txtAgent);
    else if (b.querySelector('.typing')) b.textContent = '(no spoken response)';
    curAgent = null; txtAgent = ''; scroll();
  }
  function target() { return curAgent || lastAgent || startAgentTurn('voice'); }
  function addBlocked(text) {
    const n = el(`<div class="msg blocked"><div class="role">Blocked<span class="chan">post-hoc judge</span></div><div class="bubble">⚠️ ${text}</div></div>`);
    col.appendChild(n); scroll();
  }

  // ---- audio worklets (Blob URLs; page stays self-contained) ----------------
  const CAPTURE_WORKLET = `
class CaptureProcessor extends AudioWorkletProcessor{
  process(inputs){ const ch=inputs[0][0]; if(ch) this.port.postMessage(ch.slice(0)); return true; }
}
registerProcessor('capture-processor', CaptureProcessor);`;
  const PLAYER_WORKLET = `
class PlayerProcessor extends AudioWorkletProcessor{
  constructor(){ super(); this.q=[]; this.cur=null; this.pos=0;
    this.port.onmessage=(e)=>{ if(e.data==='flush'){this.q=[];this.cur=null;this.pos=0;} else {this.q.push(e.data);} }; }
  process(_, outputs){ const out=outputs[0][0]; let i=0;
    while(i<out.length){ if(!this.cur){ if(!this.q.length){ while(i<out.length) out[i++]=0; break; } this.cur=this.q.shift(); this.pos=0; }
      out[i++]=this.cur[this.pos++]; if(this.pos>=this.cur.length) this.cur=null; } return true; }
}
registerProcessor('player-processor', PlayerProcessor);`;
  function workletURL(code) { return URL.createObjectURL(new Blob([code], { type: 'application/javascript' })); }

  async function startPlayback() {
    if (playCtx) return;
    playCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 24000 });
    await playCtx.audioWorklet.addModule(workletURL(PLAYER_WORKLET));
    playNode = new AudioWorkletNode(playCtx, 'player-processor');
    playNode.connect(playCtx.destination);
  }
  async function startCapture() {
    micStream = await navigator.mediaDevices.getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } });
    capCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    await capCtx.audioWorklet.addModule(workletURL(CAPTURE_WORKLET));
    const src = capCtx.createMediaStreamSource(micStream);
    capNode = new AudioWorkletNode(capCtx, 'capture-processor');
    const sink = capCtx.createGain(); sink.gain.value = 0;              // keep node alive, no echo
    src.connect(capNode); capNode.connect(sink); sink.connect(capCtx.destination);
    let batch = [], n = 0;
    capNode.port.onmessage = (e) => {
      if (!live || held) return;                                     // Hold mutes the mic
      const f = e.data; batch.push(f); n += f.length;
      if (n >= 1600 && ws && ws.readyState === 1) {                  // ~100 ms @16k
        const buf = new Int16Array(n); let o = 0;
        for (const fr of batch) { for (let i = 0; i < fr.length; i++) { let s = Math.max(-1, Math.min(1, fr[i])); buf[o++] = s < 0 ? s * 0x8000 : s * 0x7FFF; } }
        ws.send(buf.buffer); batch = []; n = 0;
      }
    };
  }
  function stopCapture() { try { micStream && micStream.getTracks().forEach(t => t.stop()); } catch (e) {} try { capCtx && capCtx.close(); } catch (e) {} capCtx = capNode = micStream = null; }
  function stopPlayback() { try { playCtx && playCtx.close(); } catch (e) {} playCtx = playNode = null; }
  function playChunk(arrbuf) {
    if (!playNode) return;
    const i16 = new Int16Array(arrbuf); const f32 = new Float32Array(i16.length);
    for (let i = 0; i < i16.length; i++) f32[i] = i16[i] / 0x8000;
    playNode.port.postMessage(f32);
  }

  // ---- websocket ---------------------------------------------------------------
  function ensureWS() {
    if (ws && ws.readyState === 1) return Promise.resolve();
    return new Promise(async (resolve) => {
      await startPlayback();                                        // so typed turns can also speak
      const proto = location.protocol === 'https:' ? 'wss' : 'ws';
      ws = new WebSocket(`${proto}://${location.host}/api/voice?user_id=${encodeURIComponent(USER)}`);
      ws.binaryType = 'arraybuffer';
      ws.onmessage = onWSMessage;
      ws.onclose = () => onWSClosed();
      ws.onerror = () => setVoiceStatus('Connection error');
      wsResolve = resolve;
    });
  }
  function onWSClosed() {
    if (live) { live = false; held = false; micBtn.classList.remove('live'); holdBtn.style.display = 'none'; }
    stopCapture(); stopPlayback(); ws = null;
  }
  function onWSMessage(e) {
    if (typeof e.data !== 'string') { playChunk(e.data); if (live) setVoiceStatus('🎙 speaking…'); return; }
    const m = JSON.parse(e.data);
    switch (m.type) {
      case 'ready':
        if (wsResolve) { wsResolve(); wsResolve = null; }
        setVoiceStatus(live ? '🎙 listening…' : 'Connected'); break;
      case 'transcript':
        if (m.role === 'user') {
          if (m.mode === 'final' && (m.text || '').trim()) { finishAgentTurn(); addUser(m.text.trim(), 'voice'); startAgentTurn('voice'); }
        } else if (m.mode === 'append') agentAppend(m.text);
        break;
      case 'turn_complete':
        finishAgentTurn(); setVoiceStatus(live ? (held ? '🎙 on hold (muted)' : '🎙 listening…') : ''); break;
      case 'blocked':
        // Post-hoc judge: the model already answered, so this is a separate warning. For
        // typed text the server also sends final{blocked}, which paints the message red.
        if (m.posthoc) addBlocked(m.text);
        else if (curAgent && !txtAgent) { /* final{blocked} renders it */ }
        setVoiceStatus(live ? '🎙 listening…' : ''); break;
      case 'final':
        renderEvent(target(), m);
        if (m.blocked) { curAgent = null; txtAgent = ''; }
        break;
      case 'flush':
        if (playNode) playNode.port.postMessage('flush'); finishAgentTurn(); break;
      case 'error':
        setVoiceStatus('Error: ' + m.text); break;
      case 'tool':      // legacy event, kept for the benchmark; tool_call/tool_result carry the rows
      case 'timing':    // latency & cost metrics intentionally not rendered in the UI
        break;
      default:          // stage / step / llm / tool_call / tool_result / trace
        renderEvent(target(), m);
    }
  }

  // ---- controls -------------------------------------------------------------------
  async function toggleMic() {
    if (!live) {
      micBtn.disabled = true; setVoiceStatus('Connecting…');
      try { await ensureWS(); await startCapture(); }
      catch (e) { setVoiceStatus('Mic/audio error: ' + e.message); micBtn.disabled = false; return; }
      live = true; held = false;
      const chips = document.getElementById('chips'); if (chips) chips.remove();
      micBtn.classList.add('live'); micBtn.disabled = false; micBtn.title = 'Stop voice';
      holdBtn.style.display = 'inline-block'; holdBtn.textContent = 'Hold'; holdBtn.classList.remove('on');
      setVoiceStatus('🎙 listening…');
    } else { endSession(); }
  }
  function endSession() {
    live = false; held = false;
    micBtn.classList.remove('live'); micBtn.title = 'Talk (start/stop voice)';
    holdBtn.style.display = 'none';
    try { ws && ws.readyState === 1 && ws.send(JSON.stringify({ type: 'end' })); } catch (e) {}
    try { ws && ws.close(); } catch (e) {}
    stopCapture(); setVoiceStatus('Voice ended — tap the mic to talk again');
  }
  function toggleHold() {
    if (!live) return;
    held = !held;
    // Mic stays "on" (session active) during hold — only the audio is muted.
    if (held) { holdBtn.textContent = 'Resume'; holdBtn.classList.add('on'); setVoiceStatus('🎙 on hold (muted)'); }
    else { holdBtn.textContent = 'Hold'; holdBtn.classList.remove('on'); setVoiceStatus('🎙 listening…'); }
  }
  // Typed turns go through the same Live session (sanitized + judged first, server side).
  async function sendText(text) {
    finishAgentTurn(); addUser(text);
    try { await ensureWS(); ws.send(JSON.stringify({ type: 'text', text })); startAgentTurn(); }
    catch (e) { setVoiceStatus('Connection error'); }
  }
  setSendImpl(sendText);

  micBtn.onclick = toggleMic;
  holdBtn.onclick = toggleHold;
  window.addEventListener('cs:logout', () => { try { endSession(); } catch (e) {} });
})();
