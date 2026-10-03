"""WebSocket voice endpoint — orchestrates the cascade around the UNTOUCHED text pipeline.

Turn model (accumulate-and-combine):
  * The user can speak in several bursts. Each burst is transcribed (STT) and APPENDED
    to a pending buffer, so the query grows: "status of my order" + "and summary of
    last month".
  * Whenever the user starts speaking again, any answer in progress is STOPPED
    (the agent turn is cancelled) — the user is still adding to their question.
  * When the user goes quiet for SETTLE_MS, the WHOLE combined buffer is sent through
    web.text_pipeline (sanitize -> A2A Judge -> ADK agent (+MCP tools, Mem0) -> A2A
    Masker) and the reply is streamed back as TTS audio.
The pipeline is the exact generator web.py uses for /api/chat — nothing is duplicated.

Protocol (see ui.js for the client side):
  client -> server   binary frame              one speech burst, 16-bit PCM mono @16kHz
  client -> server   {"type":"interrupt"}      user started speaking: stop the answer
  server -> client   binary frame              TTS audio chunk, 16-bit PCM mono @24kHz
  server -> client   {"type":"partial_transcript","text":...}   combined query so far
  server -> client   {"type":"processing"}     combined query sent to the pipeline
  server -> client   every text_pipeline event — stage / step / llm / tool_call /
                      tool_result / delta / final — plus voice-only steps (key "stt",
                      "tts") and {"type":"trace"}; the UI renders them in "What happened"
  server -> client   {"type":"response_text","text":..,"tool_calls":[..]}  reply text
  server -> client   {"type":"blocked","stage":..,"response":..}
  server -> client   {"type":"timing","stages":{judge, stt, [mask], agent_start,
                      agent_end, tts_start, tts_end, total_response}}
  server -> client   {"type":"cost","total":usd,"stages":{stage:{in,out,usd,measured}}}
  server -> client   {"type":"turn_end"[,"reason":"interrupted"]} | {"type":"error",..}
"""

import asyncio
import json
import os
import re
import time

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from cs_agent.voice.stt import transcribe, STT_MODEL
from cs_agent.voice.tts import synthesize_stream, TTS_MODEL, TTS_VOICE, TTS_SAMPLE_RATE
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
_BYTES_PER_SEC = TTS_SAMPLE_RATE * 2   # 16-bit mono

# Pull the COMPLETE sentences off a growing buffer, leaving the trailing partial behind.
_SENT_END = re.compile(r"[.!?…](?:[\"')\]]+)?(?:\s|$)")


def _take_complete(buf: str):
    matches = list(_SENT_END.finditer(buf))
    if not matches:
        return "", buf
    cut = matches[-1].end()
    return buf[:cut], buf[cut:]


def _ms(t0: float) -> int:
    return int((time.perf_counter() - t0) * 1000)


def make_voice_router(*, runners, pipeline, record=None, trace_url=None, mask_enabled=None) -> APIRouter:
    router = APIRouter()
    do_mask = MASK_ENABLED if mask_enabled is None else mask_enabled

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
                await ws.send_text(json.dumps(obj, default=str))

        async def send_bytes(data: bytes):
            async with ws_send_lock:
                await ws.send_bytes(data)

        def reset_query():
            nonlocal pending
            pending = ""
            stt_acc["in"] = stt_acc["out"] = 0
            stt_time["sec"] = 0.0

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
            tool_calls: list[dict] = []
            audio_bytes = {"n": 0}

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

            async def speak(segment: str, first: list):
                """Synthesize one segment and stream its audio; `first` records TTFA."""
                async for chunk in synthesize_stream(segment, usage_out=tts_tok):
                    if not first:
                        first.append(_ms(tts_t0))
                        mark("tts_start")           # first audio chunk produced
                    audio_bytes["n"] += len(chunk)
                    for i in range(0, len(chunk), _AUDIO_CHUNK):
                        await send_bytes(chunk[i:i + _AUDIO_CHUNK])
                    mark("tts_end")                 # bump to the last chunk sent

            def tts_step(first: list, chars: int):
                secs = audio_bytes["n"] / _BYTES_PER_SEC
                detail = (f"spoke {chars:,} characters as {secs:.1f} s of audio"
                          + (f", first audio after {first[0]:,} ms" if first else ", no audio produced"))
                return {"type": "step", "key": "tts", "title": "Text to speech", "status": "passed",
                        "detail": detail, "span": "tts", "ms": _ms(tts_t0), "kind": "Voice",
                        "runs": f"{TTS_MODEL} · voice {TTS_VOICE} · text in, 24 kHz PCM out"
                                + (" · sentence by sentence, concurrent with the agent" if STREAM_ENABLED else "")}

            turn = tracer.start_as_current_span("voice.turn")
            span = turn.__enter__()
            span.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "CHAIN")
            span.set_attribute(ATTR.INPUT_VALUE, text)
            span.set_attribute("user.id", user_id)
            span.set_attribute("turn.channel", "voice")
            try:
                await send_json({"type": "processing"})
                turn_t0 = time.perf_counter()   # whole-response wall clock
                t = trace_url(span) if trace_url else None
                if t:
                    await send_json({"type": "trace", "span": "voice.turn", **t})

                runner = runners[user_id]
                display, blocked = "", None
                judge_t0 = mask_t0 = None
                tts_t0 = None
                first_audio: list = []
                tts_queue: asyncio.Queue | None = None
                worker = None
                tts_buffer = ""

                async def tts_worker():
                    # STREAMING mode: synthesise queued sentences IN ORDER, streaming each
                    # one's audio as it arrives, concurrently with text. `None` = done.
                    while True:
                        segment = await tts_queue.get()
                        if segment is None:
                            break
                        try:
                            await speak(segment, first_audio)
                        except asyncio.CancelledError:
                            raise
                        except Exception:
                            pass   # skip this sentence's audio, keep the worker alive

                try:
                    async for e in pipeline(runner, user_id, text, stream=STREAM_ENABLED,
                                            turn_span=span, mask=do_mask):
                        kind = e["type"]
                        if kind == "stage":
                            if e["key"] == "judge":
                                judge_t0 = time.perf_counter()
                            elif e["key"] == "mask":
                                mask_t0 = time.perf_counter()
                            elif e["key"] == "agent" and "agent_start" not in timing:
                                mark("agent_start")
                        elif kind == "step":
                            if e["key"] == "judge" and judge_t0:
                                clock("judge", judge_t0)
                                # Judge is a remote A2A LLM call; estimate its tokens from
                                # the text it saw in (the query) and out (a short verdict).
                                judge_tok["in"] = max(1, e.get("text_chars", len(text)) // 4)
                                judge_tok["out"] = 4
                            elif e["key"] == "mask" and mask_t0:
                                clock("mask", mask_t0)
                                mask_tok["in"] = max(1, e.get("in_chars", 0) // 4)
                                mask_tok["out"] = max(1, e.get("out_chars", 0) // 4)
                        elif kind == "llm":
                            agent_tok["in"] += e.get("tokens_in") or 0
                            agent_tok["out"] += e.get("tokens_out") or 0
                        elif kind == "tool_call":
                            tool_calls.append({"name": e["name"], "args": e["args"], "result": None})
                        elif kind == "tool_result":
                            for tc in reversed(tool_calls):
                                if tc["name"] == e["name"] and tc["result"] is None:
                                    tc["result"] = json.dumps(e["result"], default=str)[:800]
                                    break
                        elif kind == "delta":
                            # Streamed text: show it at once and hand finished sentences to
                            # TTS (which runs concurrently) — text never waits for audio.
                            if "agent_end" not in timing and not display:
                                pending = ""   # answer started -> next speech is a NEW query
                                tts_t0 = time.perf_counter()
                                tts_queue = asyncio.Queue()
                                worker = asyncio.create_task(tts_worker())
                                await send_json({"type": "stage", "key": "tts", "stage": "Speaking"})
                            new = e["text"][len(display):]
                            display = e["text"]
                            tts_buffer += new
                            await send_json({"type": "response_text", "text": display.strip(),
                                             "tool_calls": tool_calls})
                            head, tts_buffer = _take_complete(tts_buffer)
                            if head.strip() and tts_queue is not None:
                                tts_queue.put_nowait(head)
                        elif kind == "final":
                            if e["blocked"]:
                                blocked = e
                            else:
                                display = e["response"]
                            mark("agent_end")
                        await send_json(e)

                    if blocked:
                        await send_json({"type": "blocked", "stage": blocked["stage"],
                                         "response": blocked["response"]})
                        await send_json({"type": "turn_end"})
                        reset_query()
                        return

                    if STREAM_ENABLED and tts_queue is not None:
                        if tts_buffer.strip():
                            tts_queue.put_nowait(tts_buffer)  # trailing partial sentence
                        tts_queue.put_nowait(None)
                        await worker                          # wait until all audio is sent
                        await send_json({"type": "response_text", "text": display.strip(),
                                         "tool_calls": tool_calls})
                        await send_json(tts_step(first_audio, len(display)))
                    else:
                        # BUFFERED: the whole (masked) reply exists — show it, then speak it.
                        await send_json({"type": "response_text", "text": display, "tool_calls": tool_calls})
                        pending = ""
                        tts_t0 = time.perf_counter()
                        await send_json({"type": "stage", "key": "tts", "stage": "Speaking"})
                        await speak(display, first_audio)
                        await send_json(tts_step(first_audio, len(display)))
                    answer_text = display.strip()
                finally:
                    if worker is not None and not worker.done():
                        worker.cancel()
                        try:
                            await worker
                        except asyncio.CancelledError:
                            pass

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
                reset_query()                          # answered — clear the buffer
            except asyncio.CancelledError:
                # user spoke again; keep `pending` (and its STT tokens) for the next run.
                span.set_attribute("turn.interrupted", True)
                await send_json({"type": "turn_end", "reason": "interrupted"})
                raise
            except Exception as exc:                  # keep the socket alive
                await send_json({"type": "error", "message": str(exc)[:300], "error": str(exc)[:300]})
                await send_json({"type": "turn_end"})
                reset_query()
            finally:
                turn.__exit__(None, None, None)

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
            await send_json({"type": "stage", "key": "stt", "stage": "Transcribing"})
            async with stt_lock:
                _t = time.perf_counter()
                text, stt_usage = await transcribe(pcm)
                stt_time["sec"] += time.perf_counter() - _t   # time this burst's STT
            tin, tout = cost.usage_tokens(stt_usage)
            audio_sec = len(pcm) / 32000                       # 16 kHz · 16-bit mono
            detail = (f'transcribed {audio_sec:.1f} s of speech → “{text}”' if text
                      else f"heard {audio_sec:.1f} s of audio but recognized no speech")
            await send_json({"type": "step", "key": "stt", "title": "Speech to text",
                             "status": "passed", "detail": detail, "span": "stt", "ms": _ms(_t),
                             "kind": "Voice", "runs": f"{STT_MODEL} · audio in, text out",
                             "extra": f"{tin:,} in / {tout:,} out tokens" if tin or tout else None})
            if text:
                pending = f"{pending} {text}".strip() if pending else text
                stt_acc["in"] += tin                            # bill this burst's STT
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
