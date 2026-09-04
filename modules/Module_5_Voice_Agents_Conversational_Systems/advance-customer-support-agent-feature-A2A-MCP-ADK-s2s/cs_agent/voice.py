"""Real-time speech-to-speech (voice) engine for the customer-support agent.

This module is the *engine* only — it holds no server/socket state and opens no
external connections at import time, so it is safe to unit-test and reuse. The
FastAPI app that wires a browser WebSocket to it lives in ``cs_agent/web.py``.

How it works
------------
The same ADK ``LlmAgent`` (MCP DB tools + Mem0 ``search_memory``) is run on a
**Gemini Live** model via ADK's bidirectional streaming: ``runner.run_live()`` +
``LiveRequestQueue`` + ``RunConfig(streaming_mode=BIDI, response_modalities=["AUDIO"])``.

Audio contract (fixed by the Live API):
  * input  : 16-bit PCM, 16 kHz, mono   (mime ``audio/pcm;rate=16000``)
  * output : 16-bit PCM, 24 kHz, mono

Security note (deliberate, documented gap)
------------------------------------------
Native S2S sends the user's *audio* straight to the model, so the text pipeline
(sanitize -> A2A Judge) cannot gate it beforehand the way ``web.py`` / ``agent_cli.py``
do for typed text. We do a best-effort **transcript guardrail**: when the Live API
returns the finished transcription of what the user said, we run it past the A2A
Security Judge and flag the turn if it's blocked. This is *post-hoc* (the model has
already heard the audio) and weaker than the text pipeline — that is inherent to
native speech-to-speech. Output masking is likewise display/log-only (the spoken
audio cannot be re-masked after synthesis).
"""

import asyncio
import json
import logging
import os
import time

from google.adk.agents.llm_agent import LlmAgent
from google.adk.agents.live_request_queue import LiveRequestQueue
from google.adk.agents.run_config import RunConfig, StreamingMode
from google.genai import types

from prompts import SQL_PROMPT_INSTRUCTION
from cs_agent.a2a.client import call_a2a_agent
from cs_agent.security.sanitizer import sanitize_input
from telemetry import get_tracer, ATTR

# Observability (Phoenix). No-op unless TELEMETRY=true. The Live model calls are
# auto-instrumented once web.py calls get_tracer(); this adds a guardrail span.
tracer = get_tracer()

logger = logging.getLogger(__name__)

# Default to the latest dialog speech-to-speech model; override via env.
# (Alternatives: gemini-2.5-flash-native-audio-preview-12-2025)
VOICE_MODEL = os.getenv("VOICE_MODEL", "gemini-3.1-flash-live-preview")
# Prebuilt Live voice name (e.g. Kore, Puck, Charon, Aoede, Fenrir).
VOICE_NAME = os.getenv("VOICE_NAME", "Kore")

# Fixed by the Gemini Live API.
INPUT_SAMPLE_RATE = 16000
OUTPUT_SAMPLE_RATE = 24000
INPUT_MIME = f"audio/pcm;rate={INPUT_SAMPLE_RATE}"

# s2s profile — its OWN A2A Security Judge on 11002 (cascade uses 10002).
A2A_JUDGE_HOST = "localhost"
A2A_JUDGE_PORT = 11002

# --- Cost estimation ---------------------------------------------------------
# Per-1M-token prices (USD) for the Live model, split by modality (audio tokens
# cost much more than text). Defaults are the published rates for
# gemini-3.1-flash-live-preview (ai.google.dev/gemini-api/docs/pricing, mid-2026):
#   text-in $0.75 · audio-in $3.00 · text-out $4.50 · audio-out $12.00.
# Override via env if you switch models or the prices change.
PRICE_PER_1M = {
    "text_in":  float(os.getenv("PRICE_TEXT_IN_PER_1M",  "0.75")),
    "audio_in": float(os.getenv("PRICE_AUDIO_IN_PER_1M", "3.00")),
    "text_out": float(os.getenv("PRICE_TEXT_OUT_PER_1M", "4.50")),
    "audio_out": float(os.getenv("PRICE_AUDIO_OUT_PER_1M", "12.00")),
}

# The A2A Security Judge is a separate gemini-2.5-flash call; its token usage isn't
# returned across the A2A boundary, so its cost is ESTIMATED from the transcript
# (like the cascade's "judge $… (est)"). Rates: gemini-2.5-flash $0.30/$2.50 per 1M.
JUDGE_PRICE_IN_PER_1M = float(os.getenv("JUDGE_PRICE_IN_PER_1M", "0.30"))
JUDGE_PRICE_OUT_PER_1M = float(os.getenv("JUDGE_PRICE_OUT_PER_1M", "2.50"))
JUDGE_OVERHEAD_TOKENS = int(os.getenv("JUDGE_OVERHEAD_TOKENS", "260"))  # system prompt + tool schema


def _modality_tokens(details) -> dict:
    """Sum a usage_metadata *_tokens_details list into {TEXT, AUDIO} counts."""
    out = {"TEXT": 0, "AUDIO": 0}
    for m in (details or []):
        key = getattr(m.modality, "name", str(m.modality)).upper()
        if "AUDIO" in key:
            out["AUDIO"] += m.token_count or 0
        elif "TEXT" in key:
            out["TEXT"] += m.token_count or 0
    return out


def _compute_cost(usage) -> dict | None:
    """Estimate the USD cost of one turn from its usage_metadata.

    Uses the per-modality token breakdown (input text/audio, output audio/text);
    the prompt count reflects the current context, which the Live API re-bills each
    turn — so this is that turn's real cost, not a running total.
    """
    if not usage:
        return None
    pin = _modality_tokens(getattr(usage, "prompt_tokens_details", None))
    pout = _modality_tokens(getattr(usage, "candidates_tokens_details", None))
    in_text, in_audio = pin["TEXT"], pin["AUDIO"]
    out_audio, out_text = pout["AUDIO"], pout["TEXT"]
    # Fallbacks when the API omits per-modality details.
    if in_text == 0 and in_audio == 0:
        in_text = usage.prompt_token_count or 0
    if out_audio == 0 and out_text == 0:
        out_audio = usage.candidates_token_count or 0   # response modality is AUDIO
    usd = (
        in_text * PRICE_PER_1M["text_in"]
        + in_audio * PRICE_PER_1M["audio_in"]
        + out_text * PRICE_PER_1M["text_out"]
        + out_audio * PRICE_PER_1M["audio_out"]
    ) / 1_000_000
    return {
        "usd": round(usd, 6),
        "in_text": in_text, "in_audio": in_audio,
        "out_audio": out_audio, "out_text": out_text,
        "total_tokens": usage.total_token_count or (in_text + in_audio + out_audio + out_text),
    }


def make_voice_agent(user_id: str, tools: list) -> LlmAgent:
    """Build the voice agent — identical to the text agent but on a Live model.

    ``tools`` should be ``[*database_tools, search_memory]`` (same as web.py), so
    order lookups, action logging, and Mem0 recall all work during a spoken turn.
    """
    return LlmAgent(
        model=VOICE_MODEL,
        name="customer_support_voice",
        description=(
            "Voice-enabled customer support agent for order questions and requests."
        ),
        instruction=SQL_PROMPT_INSTRUCTION.format(USER_ID=user_id),
        tools=tools,
    )


def make_run_config() -> RunConfig:
    """RunConfig for a real-time audio-in / audio-out session."""
    return RunConfig(
        streaming_mode=StreamingMode.BIDI,
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=VOICE_NAME)
            )
        ),
        # We ask for both transcripts: input drives the security guardrail and the
        # on-screen "You said…"; output gives the on-screen agent text.
        input_audio_transcription=types.AudioTranscriptionConfig(),
        output_audio_transcription=types.AudioTranscriptionConfig(),
        # Transparent reconnect across the Live API's ~10-min connection timeout.
        session_resumption=types.SessionResumptionConfig(),
    )


def _estimate_judge_cost(text: str) -> float:
    """Rough USD estimate of the A2A Judge's own LLM cost (see note above).

    Input ≈ fixed overhead (system prompt + tool schema) + the transcript; output ≈
    the transcript echoed back plus a short verdict. ~4 chars/token. Labeled "(est)".
    """
    tok = max(1, len(text or "") // 4)
    in_tok = JUDGE_OVERHEAD_TOKENS + tok
    out_tok = tok + 20
    return round((in_tok * JUDGE_PRICE_IN_PER_1M + out_tok * JUDGE_PRICE_OUT_PER_1M) / 1_000_000, 6)


async def _judge_transcript(text: str) -> bool:
    """Return True if the A2A Security Judge clears *text*; False if BLOCKED.

    Fails open (returns True) if the Judge is unreachable — voice should not hard
    -fail on a security-service outage, and this layer is best-effort by design.
    """
    text = (text or "").strip()
    if not text:
        return True
    with tracer.start_as_current_span("security.a2a_judge") as _j_span:
        _j_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
        _j_span.set_attribute(ATTR.INPUT_VALUE, text)
        try:
            verdict = await call_a2a_agent(
                query=text, host=A2A_JUDGE_HOST, port=A2A_JUDGE_PORT
            )
            passed = "BLOCKED" not in (verdict or "").upper()
            _j_span.set_attribute(ATTR.OUTPUT_VALUE, "passed" if passed else "blocked")
            return passed
        except Exception as exc:  # noqa: BLE001 - best-effort guardrail
            logger.warning("Voice transcript guardrail: Judge unreachable: %s", exc)
            _j_span.set_attribute(ATTR.OUTPUT_VALUE, f"error(open): {exc}")
            return True


async def run_voice_session(websocket, runner, user_id: str, session_id: str, record=None) -> None:
    """Bridge a browser WebSocket to an ADK live session.

    Protocol with the browser client:
      * client -> server : binary frames = 16 kHz PCM16 mic audio.
                           text frames   = JSON control, e.g. {"type": "end"}.
      * server -> client : binary frames = 24 kHz PCM16 agent audio.
                           JSON messages = transcript / tool / control events:
        - {"type":"transcript","role":"user"|"agent","text":..,"final":bool}
        - {"type":"tool","phase":"call"|"result","name":..,"detail":..}
        - {"type":"blocked","text":..}         (transcript guardrail tripped)
        - {"type":"flush"}                      (barge-in: clear playback buffer)
        - {"type":"turn_complete"}
        - {"type":"error","text":..}
    """
    live_request_queue = LiveRequestQueue()
    run_config = make_run_config()

    # Accumulates the user's speech for the (post-hoc) transcript guardrail.
    user_buffer = {"text": ""}
    # Per-turn latency timing. t0 starts when a turn's input is ready; ttfa/ttft are
    # filled on the first agent audio / first agent transcript of that turn.
    # Per-turn state. Judge metrics are stored here and reported ONLY at turn end
    # (so the judge line never pops up mid-response). judge_mode: "concurrent" (voice)
    # or "sequential" (text); the latter is on the critical path (counted in total).
    # t0 = turn start (drives Total). agent_t0 = when the MODEL starts (drives the
    # agent TTFA/S2S) — same as t0 for voice (judge is concurrent), but AFTER the
    # blocking judge for text. So Total always includes the judge; agent(*) never does.
    turn = {"t0": None, "agent_t0": None, "ttfa": None, "ttft": None, "usage": None,
            "judge_secs": None, "judge_cost": 0.0, "judge_mode": None, "guard_task": None,
            # captured for the Phoenix `voice.turn` span (Live gives no content spans)
            "user_text": "", "agent_text": "", "tools": [],
            # tool calls awaiting their result, so we can emit a paired tool.<name> span
            # (Live delivers the call and the response in separate events)
            "pending_tools": []}
    session_totals: list[float] = []
    session_cost = {"usd": 0.0, "judge": 0.0}   # usd = S2S model; judge = est. guardrail
    bg: set = set()   # background guardrail tasks (kept referenced so they aren't GC'd)

    def _mark_turn_start() -> None:
        turn["t0"] = time.monotonic()
        turn["agent_t0"] = None
        turn["ttfa"] = None; turn["ttft"] = None; turn["usage"] = None
        turn["judge_secs"] = None; turn["judge_cost"] = 0.0
        turn["judge_mode"] = None; turn["guard_task"] = None
        turn["user_text"] = ""; turn["agent_text"] = ""; turn["tools"] = []
        turn["pending_tools"] = []

    def _mark_agent_start() -> None:
        turn["agent_t0"] = time.monotonic()

    async def _guard(full: str) -> None:
        """Voice transcript guardrail — runs CONCURRENTLY so it never delays audio.

        Its time/cost are stored on the turn and reported at turn end (not mid-turn).
        Because it overlaps the response, its latency is NOT added to total.
        """
        if not full:
            return
        t0 = time.monotonic()
        ok = await _judge_transcript(full)
        turn["judge_secs"] = round(time.monotonic() - t0, 2)
        turn["judge_cost"] = _estimate_judge_cost(full)
        turn["judge_mode"] = "concurrent"
        session_cost["judge"] += turn["judge_cost"]
        if not ok:
            logger.warning("Voice guardrail BLOCKED transcript: %r", full)
            try:
                await websocket.send_json({
                    "type": "blocked",
                    "text": "That request was flagged by the Security Judge.",
                })
            except Exception:
                pass

    async def _handle_event(event) -> None:
        # Capture the latest usage_metadata of the turn (used for cost on turn end).
        if event.usage_metadata:
            turn["usage"] = event.usage_metadata

        # 1) Agent audio out (24 kHz PCM). First audio of a turn = TTFA.
        if event.content and event.content.parts:
            for part in event.content.parts:
                blob = getattr(part, "inline_data", None)
                if blob is not None and (blob.mime_type or "").startswith("audio/"):
                    if turn["agent_t0"] is not None and turn["ttfa"] is None:
                        turn["ttfa"] = time.monotonic() - turn["agent_t0"]
                    await websocket.send_bytes(blob.data)

        # 2) Transcripts. ADK streams incremental deltas as partial=True events,
        # then repeats the WHOLE utterance once in a final partial=False aggregate
        # event. We forward only the deltas ("append") for display and treat the
        # aggregate as finalize-only ("final") — otherwise the UI shows every reply
        # twice. The guardrail runs on the accumulated full user utterance.
        it = event.input_transcription
        if it and it.text:
            if event.partial:
                user_buffer["text"] += it.text
                await websocket.send_json({
                    "type": "transcript", "role": "user",
                    "text": it.text, "mode": "append",
                })
            else:
                full = (user_buffer["text"] or it.text).strip()
                user_buffer["text"] = ""
                _mark_turn_start()   # user finished speaking -> turn clock starts
                turn["user_text"] = full   # for the Phoenix voice.turn span
                _mark_agent_start()  # voice: model starts now (judge runs concurrently)
                await websocket.send_json({
                    "type": "transcript", "role": "user",
                    "text": it.text, "mode": "final",
                })
                # Guardrail runs concurrently so it never delays the agent's audio.
                gt = asyncio.create_task(_guard(full))
                turn["guard_task"] = gt
                bg.add(gt); gt.add_done_callback(bg.discard)

        ot = event.output_transcription
        if ot and ot.text:
            if turn["agent_t0"] is not None and turn["ttft"] is None:
                turn["ttft"] = time.monotonic() - turn["agent_t0"]
            if event.partial:
                turn["agent_text"] += ot.text     # deltas build the reply
            elif not turn["agent_text"]:
                turn["agent_text"] = ot.text       # aggregate if we saw no deltas
            await websocket.send_json({
                "type": "transcript", "role": "agent",
                "text": ot.text, "mode": "append" if event.partial else "final",
            })

        # 3) Tool calls / results (shown as "steps" like the text UI).
        for fc in (event.get_function_calls() or []):
            turn["tools"].append(fc.name)   # for the Phoenix voice.turn span
            # Remember the args so the matching response can emit a paired tool span.
            # (In cascade the call+result arrive together; on Live they're two events.)
            turn["pending_tools"].append(
                {"id": getattr(fc, "id", None), "name": fc.name, "args": dict(fc.args or {})}
            )
            await websocket.send_json({
                "type": "tool", "phase": "call",
                "name": fc.name, "detail": _fmt_args(fc.args),
                # structured args too (matches Module 4 / cascading web.py format);
                # detail is kept for the UI, args lets the benchmark do exact matching.
                "args": dict(fc.args or {}),
            })
        for fr in (event.get_function_responses() or []):
            # Emit a tool.<name> span carrying the args + result, like cascade's
            # router.py. Live gives no auto tool spans, so we pair the earlier call
            # (by id, else FIFO by name) with this response. Never breaks the turn.
            _emit_tool_span(turn["pending_tools"], fr)
            await websocket.send_json({
                "type": "tool", "phase": "result",
                "name": fr.name, "detail": _short(fr.response),
            })

        # 4) Control signals + per-turn timing.
        if event.interrupted:
            await websocket.send_json({"type": "flush"})
        if event.turn_complete:
            if turn["t0"] is not None:
                # Make sure the concurrent (voice) judge has finished so we can report
                # it at the end rather than mid-turn. Audio already played, so this only
                # delays the metrics line by a moment (the judge is usually long done).
                gt = turn.get("guard_task")
                if gt is not None and not gt.done():
                    try:
                        await asyncio.wait_for(asyncio.shield(gt), timeout=10)
                    except Exception:
                        pass

                total = round(time.monotonic() - turn["t0"], 2)
                session_totals.append(total)
                cost = _compute_cost(turn["usage"])
                cost_model = cost["usd"] if cost else 0.0
                if cost:
                    session_cost["usd"] += cost["usd"]
                jsecs, jmode = turn["judge_secs"], turn["judge_mode"]
                jcost = turn["judge_cost"] or 0.0
                # agent(S2S) = the model's own turn time (from agent start to end),
                # so it excludes the judge in BOTH modes. Total (from turn start) still
                # includes the sequential judge for text.
                s2s = round(time.monotonic() - turn["agent_t0"], 2) if turn["agent_t0"] else total

                # Emit a readable Phoenix span for the turn. The native Live stream gives
                # ADK only an opaque `invoke_agent` span (input/output = "--"), so we add
                # one that actually carries the transcript, reply, tools, and cost.
                with tracer.start_as_current_span("voice.turn") as _turn_span:
                    _turn_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "CHAIN")
                    _turn_span.set_attribute(ATTR.INPUT_VALUE, turn["user_text"] or "(no transcript)")
                    _turn_span.set_attribute(ATTR.OUTPUT_VALUE, turn["agent_text"] or "(audio only)")
                    _turn_span.set_attribute("turn.channel", "voice")
                    _turn_span.set_attribute("turn.latency_s", total)
                    if turn["tools"]:
                        _turn_span.set_attribute("llm.tool_calls", ", ".join(turn["tools"]))
                    if cost:
                        _turn_span.set_attribute(ATTR.LLM_TOKEN_COUNT_TOTAL, cost["total_tokens"])
                        _turn_span.set_attribute(ATTR.LLM_COST_TOTAL, round(cost_model + jcost, 6))

                # Record the spoken/typed turn into the session transcript (flushed to
                # Mem0 on logout) — the voice equivalent of the CLI appending to `messages`.
                if record:
                    record(user_id, "user", turn["user_text"])
                    record(user_id, "assistant", turn["agent_text"])

                await websocket.send_json({
                    "type": "timing",
                    "mode": "text" if jmode == "sequential" else "voice",
                    "ttfa": round(turn["ttfa"], 2) if turn["ttfa"] is not None else None,
                    "ttft": round(turn["ttft"], 2) if turn["ttft"] is not None else None,
                    "s2s": s2s,
                    "total": total,
                    "judge_secs": jsecs,
                    "judge_mode": jmode,
                    "cost_model": round(cost_model, 6),
                    "cost_judge": round(jcost, 6),
                    "cost_total": round(cost_model + jcost, 6),
                    "tokens": cost and {
                        "in_text": cost["in_text"], "in_audio": cost["in_audio"],
                        "out_audio": cost["out_audio"], "out_text": cost["out_text"],
                        "total": cost["total_tokens"],
                    },
                })
                turn["t0"] = None
            await websocket.send_json({"type": "turn_complete"})

    async def downstream() -> None:
        async for event in runner.run_live(
            user_id=user_id,
            session_id=session_id,
            live_request_queue=live_request_queue,
            run_config=run_config,
        ):
            await _handle_event(event)

    async def upstream() -> None:
        while True:
            msg = await websocket.receive()
            if msg.get("type") == "websocket.disconnect":
                break
            data = msg.get("bytes")
            if data:
                # Binary frame = 16 kHz PCM16 mic audio.
                live_request_queue.send_realtime(
                    types.Blob(data=data, mime_type=INPUT_MIME)
                )
                continue
            # Text frame = JSON control:
            #   {"type": "text", "text": "..."}  -> typed question (send as a text turn)
            #   {"type": "end"}                   -> end the session
            text = msg.get("text")
            if not text:
                continue
            try:
                obj = json.loads(text)
            except Exception:
                continue
            kind = obj.get("type")
            if kind == "end":
                break
            if kind == "text" and obj.get("text"):
                # Typed turns get the SAME pre-checks the text UI applies (sanitize +
                # A2A Judge). Unlike voice, the Judge here is BLOCKING (sequential) — it
                # delays the reply — so the turn clock starts BEFORE it, and `total`
                # correctly includes the judge. We report it as mode="blocking".
                _mark_turn_start()
                try:
                    clean = sanitize_input(obj["text"])
                except ValueError as exc:
                    await websocket.send_json({
                        "type": "blocked", "text": f"Input rejected: {exc}",
                    })
                    continue
                jt0 = time.monotonic()
                ok = await _judge_transcript(clean)
                turn["judge_secs"] = round(time.monotonic() - jt0, 2)
                turn["judge_cost"] = _estimate_judge_cost(clean)
                turn["judge_mode"] = "sequential"   # blocking -> counted in total
                session_cost["judge"] += turn["judge_cost"]
                if not ok:
                    await websocket.send_json({
                        "type": "blocked",
                        "text": "That request was flagged by the Security Judge.",
                    })
                    continue
                _mark_agent_start()  # text: model starts AFTER the blocking judge
                turn["user_text"] = clean   # typed input has no STT transcript; set it so
                                            # the turn's input is recorded to memory too
                live_request_queue.send_content(
                    types.Content(role="user", parts=[types.Part(text=clean)])
                )

    down = asyncio.create_task(downstream())
    up = asyncio.create_task(upstream())
    try:
        await asyncio.wait({down, up}, return_when=asyncio.FIRST_COMPLETED)
    except Exception as exc:  # noqa: BLE001
        logger.exception("Voice session error: %s", exc)
        try:
            await websocket.send_json({"type": "error", "text": str(exc)})
        except Exception:
            pass
    finally:
        live_request_queue.close()
        for task in (down, up):
            task.cancel()
        # Surface any non-cancellation exception from the finished task.
        for task in (down, up):
            if task.done() and not task.cancelled():
                exc = task.exception()
                if exc:
                    logger.error("Voice task ended with error: %s", exc)
        if session_totals:
            s = sorted(session_totals)
            median = s[len(s) // 2]
            grand = session_cost["usd"] + session_cost["judge"]
            print(f"[voice] session ended — {len(s)} turn(s): "
                  f"median total {median:.2f}s (min {s[0]:.2f}s, max {s[-1]:.2f}s) "
                  f"| est. cost ${grand:.4f} "
                  f"(model ${session_cost['usd']:.4f} + judge ${session_cost['judge']:.4f})")


def _fmt_args(args) -> str:
    if not args:
        return ""
    try:
        return ", ".join(f"{k}={v!r}" for k, v in dict(args).items())
    except Exception:  # noqa: BLE001
        return str(args)


def _short(value, limit: int = 300) -> str:
    s = str(value)
    return s if len(s) <= limit else s[:limit] + "…"


def _emit_tool_span(pending: list, fr) -> None:
    """Emit a Phoenix `tool.<name>` span for a completed tool call, carrying the
    input args (paired from the earlier call event) and the result — the same TOOL
    span cascade's router.py produces inline.

    Live delivers the call and its response as separate events, so we pop the matching
    entry from `pending` (by id when present, else FIFO by name). No-op when telemetry
    is off (the tracer is a stub); wrapped so it can never break a voice turn.
    """
    try:
        # Find the matching call: prefer id, else the first same-named pending call.
        args, idx = {}, None
        fr_id = getattr(fr, "id", None)
        for i, call in enumerate(pending):
            if fr_id is not None and call.get("id") == fr_id:
                idx = i
                break
            if idx is None and call.get("name") == fr.name:
                idx = i
        if idx is not None:
            args = pending.pop(idx).get("args", {}) or {}

        with tracer.start_as_current_span(f"tool.{fr.name}") as span:
            span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
            span.set_attribute(ATTR.TOOL_NAME, fr.name)
            if args:
                span.set_attribute(ATTR.INPUT_VALUE, json.dumps(args, default=str))
            span.set_attribute(ATTR.OUTPUT_VALUE, _short(fr.response, 2000))
    except Exception:  # noqa: BLE001 - telemetry must never break the turn
        pass
