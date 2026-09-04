/* Voice client for the customer-support cascade.
 *
 * Injects a mic button into the existing chat UI (so web.py stays untouched),
 * then runs the browser half of the cascade:
 *   mic @16kHz -> energy VAD (utterance endpointing) -> WS binary -> server
 *   server -> TTS PCM @24kHz chunks -> scheduled playback (queue)
 * Barge-in: if the user clearly speaks while the agent is talking, playback stops
 * client-side and an {"type":"interrupt"} is sent to cancel the turn.
 *
 * Reuses the page's own globals: USER, addUser, addAssistant, renderSteps, md, scroll.
 */
(function () {
  // ---- tunables (the Module 5 knobs) -------------------------------------
  const VAD_RMS = 0.02;         // energy threshold to count a frame as speech
  const BARGE_RMS = 0.05;       // higher bar to interrupt the agent (avoid self-trigger)
  const ONSET_FRAMES = 2;       // consecutive speech frames needed to start an utterance
  const BARGE_FRAMES = 3;       // consecutive loud frames needed to barge in
  const END_SILENCE_MS = 1500;  // trailing silence that ends an utterance
                                // (long enough to survive natural mid-sentence pauses;
                                //  raise it if pausing still splits your sentence)
  const MIN_UTTER_MS = 400;     // ignore utterances shorter than this
  const PLAYBACK_GRACE_MS = 400;// ignore mic right after playback starts (echo tail)
  const PREROLL_FRAMES = 3;     // frames kept before onset (avoid clipped first word)
  const FRAME = 2048;           // samples per capture frame (128ms @ 16kHz)
  const CAPTURE_RATE = 16000, PLAY_RATE = 24000;

  let ws = null, captureCtx = null, playCtx = null, stream = null, proc = null;
  let voiceOn = false, speaking = false, agentSpeaking = false, muted = false;
  let frames = [], preroll = [], silentFrames = 0, onsetCount = 0, bargeCount = 0;
  let playCursor = 0, activeSources = [], lastPlayStart = 0;
  let node = null, calls = [];   // current assistant message + its tool calls
  let userBubble = null;         // the growing "You" bubble for the combined query

  // ---- self-injected UI ---------------------------------------------------
  const inwrap = document.querySelector('.inwrap');
  if (!inwrap) return;
  const MIC_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="vertical-align:middle" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
  const micBtn = document.createElement('button');
  micBtn.id = 'mic';
  micBtn.innerHTML = MIC_SVG;
  micBtn.title = 'Voice mode';
  micBtn.style.cssText = 'background:#f1f3f6;color:#1a1d23;border:1px solid #e4e7ec;';
  inwrap.insertBefore(micBtn, document.getElementById('send'));

  // Mute / hold — like the mute button on a phone call. When held, the device's
  // audio does not go forward (nothing is captured or sent). Hidden until voice is on.
  const holdBtn = document.createElement('button');
  holdBtn.id = 'hold';
  holdBtn.textContent = 'Hold';
  holdBtn.title = 'Pause sending your voice (mute)';
  holdBtn.style.cssText = 'background:#f1f3f6;color:#1a1d23;border:1px solid #e4e7ec;display:none;';
  inwrap.insertBefore(holdBtn, document.getElementById('send'));

  const status = document.createElement('div');
  status.className = 'hint';
  status.id = 'voiceStatus';
  document.getElementById('footer').appendChild(status);

  function setStatus(s) {
    status.textContent = s ? ('🎙 ' + s) : '';
    micBtn.style.background = voiceOn ? '#0f9aae' : '#f1f3f6';
    micBtn.style.color = voiceOn ? '#fff' : '#1a1d23';
  }

  function now() { return (typeof performance !== 'undefined' ? performance.now() : Date.now()); }

  // ---- playback (agent speech) --------------------------------------------
  function playChunk(buf) {
    if (!playCtx) return;                 // context is set up on mic-button click
    const i16 = new Int16Array(buf);
    const f32 = new Float32Array(i16.length);
    for (let i = 0; i < i16.length; i++) f32[i] = i16[i] / 32768;
    const audio = playCtx.createBuffer(1, f32.length, PLAY_RATE);
    audio.getChannelData(0).set(f32);
    const src = playCtx.createBufferSource();
    src.buffer = audio;
    src.connect(playCtx.destination);
    if (playCursor < playCtx.currentTime) playCursor = playCtx.currentTime + 0.05;
    src.start(playCursor);
    playCursor += audio.duration;
    if (!agentSpeaking) lastPlayStart = now();
    agentSpeaking = true;
    activeSources.push(src);
    src.onended = () => {
      activeSources = activeSources.filter(s => s !== src);
      if (!activeSources.length) { agentSpeaking = false; if (voiceOn) setStatus('listening…'); }
    };
    setStatus('speaking…');
  }

  function stopPlayback() {
    activeSources.forEach(s => { try { s.stop(); } catch (e) {} });
    activeSources = [];
    playCursor = 0;
    agentSpeaking = false;
  }

  // ---- capture + VAD (user speech) ----------------------------------------
  function onFrame(f32) {
    if (muted) return;   // on hold: device audio does not go forward
    let sum = 0;
    for (let i = 0; i < f32.length; i++) sum += f32[i] * f32[i];
    const rms = Math.sqrt(sum / f32.length);
    const i16 = new Int16Array(f32.length);
    for (let i = 0; i < f32.length; i++) i16[i] = Math.max(-32768, Math.min(32767, f32[i] * 32768));

    if (!speaking) {
      preroll.push(i16);
      if (preroll.length > PREROLL_FRAMES) preroll.shift();

      // Detect a sustained speech onset. While the agent is talking, use a higher bar
      // (and a grace window) so its own audio/echo doesn't self-trigger; otherwise the
      // normal bar. When the user really starts, STOP the agent and start capturing —
      // this burst will be appended to the combined query.
      const speaking_now = agentSpeaking;
      if (speaking_now && (now() - lastPlayStart) < PLAYBACK_GRACE_MS) return;
      const thresh = speaking_now ? BARGE_RMS : VAD_RMS;
      const need = speaking_now ? BARGE_FRAMES : ONSET_FRAMES;
      onsetCount = (rms > thresh) ? onsetCount + 1 : 0;
      if (onsetCount < need) return;

      if (agentSpeaking) stopPlayback();                     // user speaks -> agent stops
      if (ws && ws.readyState === 1) ws.send(JSON.stringify({ type: 'interrupt' }));
      speaking = true;
      frames = preroll.slice();
      preroll = [];
      silentFrames = 0; onsetCount = 0;
      setStatus('listening… (speech)');
      return;
    }

    frames.push(i16);
    if (rms > VAD_RMS) { silentFrames = 0; return; }
    silentFrames++;
    const silenceMs = silentFrames * (FRAME / CAPTURE_RATE) * 1000;
    if (silenceMs >= END_SILENCE_MS) {   // utterance complete -> ship it
      speaking = false;
      const total = frames.reduce((n, f) => n + f.length, 0);
      const durMs = (total / CAPTURE_RATE) * 1000;
      const pcm = new Int16Array(total);
      let off = 0;
      for (const f of frames) { pcm.set(f, off); off += f.length; }
      frames = [];
      if (durMs >= MIN_UTTER_MS && ws && ws.readyState === 1) {
        ws.send(pcm.buffer);
        setStatus('thinking…');
      } else if (voiceOn) {
        setStatus(agentSpeaking ? 'speaking…' : 'listening…');
      }
    }
  }

  async function startCapture() {
    stream = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: true, noiseSuppression: true, autoGainControl: true }
    });
    captureCtx = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: CAPTURE_RATE });
    const source = captureCtx.createMediaStreamSource(stream);
    proc = captureCtx.createScriptProcessor(FRAME, 1, 1);
    proc.onaudioprocess = (e) => { if (voiceOn) onFrame(e.inputBuffer.getChannelData(0)); };
    source.connect(proc);
    proc.connect(captureCtx.destination);  // required for the node to fire
  }

  function stopCapture() {
    if (proc) { try { proc.disconnect(); } catch (e) {} proc = null; }
    if (captureCtx) { try { captureCtx.close(); } catch (e) {} captureCtx = null; }
    if (stream) { stream.getTracks().forEach(t => t.stop()); stream = null; }
    speaking = false; frames = []; preroll = []; onsetCount = 0; bargeCount = 0;
  }

  // ---- server events -------------------------------------------------------
  function ensureUserBubble() {
    if (!userBubble) {
      const m = el(`<div class="msg user"><div class="role">You</div><div class="bubble"></div></div>`);
      col.appendChild(m);
      userBubble = m.querySelector('.bubble');
    }
    return userBubble;
  }

  function onMessage(ev) {
    if (ev.data instanceof ArrayBuffer) { playChunk(ev.data); return; }
    let d;
    try { d = JSON.parse(ev.data); } catch (e) { return; }
    if (d.type === 'partial_transcript') {
      // the combined query, growing as bursts are appended — update one bubble
      ensureUserBubble().textContent = d.text;
      setStatus('listening…');
      scroll();
    } else if (d.type === 'processing') {
      calls = [];
      if (!node) node = addAssistant();      // shows "thinking…"
      setStatus('thinking…');
    } else if (d.type === 'tool_call') {
      calls.push({ name: d.name, args: d.args, result: null });
      if (!node) node = addAssistant();
      renderSteps(node.querySelector('.steps-host'), calls);   // show steps as they happen
    } else if (d.type === 'response_text') {
      // streamed: arrives repeatedly with growing text — update the same bubble.
      if (!node) node = addAssistant();
      renderSteps(node.querySelector('.steps-host'), d.tool_calls || calls);
      node.querySelector('.bubble').innerHTML = md(d.text || '');
      // Answer has started -> close the current "You" bubble so a mid-answer
      // interruption starts a FRESH bubble at the bottom, not the old one above.
      userBubble = null;
      scroll();
    } else if (d.type === 'blocked') {
      if (!node) node = addAssistant();
      node.classList.add('blocked');
      node.querySelector('.bubble').textContent = d.response;
      scroll();
    } else if (d.type === 'timing') {
      // latency metrics intentionally not rendered in the UI (event still consumed).
    } else if (d.type === 'cost') {
      // cost metrics intentionally not rendered in the UI (event still consumed).
    } else if (d.type === 'error') {
      if (!node) node = addAssistant();
      node.querySelector('.bubble').textContent = 'Voice error: ' + d.message;
      scroll();
    } else if (d.type === 'turn_end') {
      if (d.reason === 'interrupted') {
        // still the same query being extended — drop the empty "thinking…" bubble,
        // keep the growing user bubble so the next burst appends to it.
        if (node && node.querySelector('.bubble .typing')) node.remove();
        node = null;
      } else {
        // answered — next speech starts a fresh turn
        userBubble = null; node = null; calls = [];
      }
      if (voiceOn && !agentSpeaking) setStatus('listening…');
    }
  }

  // ---- toggle ---------------------------------------------------------------
  async function startVoice() {
    if (typeof USER === 'undefined' || !USER) { alert('Sign in first, then use voice.'); return; }
    // Create + resume the playback context INSIDE the click gesture, or Chrome's
    // autoplay policy leaves it suspended and no agent audio is ever heard.
    playCtx = new (window.AudioContext || window.webkitAudioContext)();
    if (playCtx.state === 'suspended') await playCtx.resume();

    const proto = location.protocol === 'https:' ? 'wss' : 'ws';
    ws = new WebSocket(`${proto}://${location.host}/voice/ws?user_id=${encodeURIComponent(USER)}`);
    ws.binaryType = 'arraybuffer';
    ws.onmessage = onMessage;
    ws.onclose = () => { if (voiceOn) stopVoice(); };
    await new Promise((res, rej) => { ws.onopen = res; ws.onerror = rej; });
    await startCapture();
    voiceOn = true;
    muted = false;
    holdBtn.style.display = 'inline-block';
    setStatus('listening…');
  }

  function stopVoice() {
    voiceOn = false;
    muted = false;
    stopCapture();
    stopPlayback();
    if (playCtx) { try { playCtx.close(); } catch (e) {} playCtx = null; }
    if (ws) { try { ws.close(); } catch (e) {} ws = null; }
    holdBtn.style.display = 'none';
    holdBtn.textContent = 'Hold';
    holdBtn.style.background = '#f1f3f6';
    holdBtn.style.color = '#1a1d23';
    setStatus('');
  }

  function toggleHold() {
    if (!voiceOn) return;
    muted = !muted;
    if (muted) {
      // drop any half-captured utterance so it isn't resumed on unmute
      speaking = false; frames = []; preroll = []; onsetCount = 0;
      holdBtn.textContent = 'Resume';
      holdBtn.style.background = '#e0a59f';
      holdBtn.style.color = '#7a2d24';
      setStatus('on hold (muted)');
    } else {
      holdBtn.textContent = 'Hold';
      holdBtn.style.background = '#f1f3f6';
      holdBtn.style.color = '#1a1d23';
      setStatus(agentSpeaking ? 'speaking…' : 'listening…');
    }
  }

  micBtn.onclick = () => { (voiceOn ? stopVoice() : startVoice().catch(e => {
    stopVoice(); alert('Could not start voice: ' + e);
  })); };
  holdBtn.onclick = toggleHold;
})();
