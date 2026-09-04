"""WebSocket voice endpoint — orchestrates the cascade around the UNTOUCHED text pipeline.

Turn model (accumulate-and-combine):
  * The user can speak in several bursts. Each burst is transcribed (STT) and APPENDED
    to a pending buffer, so the query grows: "status of my order" + "and summary of
    last month".
  * Whenever the user starts speaking again, any answer in progress is STOPPED
    (the agent turn is cancelled) — the user is still adding to their question.
  * When the user goes quiet for SETTLE_MS, the WHOLE combined buffer is sent through
    sanitize -> A2A Judge -> ADK agent (+MCP tools, Mem0) -> A2A Masker -> streamed TTS.
The Judge/agent/Masker are the exact objects web.py uses for /api/chat — nothing dupes.

Protocol (see ui.js for the client side):
  client -> server   binary frame              one speech burst, 16-bit PCM mono @16kHz
  client -> server   {"type":"interrupt"}      user started speaking: stop the answer
  server -> client   {"type":"partial_transcript","text":...}   combined query so far
  server -> client   {"type":"processing"}     combined query sent to the agent
  server -> client   {"type":"tool_call"|"response_text"|"blocked"|"timing"
                      |"cost"|"turn_end"|"error", ...}
                      timing.stages = durations {judge, stt, [mask]} + timeline
                      offsets from turn start {agent_start, agent_end, tts_start,
                      tts_end} + total_response (stt + whole answer pipeline);
                      cost = {"total": usd, "stages": {stage: {in,out,usd,measured}}}
  server -> client   binary frame              TTS audio chunk, 16-bit PCM mono @24kHz
"""

import asyncio
import json
import os
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from google.genai import types
from google.adk.agents.run_config import RunConfig, StreamingMode

from cs_agent.security.sanitizer import sanitize_input
from cs_agent.voice.stt import transcribe
from cs_agent.voice.tts import synthesize_stream
from cs_agent.voice import cost
from telemetry import get_tracer, ATTR

# Observability (Phoenix). No-op unless TELEMETRY=true. Shared with web.py (idempotent).
tracer = get_tracer()


def _flag(name: str, default: str) -> bool:
    return os.getenv(name, default).strip().lower() in ("1", "true", "yes", "on")


# MASK=true  -> buffer the full reply and run the A2A Masker before speaking (safe).
# AGENT_RESPONSE_STREAM=true -> speak each sentence as the agent generates it.
# Interlock: streaming is only allowed when masking is OFF (you can't mask a reply
# you're speaking sentence-by-sentence before it exists). MASK wins.
MASK_ENABLED = _flag("MASK", "true")
AGENT_RESPONSE_STREAM = _flag("AGENT_RESPONSE_STREAM", "false")
STREAM_ENABLED = AGENT_RESPONSE_STREAM and not MASK_ENABLED


def _config_warnings() -> list[str]:
    """Surface conflicting / degenerate voice-config combinations at startup."""
    warnings = []
    if AGENT_RESPONSE_STREAM and MASK_ENABLED:
        warnings.append(
            "AGENT_RESPONSE_STREAM=true is being IGNORED because MASK=true. A reply "
            "cannot be masked while it is spoken sentence-by-sentence, so streaming is "
            "turned OFF. Set MASK=false to enable streaming.")
    if MASK_ENABLED and not os.getenv("GOOGLE_CLOUD_PROJECT", "").strip():
        warnings.append(
            "MASK=true but GOOGLE_CLOUD_PROJECT is not set. The Data Masker still runs "
            "(costing ~5s per reply) but returns the text UNMASKED — no PII is actually "
            "removed. Set GOOGLE_CLOUD_PROJECT to mask for real, or MASK=false to skip it.")
    return warnings


def print_config_warnings():
    for msg in _config_warnings():
        print(f"\033[1;33mWARNING (voice config):\033[0m {msg}")

_UI_JS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ui.js")
_AUDIO_CHUNK = 48000   # bytes per binary frame (~1s of 24 kHz PCM)
_SETTLE_MS = 1500      # quiet time after the last burst before the query is sent

# Pull the COMPLETE sentences off a growing buffer, leaving the trailing partial behind.
_SENT_END = re.compile(r"[.!?…](?:[\"')\]]+)?(?:\s|$)")


def _take_complete(buf: str):
    matches = list(_SENT_END.finditer(buf))
    if not matches:
        return "", buf
    cut = matches[-1].end()
    return buf[:cut], buf[cut:]


def make_voice_router(*, runners, session_service, judge, mask, record=None) -> APIRouter:
    router = APIRouter()

    @router.get("/voice/ui.js", include_in_schema=False)
    def ui_js():
        return FileResponse(_UI_JS, media_type="application/javascript")

    @router.websocket("/voice/ws")
    async def voice_ws(ws: WebSocket):
        await ws.accept()
        user_id = ws.query_params.get("user_id", "")
        if not user_id or user_id not in runners:
            await ws.send_text(json.dumps({"type": "error", "message": "Not logged in."}))
            await ws.close()
            return

        pending = ""                       # accumulated, not-yet-answered transcript
        stt_acc = {"in": 0, "out": 0}      # STT tokens for the bursts in `pending`
        stt_time = {"sec": 0.0}            # STT wall time summed over those bursts
        agent_task: asyncio.Task | None = None
        settle_task: asyncio.Task | None = None
        stt_lock = asyncio.Lock()          # serialize STT so bursts append in order
        ws_send_lock = asyncio.Lock()      # serialize WS sends (text loop + TTS worker
                                           # run concurrently and must not interleave frames)

        async def send_json(obj: dict):
            async with ws_send_lock:
                await ws.send_text(json.dumps(obj))

        async def send_bytes(data: bytes):
            async with ws_send_lock:
                await ws.send_bytes(data)

        # ---- the answer half of the cascade (runs on the COMBINED query) ----------
        async def run_agent(text: str):
            nonlocal pending
            answer_text = ""    # final reply for this turn; recorded to memory on success
            timing: dict[str, float] = {}
            # per-stage token counts for costing (stt already accrued in stt_acc)
            agent_tok = {"in": 0, "out": 0}
            judge_tok = {"in": 0, "out": 0}
            mask_tok = {"in": 0, "out": 0}
            tts_tok = {"in": 0, "out": 0}

            def clock(stage, t0):
                timing[stage] = round(time.perf_counter() - t0, 2)

            def mark(name):
                # absolute offset (seconds) from the turn start — for benchmark timelines
                timing[name] = round(time.perf_counter() - turn_t0, 2)

            async def send_cost():
                # Roll the per-stage tokens up into dollars. STT/agent/TTS are MEASURED
                # (real usage_metadata); Judge/Masker are ESTIMATED from text length,
                # since they run as separate A2A services that don't report tokens.
                all_stages = {
                    "stt":   {**stt_acc,   "usd": cost.usd("stt", stt_acc["in"], stt_acc["out"]), "measured": True},
                    "judge": {**judge_tok, "usd": cost.usd("llm", judge_tok["in"], judge_tok["out"]), "measured": False},
                    "agent": {**agent_tok, "usd": cost.usd("llm", agent_tok["in"], agent_tok["out"]), "measured": True},
                    "mask":  {**mask_tok,  "usd": cost.usd("llm", mask_tok["in"], mask_tok["out"]), "measured": False},
                    "tts":   {**tts_tok,   "usd": cost.usd("tts", tts_tok["in"], tts_tok["out"]), "measured": True},
                }
                # Only report stages that actually ran (e.g. the Masker is skipped in
                # streaming mode) — a $0.00000 line for a stage that never fired is noise.
                stages = {k: v for k, v in all_stages.items() if v["in"] or v["out"]}
                total = round(sum(s["usd"] for s in stages.values()), 6)
                for s in stages.values():
                    s["usd"] = round(s["usd"], 6)
                await send_json({"type": "cost", "total": total, "stages": stages})

            try:
                await send_json({"type": "processing"})
                turn_t0 = time.perf_counter()   # whole-response wall clock

                # [1] local sanitizer
                with tracer.start_as_current_span("security.sanitize") as _s_span:
                    _s_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
                    _s_span.set_attribute(ATTR.INPUT_VALUE, text)
                    try:
                        clean = sanitize_input(text)
                        _s_span.set_attribute(ATTR.OUTPUT_VALUE, "passed")
                    except ValueError as exc:
                        _s_span.set_attribute(ATTR.OUTPUT_VALUE, f"blocked: {exc}")
                        await send_json({"type": "blocked", "stage": "sanitizer",
                                         "response": f"Input rejected by sanitizer: {exc}"})
                        await send_json({"type": "turn_end"})
                        pending = ""
                        stt_acc["in"] = stt_acc["out"] = 0
                        stt_time["sec"] = 0.0
                        return

                # [2] A2A Security Judge
                t = time.perf_counter()
                with tracer.start_as_current_span("security.a2a_judge") as _j_span:
                    _j_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
                    _j_span.set_attribute(ATTR.INPUT_VALUE, clean)
                    judge_ok = await judge(clean)
                    _j_span.set_attribute(ATTR.OUTPUT_VALUE, "passed" if judge_ok else "blocked")
                if not judge_ok:
                    await send_json({"type": "blocked", "stage": "judge",
                                     "response": "Blocked by the A2A Security Judge."})
                    await send_json({"type": "turn_end"})
                    pending = ""
                    stt_acc["in"] = stt_acc["out"] = 0
                    stt_time["sec"] = 0.0
                    return
                clock("judge", t)
                # Judge is a remote A2A LLM call; estimate its tokens from the text
                # it saw in (the query) and out (a short verdict).
                judge_tok["in"] = cost.estimate_tokens(clean)
                judge_tok["out"] = 4

                runner = runners[user_id]
                content = types.Content(role="user", parts=[types.Part(text=clean)])

                if STREAM_ENABLED:
                    # ---- STREAMING (no mask) — text streams; TTS runs CONCURRENTLY --
                    # Text deltas go to the UI the instant the agent produces them and
                    # are NEVER blocked by audio. Each finished sentence is dropped on a
                    # queue; a background worker synthesises it and streams the audio
                    # chunks AS THEY ARRIVE, in parallel with ongoing text generation.
                    # So the moment a sentence exists, TTS starts on it — no delay on our
                    # side. Text leads the voice slightly (the natural cascade order).
                    t = time.perf_counter()
                    mark("agent_start")            # agent stream begins (offset from turn)
                    run_config = RunConfig(streaming_mode=StreamingMode.SSE)
                    tool_calls = []
                    tts_buffer = ""    # generated text not yet handed to TTS
                    display = ""       # full text shown so far
                    first_text = True
                    first_audio = True
                    tts_queue: asyncio.Queue = asyncio.Queue()

                    async def emit_text():
                        nonlocal first_text, pending
                        if first_text:
                            first_text = False
                            pending = ""   # answer started -> next speech is a NEW query
                        await send_json({"type": "response_text", "text": display.strip(),
                                         "tool_calls": tool_calls})

                    async def tts_worker():
                        # Synthesise queued sentences IN ORDER, streaming each one's audio
                        # as it arrives, concurrently with text. `None` = no more sentences.
                        # A failure on one sentence is skipped so the rest still play.
                        nonlocal first_audio
                        while True:
                            segment = await tts_queue.get()
                            if segment is None:
                                break
                            try:
                                async for chunk in synthesize_stream(segment, usage_out=tts_tok):
                                    if first_audio:
                                        mark("tts_start")   # first audio chunk produced
                                        first_audio = False
                                    for i in range(0, len(chunk), _AUDIO_CHUNK):
                                        await send_bytes(chunk[i:i + _AUDIO_CHUNK])
                                    mark("tts_end")         # bump to the last chunk sent
                            except asyncio.CancelledError:
                                raise
                            except Exception:
                                pass   # skip this sentence's audio, keep the worker alive

                    worker = asyncio.create_task(tts_worker())
                    try:
                        seen_partial = False
                        async for event in runner.run_async(
                                user_id=user_id, session_id=f"session_{user_id}",
                                new_message=content, run_config=run_config):
                            # count tokens on each finished LLM call (skip streaming
                            # partials, whose usage is cumulative and would double-count)
                            um = getattr(event, "usage_metadata", None)
                            if um and not getattr(event, "partial", False):
                                ti, to = cost.usage_tokens(um)
                                agent_tok["in"] += ti
                                agent_tok["out"] += to
                            # SSE surfaces the SAME function call on both the partial and
                            # the final event — only read tool calls/results on non-partial
                            # events so they aren't double-counted.
                            if not getattr(event, "partial", False):
                                for fc in (event.get_function_calls() or []):
                                    call = {"name": fc.name, "args": dict(fc.args or {}), "result": None}
                                    tool_calls.append(call)
                                    await send_json({"type": "tool_call", "name": fc.name, "args": call["args"]})
                                for fr in (event.get_function_responses() or []):
                                    rs = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                                    for tc in reversed(tool_calls):
                                        if tc["name"] == fr.name and tc["result"] is None:
                                            tc["result"] = rs[:800]
                                            with tracer.start_as_current_span(f"tool.{fr.name}") as _tc_span:
                                                _tc_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
                                                _tc_span.set_attribute(ATTR.TOOL_NAME, fr.name)
                                                _tc_span.set_attribute(ATTR.INPUT_VALUE, json.dumps(tc["args"]))
                                                _tc_span.set_attribute(ATTR.OUTPUT_VALUE, tc["result"])
                                            break
                            txt = None
                            if event.content and event.content.parts and event.content.parts[0].text:
                                txt = event.content.parts[0].text
                            if txt is None:
                                continue
                            if getattr(event, "partial", False):
                                seen_partial = True
                            elif seen_partial:
                                continue   # redundant final aggregate repeating the partials
                            display += txt
                            tts_buffer += txt
                            await emit_text()                 # text streams, never waits for TTS
                            head, tts_buffer = _take_complete(tts_buffer)
                            if head.strip():
                                tts_queue.put_nowait(head)    # hand to TTS; don't block text
                        mark("agent_end")                     # agent finished generating text
                        if tts_buffer.strip():
                            tts_queue.put_nowait(tts_buffer)  # trailing partial sentence
                        tts_queue.put_nowait(None)            # signal end-of-sentences
                        await worker                          # wait until all audio is sent
                    finally:
                        if not worker.done():
                            worker.cancel()
                        try:
                            await worker
                        except asyncio.CancelledError:
                            pass
                    # final send: guarantees the full text + tool results (with results
                    # attached) even if they landed after the last text delta.
                    await send_json({"type": "response_text", "text": display.strip(),
                                     "tool_calls": tool_calls})
                    answer_text = display.strip()
                    pending = ""
                else:
                    # ---- BUFFERED: full reply, optional A2A Masker, then speak ----
                    t = time.perf_counter()
                    mark("agent_start")
                    tool_calls, final_text = [], ""
                    async for event in runner.run_async(
                            user_id=user_id, session_id=f"session_{user_id}", new_message=content):
                        um = getattr(event, "usage_metadata", None)
                        if um:                       # one per LLM call in the tool loop
                            ti, to = cost.usage_tokens(um)
                            agent_tok["in"] += ti
                            agent_tok["out"] += to
                        for fc in (event.get_function_calls() or []):
                            call = {"name": fc.name, "args": dict(fc.args or {}), "result": None}
                            tool_calls.append(call)
                            await send_json({"type": "tool_call", "name": fc.name, "args": call["args"]})
                        for fr in (event.get_function_responses() or []):
                            rs = json.dumps(fr.response) if isinstance(fr.response, dict) else str(fr.response)
                            for tc in reversed(tool_calls):
                                if tc["name"] == fr.name and tc["result"] is None:
                                    tc["result"] = rs[:800]
                                    with tracer.start_as_current_span(f"tool.{fr.name}") as _tc_span:
                                        _tc_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "TOOL")
                                        _tc_span.set_attribute(ATTR.TOOL_NAME, fr.name)
                                        _tc_span.set_attribute(ATTR.INPUT_VALUE, json.dumps(tc["args"]))
                                        _tc_span.set_attribute(ATTR.OUTPUT_VALUE, tc["result"])
                                    break
                        if event.is_final_response() and event.content:
                            final_text = event.content.parts[0].text or ""
                    mark("agent_end")

                    if MASK_ENABLED:
                        t = time.perf_counter()
                        pre_mask = final_text
                        with tracer.start_as_current_span("security.a2a_mask") as _m_span:
                            _m_span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "GUARDRAIL")
                            _m_span.set_attribute(ATTR.INPUT_VALUE, pre_mask[:500])
                            final_text = await mask(final_text)
                            _m_span.set_attribute(ATTR.OUTPUT_VALUE, final_text[:500])
                        clock("mask", t)
                        # remote A2A call: estimate tokens from text in/out
                        mask_tok["in"] = cost.estimate_tokens(pre_mask)
                        mask_tok["out"] = cost.estimate_tokens(final_text)

                    answer_text = final_text
                    t = time.perf_counter()
                    text_sent = False
                    async for chunk in synthesize_stream(final_text, usage_out=tts_tok):
                        if not text_sent:
                            mark("tts_start")
                            await send_json({"type": "response_text", "text": final_text,
                                             "tool_calls": tool_calls})
                            text_sent = True
                            pending = ""
                        for i in range(0, len(chunk), _AUDIO_CHUNK):
                            await ws.send_bytes(chunk[i:i + _AUDIO_CHUNK])
                    mark("tts_end")
                    if not text_sent:
                        await send_json({"type": "response_text", "text": final_text,
                                         "tool_calls": tool_calls})
                        pending = ""

                # STT (the listen half) + the answer pipeline (agent fired -> done) =
                # the whole turn. `stt` is shown on its own so it can be subtracted back
                # out. Note: on a multi-burst query stt_time sums bursts that overlapped
                # your speech, so total_response is an upper bound, not strictly serial.
                answer_sec = time.perf_counter() - turn_t0
                timing["stt"] = round(stt_time["sec"], 2)
                timing["total_response"] = round(stt_time["sec"] + answer_sec, 2)
                await send_json({"type": "timing", "stages": timing})
                await send_cost()
                # Record the spoken turn into the session transcript (flushed to Mem0 on
                # logout) — the voice equivalent of the CLI appending to `messages`.
                if record and answer_text:
                    record(user_id, "user", text)
                    record(user_id, "assistant", answer_text)
                await send_json({"type": "turn_end"})
                pending = ""                          # answered — clear the buffer
                stt_acc["in"] = stt_acc["out"] = 0     # STT billed — reset for next query
                stt_time["sec"] = 0.0
            except asyncio.CancelledError:
                # user spoke again; keep `pending` (and its STT tokens) for the next run.
                await send_json({"type": "turn_end", "reason": "interrupted"})
                raise
            except Exception as exc:                  # keep the socket alive
                await send_json({"type": "error", "message": str(exc)[:300]})
                await send_json({"type": "turn_end"})
                pending = ""
                stt_acc["in"] = stt_acc["out"] = 0
                stt_time["sec"] = 0.0

        # ---- fire the agent once the user has been quiet for SETTLE_MS ------------
        async def settle_then_run():
            nonlocal agent_task
            try:
                await asyncio.sleep(_SETTLE_MS / 1000)
            except asyncio.CancelledError:
                return
            query = pending.strip()
            if query:
                agent_task = asyncio.create_task(run_agent(query))

        def restart_settle():
            nonlocal settle_task
            if settle_task and not settle_task.done():
                settle_task.cancel()
            settle_task = asyncio.create_task(settle_then_run())

        # ---- one speech burst arrived: stop any answer, transcribe, accumulate ----
        async def handle_burst(pcm: bytes):
            nonlocal pending, settle_task
            if settle_task and not settle_task.done():
                settle_task.cancel()
            async with stt_lock:
                _t = time.perf_counter()
                text, stt_usage = await transcribe(pcm)
                stt_time["sec"] += time.perf_counter() - _t   # time this burst's STT
            if text:
                pending = f"{pending} {text}".strip() if pending else text
                tin, tout = cost.usage_tokens(stt_usage)   # bill this burst's STT
                stt_acc["in"] += tin
                stt_acc["out"] += tout
                await send_json({"type": "partial_transcript", "text": pending})
            restart_settle()

        def stop_answer():
            nonlocal agent_task
            if agent_task and not agent_task.done():
                agent_task.cancel()

        try:
            while True:
                msg = await ws.receive()
                if msg.get("type") == "websocket.disconnect":
                    break
                if msg.get("bytes") is not None:
                    stop_answer()                       # a burst supersedes any answer
                    asyncio.create_task(handle_burst(msg["bytes"]))
                elif msg.get("text"):
                    try:
                        data = json.loads(msg["text"])
                    except json.JSONDecodeError:
                        continue
                    if data.get("type") == "interrupt":
                        stop_answer()                   # immediate stop on speech onset
        except WebSocketDisconnect:
            pass
        finally:
            for t in (agent_task, settle_task):
                if t and not t.done():
                    t.cancel()

    return router
