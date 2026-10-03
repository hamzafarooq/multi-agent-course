/* Voice client for the customer-support cascade.
 *
 * Adds the mic / hold buttons to the chat page (static/index.html) and runs the
 * browser half of the cascade:
 *   mic @16kHz -> energy VAD (utterance endpointing) -> WS binary -> server
 *   server -> TTS PCM @24kHz chunks -> scheduled playback (queue)
 * Barge-in: if the user clearly speaks while the agent is talking, playback stops
 * client-side and an {"type":"interrupt"} is sent to cancel the turn.
 *
 * Every pipeline event the server sends (stage / step / llm / tool_call / tool_result /
 * delta / final / trace) goes through the page's renderEvent(), so a spoken turn gets
 * the same "What happened" panel as a typed one — plus "Speech to text" and "Text to
 * speech" rows. Reuses the page's globals: USER, col, el, scroll, md, addAssistant,
 * renderEvent, setStatus.
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
  let node = null;               // current assistant message (holds the "What happened" rows)
  let userBubble = null;         // the growing "You" bubble for the combined query

  // ---- self-injected UI ---------------------------------------------------
  const inwrap = document.querySelector('.inwrap');
  if (!inwrap) return;
  const MIC_SVG = '<svg viewBox="0 0 24 24" width="18" height="18" fill="currentColor" style="vertical-align:middle" aria-hidden="true"><path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3zm5-3c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/></svg>';
  const holdBtn = document.createElement('button');
  holdBtn.id = 'hold'; holdBtn.className = 'vbtn'; holdBtn.textContent = 'Hold';
  holdBtn.title = 'Pause sending your voice (mute)'; holdBtn.style.display = 'none';
  inwrap.insertBefore(holdBtn, document.getElementById('send'));
  const micBtn = document.createElement('button');
  micBtn.id = 'mic'; micBtn.className = 'vbtn'; micBtn.innerHTML = MIC_SVG; micBtn.title = 'Talk (start/stop voice)';
  inwrap.insertBefore(micBtn, document.getElementById('send'));
  const status = document.getElementById('voiceStatus');

  function setVoiceStatus(s) {
    status.textContent = s ? ('🎙 ' + s) : '';
    micBtn.classList.toggle('live', voiceOn);
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
      if (!activeSources.length) { agentSpeaking = false; if (voiceOn) setVoiceStatus('listening…'); }
    };
    setVoiceStatus('speaking…');
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
      setVoiceStatus('listening… (speech)');
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
        setVoiceStatus('transcribing…');
      } else if (voiceOn) {
        setVoiceStatus(agentSpeaking ? 'speaking…' : 'listening…');
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
      const m = el(`<div class="msg user"><div class="role">You<span class="chan">voice</span></div><div class="bubble"></div></div>`);
      col.appendChild(m);
      userBubble = m.querySelector('.bubble');
    }
    return userBubble;
  }
  // The agent message for this turn. STT rows arrive before the query is even sent, so
  // the message (and its "What happened" panel) is created on the first voice event.
  function ensureNode() {
    if (!node) {
      ensureUserBubble();
      node = addAssistant('voice');
      setStatus(node, 'Listening');
    }
    return node;
  }

  function onMessage(ev) {
    if (ev.data instanceof ArrayBuffer) { playChunk(ev.data); return; }
    let d;
    try { d = JSON.parse(ev.data); } catch (e) { return; }
    switch (d.type) {
      case 'partial_transcript':
        // the combined query, growing as bursts are appended — update one bubble
        ensureUserBubble().textContent = d.text;
        setVoiceStatus('listening…');
        scroll();
        break;
      case 'processing':
        ensureNode();
        setStatus(node, 'Running the pipeline');
        setVoiceStatus('thinking…');
        break;
      case 'response_text':
        // streamed: arrives repeatedly with growing text — update the same bubble.
        ensureNode().querySelector('.bubble').innerHTML = md(d.text || '');
        // Answer has started -> close the current "You" bubble so a mid-answer
        // interruption starts a FRESH bubble at the bottom, not the old one above.
        userBubble = null;
        scroll();
        break;
      case 'blocked':
        ensureNode().classList.add('blocked');
        node.querySelector('.bubble').textContent = d.response;
        scroll();
        break;
      case 'final':
        // renderEvent() paints the reply; response_text / blocked above keep the
        // benchmark protocol working. Both are sent, so just let renderEvent handle it.
        renderEvent(ensureNode(), d);
        break;
      case 'timing':
      case 'cost':
        // latency / cost metrics are not rendered in the UI (events still consumed).
        break;
      case 'error':
        ensureNode().querySelector('.bubble').textContent = 'Voice error: ' + (d.message || d.error);
        scroll();
        break;
      case 'turn_end':
        if (d.reason === 'interrupted') {
          // Still the same query being extended: keep the message and its STT rows,
          // drop the rows from the cancelled pipeline run, and go back to "listening".
          if (node) {
            node.querySelectorAll('.step:not([data-key="stt"])').forEach(s => s.remove());
            const pill = node.querySelector('.pill'); if (pill) pill.textContent = node.querySelectorAll('.step').length;
            node.querySelector('.bubble').innerHTML = '<span class="typing"><span class="spin"></span>Listening…</span>';
          }
        } else {
          // answered — next speech starts a fresh turn
          userBubble = null; node = null;
        }
        if (voiceOn && !agentSpeaking) setVoiceStatus('listening…');
        break;
      default:
        // stage / step / llm / tool_call / tool_result / delta / trace
        if (d.type === 'stage' && d.key === 'stt') ensureNode();
        if (node) renderEvent(node, d);
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
    const chips = document.getElementById('chips'); if (chips) chips.remove();
    holdBtn.style.display = 'inline-block';
    setVoiceStatus('listening…');
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
    holdBtn.classList.remove('on');
    setVoiceStatus('');
  }

  function toggleHold() {
    if (!voiceOn) return;
    muted = !muted;
    if (muted) {
      // drop any half-captured utterance so it isn't resumed on unmute
      speaking = false; frames = []; preroll = []; onsetCount = 0;
      holdBtn.textContent = 'Resume';
      holdBtn.classList.add('on');
      setVoiceStatus('on hold (muted)');
    } else {
      holdBtn.textContent = 'Hold';
      holdBtn.classList.remove('on');
      setVoiceStatus(agentSpeaking ? 'speaking…' : 'listening…');
    }
  }

  micBtn.onclick = () => { (voiceOn ? stopVoice() : startVoice().catch(e => {
    stopVoice(); alert('Could not start voice: ' + e);
  })); };
  holdBtn.onclick = toggleHold;
  window.addEventListener('cs:logout', () => { try { stopVoice(); } catch (e) {} });
})();
