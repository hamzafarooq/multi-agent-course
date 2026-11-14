"""Structured, vendor-neutral telemetry for Aurora voice turns."""

from __future__ import annotations

import json
import os
import threading
import time
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator


_SENSITIVE_KEYS = {
    "contact", "email", "guest_name", "name", "phone", "phone_number",
}
_CONTENT_KEYS = {"message", "query", "result", "text", "transcript"}


def _sanitize(value, key: str = ""):
    normalized_key = key.lower()
    if normalized_key in _SENSITIVE_KEYS:
        return "[REDACTED]"
    if normalized_key in _CONTENT_KEYS and os.getenv("TELEMETRY_INCLUDE_CONTENT", "false").lower() != "true":
        return f"[OMITTED:{len(str(value))}]"
    if isinstance(value, dict):
        return {nested_key: _sanitize(nested_value, nested_key) for nested_key, nested_value in value.items()}
    if isinstance(value, (list, tuple)):
        return [_sanitize(item) for item in value]
    return value


class TurnTrace:
    """Collect ordered events and stage timings for one conversation turn."""

    def __init__(self, session_id: str | None = None, turn_id: str | None = None):
        self.session_id = session_id or f"session-{uuid.uuid4().hex[:12]}"
        self.turn_id = turn_id or f"turn-{uuid.uuid4().hex[:12]}"
        self.trace_id = uuid.uuid4().hex
        self.started_at = time.time()
        self._started_perf = time.perf_counter()
        self.events: list[dict] = []
        self.timings: dict[str, float] = {}
        self.attributes: dict = {}
        self._finished = False

    def event(self, name: str, **attributes) -> None:
        self.events.append({
            "name": name,
            "offsetMs": round((time.perf_counter() - self._started_perf) * 1000, 1),
            "attributes": _sanitize(attributes),
        })

    @contextmanager
    def span(self, name: str, **attributes) -> Iterator[None]:
        started = time.perf_counter()
        self.event(f"{name}.started", **attributes)
        try:
            yield
        except Exception as exc:
            self.event(f"{name}.failed", error=type(exc).__name__, message=str(exc))
            raise
        finally:
            duration = (time.perf_counter() - started) * 1000
            self.timings[name] = round(self.timings.get(name, 0.0) + duration, 1)
            self.event(f"{name}.completed", durationMs=round(duration, 1))

    def set_timing(self, name: str, duration_ms: float) -> None:
        self.timings[name] = round(duration_ms, 1)

    def finish(self, **attributes) -> dict:
        if attributes:
            self.attributes.update(attributes)
        if not self._finished:
            self._finished = True
            self.event("turn.completed")
        return self.to_dict()

    def to_dict(self) -> dict:
        total_ms = (time.perf_counter() - self._started_perf) * 1000
        return {
            "schemaVersion": "1.0",
            "traceId": self.trace_id,
            "sessionId": self.session_id,
            "turnId": self.turn_id,
            "startedAt": self.started_at,
            "totalMs": round(total_ms, 1),
            "timings": self.timings,
            "attributes": self.attributes,
            "events": self.events,
        }


_write_lock = threading.Lock()


def write_trace(trace: TurnTrace | dict) -> None:
    """Append a trace as JSONL when TELEMETRY_JSONL is configured."""
    destination = os.getenv("TELEMETRY_JSONL", "").strip()
    if not destination:
        return
    payload = trace.to_dict() if isinstance(trace, TurnTrace) else trace
    path = Path(destination).expanduser()
    path.parent.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(payload, ensure_ascii=True) + "\n")


def format_trace(trace: TurnTrace | dict) -> str:
    payload = trace.to_dict() if isinstance(trace, TurnTrace) else trace
    timings = payload.get("timings", {})
    lines = ["  turn telemetry"]
    for stage in ("capture", "stt", "routing", "retrieval", "llm", "tools", "tts"):
        if stage in timings:
            lines.append(f"    {stage:<12} {timings[stage]:7.0f} ms")
    lines.append(f"    {'TOTAL':<12} {payload.get('totalMs', 0):7.0f} ms")
    language = payload.get("attributes", {}).get("language")
    if language:
        lines.append(f"    {'language':<12} {language}")
    return "\n".join(lines)
