"""Serve a tiny browser client for testing local LiveKit audio.

Run this after `./start_local_server.sh`, then open http://localhost:5173.
"""

from __future__ import annotations

import base64
import json
import os
import sys
import threading
import warnings
from io import BytesIO
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

import jwt
from livekit import api

from env_loader import load_env_files

HOST = os.getenv("TALK_HOST", "localhost")
PORT = int(os.getenv("TALK_PORT", "5173"))
ROOT = Path(__file__).resolve().parent
ASSIGNMENT_ROOT = ROOT.parent
PIPELINE_ROOT = ASSIGNMENT_ROOT / "pipeline"

_session_registry_lock = threading.Lock()
_agent_sessions: dict[str, object] = {}
_session_locks: dict[str, threading.Lock] = {}

GREETING = "Thanks for calling Aurora Hotel reservations. How can I help?"


def _load_env_files() -> None:
    load_env_files((PIPELINE_ROOT / ".env", ROOT / ".env"))


def _agent_provider_name() -> str:
    return os.getenv("PROVIDER", "mock").lower()


def _livekit_url() -> str:
    raw = os.getenv("LIVEKIT_URL", "ws://localhost:7880")
    if raw.startswith("http://"):
        return "ws://" + raw[len("http://"):]
    if raw.startswith("https://"):
        return "wss://" + raw[len("https://"):]
    return raw


def _livekit_api_key() -> str:
    return os.getenv("LIVEKIT_API_KEY", "devkey")


def _livekit_api_secret() -> str:
    return os.getenv("LIVEKIT_API_SECRET", "secret")


def _livekit_room() -> str:
    return os.getenv("LIVEKIT_ROOM", "aurora-demo-room")


def _new_agent():
    if str(PIPELINE_ROOT) not in sys.path:
        sys.path.insert(0, str(PIPELINE_ROOT))
    from agent import Agent
    from providers import make_provider

    return Agent(make_provider(_agent_provider_name()))


def _get_session(session_id: str):
    with _session_registry_lock:
        if session_id not in _agent_sessions:
            _agent_sessions[session_id] = _new_agent()
            _session_locks[session_id] = threading.Lock()
        return _agent_sessions[session_id], _session_locks[session_id]


def _reset_session(session_id: str) -> None:
    with _session_registry_lock:
        _agent_sessions.pop(session_id, None)
        _session_locks.pop(session_id, None)


def _trace(session_id: str, turn_id: str | None = None):
    if str(PIPELINE_ROOT) not in sys.path:
        sys.path.insert(0, str(PIPELINE_ROOT))
    from telemetry import TurnTrace

    return TurnTrace(session_id=session_id, turn_id=turn_id)


def _finish_response(agent, trace, reply: str, action: str | None, **extra) -> dict:
    from telemetry import write_trace

    sources = extra.pop("response_sources", agent.last_sources)
    payload = trace.finish(action=action, sources=sources)
    write_trace(payload)
    return {
        "reply": reply,
        "action": action,
        "provider": getattr(agent.provider, "name", _agent_provider_name()),
        "model": getattr(agent.provider, "llm_model", "unknown"),
        "language": agent.current_language,
        "locale": agent.current_locale,
        "sources": sources,
        "trace": payload,
        **extra,
    }


def _browser_tts_payload(agent, trace, text: str) -> dict:
    """Return provider audio for the browser or select its local voice fallback."""
    provider = agent.provider
    backend = getattr(provider, "tts_backend", "provider")
    if backend != "provider" or getattr(provider, "name", "") == "mock":
        return {"ttsBackend": "browser"}

    model = getattr(provider, "tts_model", "unknown")
    voice = getattr(provider, "tts_voice", "unknown")
    try:
        with trace.span("tts", model=model, voice=voice):
            audio = provider.synthesize(text)
    except Exception as exc:
        trace.event("tts.fallback", errorType=type(exc).__name__)
        return {"ttsBackend": "browser", "ttsFallback": True}

    if not audio:
        trace.event("tts.fallback", errorType="EmptyAudio")
        return {"ttsBackend": "browser", "ttsFallback": True}
    return {
        "ttsBackend": "provider",
        "ttsModel": model,
        "ttsVoice": voice,
        "audioContentType": "audio/wav",
        "audioBase64": base64.b64encode(audio).decode("ascii"),
    }


def _greeting_reply(session_id: str) -> dict:
    agent, lock = _get_session(session_id)
    trace = _trace(session_id, "greeting")
    trace.event("greeting.requested")
    with lock:
        tts = _browser_tts_payload(agent, trace, GREETING)
    return _finish_response(
        agent,
        trace,
        GREETING,
        None,
        response_sources=[],
        **tts,
    )


def _agent_reply(text: str, session_id: str, turn_id: str | None) -> dict:
    agent, lock = _get_session(session_id)
    trace = _trace(session_id, turn_id)
    trace.event("input.text")
    with lock:
        reply, action = agent.respond(text, trace=trace)
        tts = _browser_tts_payload(agent, trace, reply)
    return _finish_response(agent, trace, reply, action, **tts)


def _voice_agent_reply(
    audio: bytes,
    content_type: str,
    session_id: str,
    turn_id: str | None,
    was_barge_in: bool,
) -> dict:
    agent, lock = _get_session(session_id)
    trace = _trace(session_id, turn_id)
    trace.event("audio.received", bytes=len(audio), contentType=content_type)
    if was_barge_in:
        trace.event("barge_in.turn_started")
    with lock:
        if getattr(agent.provider, "name", "") == "mock":
            with trace.span("stt", model=getattr(agent.provider, "stt_model", "unknown")):
                transcript = agent.provider.transcribe(b"")
        else:
            audio_file = BytesIO(audio)
            if "mp4" in content_type:
                audio_file.name = "caller.mp4"
            elif "ogg" in content_type:
                audio_file.name = "caller.ogg"
            else:
                audio_file.name = "caller.webm"
            with trace.span("stt", model=getattr(agent.provider, "stt_model", "unknown")):
                transcription_args = {
                    "model": agent.provider.stt_model,
                    "file": audio_file,
                    "response_format": "text",
                }
                stt_prompt = getattr(agent.provider, "stt_prompt", "")
                if stt_prompt:
                    transcription_args["prompt"] = stt_prompt
                stt = agent.provider.client.audio.transcriptions.create(**transcription_args)
            transcript = (stt if isinstance(stt, str) else stt.text).strip()
        if was_barge_in and _is_probable_playback_echo(transcript):
            trace.event("barge_in.echo_suppressed", transcript=transcript)
            return _finish_response(
                agent,
                trace,
                "",
                None,
                transcript=transcript,
                sttModel=getattr(agent.provider, "stt_model", "unknown"),
                ignored=True,
                ignoreReason="probable_playback_echo",
                response_sources=[],
            )
        reply, action = agent.respond(transcript, trace=trace)
        tts = _browser_tts_payload(agent, trace, reply)
    return _finish_response(
        agent,
        trace,
        reply,
        action,
        transcript=transcript,
        sttModel=getattr(agent.provider, "stt_model", "unknown"),
        **tts,
    )


def _is_probable_playback_echo(transcript: str) -> bool:
    normalized = " ".join(
        transcript.lower().replace("'", "").replace(".", "").replace(",", "").split()
    )
    return normalized in {
        "all right",
        "alright",
        "thanks",
        "thank you",
        "youre welcome",
        "your welcome",
    }


def _token(identity: str, name: str, room: str) -> str:
    if _livekit_api_secret() == "secret":
        warnings.filterwarnings("ignore", category=jwt.InsecureKeyLengthWarning)
    return (
        api.AccessToken(_livekit_api_key(), _livekit_api_secret())
        .with_identity(identity)
        .with_name(name)
        .with_grants(
            api.VideoGrants(
                room_join=True,
                room=room,
                can_publish=True,
                can_subscribe=True,
            )
        )
        .to_jwt()
    )


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self.path = "/web/index.html"
            return super().do_GET()
        if parsed.path == "/state":
            return self._send_json({
                "livekitRoom": _livekit_room(),
                "livekitUrl": _livekit_url(),
                "agentProvider": _agent_provider_name(),
                "languages": ["en", "es"],
            })
        if parsed.path != "/token":
            return super().do_GET()

        query = parse_qs(parsed.query)
        identity = query.get("identity", ["caller-demo"])[0]
        name = query.get("name", [identity])[0]
        room = query.get("room", [_livekit_room()])[0]

        payload = {
            "url": _livekit_url(),
            "room": room,
            "identity": identity,
            "token": _token(identity, name, room),
        }
        self._send_json(payload)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        session_id = self.headers.get("X-Session-ID", "browser-demo")
        turn_id = self.headers.get("X-Turn-ID")
        if parsed.path == "/reset":
            _reset_session(session_id)
            return self._send_json({"reset": True, "sessionId": session_id})
        if parsed.path == "/greeting":
            try:
                return self._send_json(_greeting_reply(session_id))
            except Exception as exc:
                return self._send_json({"error": str(exc)}, status=500)
        if parsed.path == "/voice-agent":
            return self._handle_voice_agent(session_id, turn_id)
        if parsed.path != "/agent":
            self.send_error(404, "File not found")
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length)
            payload = json.loads(body or b"{}")
            text = str(payload.get("text", "")).strip()
            if not text:
                raise ValueError("Missing text")
            response = _agent_reply(text, session_id, turn_id)
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return
        self._send_json(response)

    def _handle_voice_agent(self, session_id: str, turn_id: str | None) -> None:
        try:
            length = int(self.headers.get("Content-Length", "0"))
            audio = self.rfile.read(length)
            if not audio:
                raise ValueError("Missing audio")
            response = _voice_agent_reply(
                audio,
                self.headers.get("Content-Type", ""),
                session_id,
                turn_id,
                self.headers.get("X-Barge-In", "false").lower() == "true",
            )
        except Exception as exc:
            self._send_json({"error": str(exc)}, status=500)
            return
        self._send_json(response)

    def _send_json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)


def main() -> None:
    _load_env_files()
    os.environ.setdefault(
        "TELEMETRY_JSONL",
        str(ASSIGNMENT_ROOT / "logs" / "voice-events.jsonl"),
    )
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"Open http://{HOST}:{PORT}")
    print(f"LiveKit URL: {_livekit_url()}")
    print(f"Room: {_livekit_room()}")
    print(f"Agent provider: {_agent_provider_name()}")
    print(f"TTS backend: {os.getenv('TTS_BACKEND', 'provider').lower()}")
    print("Use the two panes for LiveKit audio. Use the conversation panel for the hotel agent.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()
