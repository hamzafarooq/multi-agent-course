"""TTS stage of the voice cascade — Gemini TTS, masked text in, 24 kHz PCM out."""

import os
import re
from functools import lru_cache

from google import genai
from google.genai import types

from telemetry import get_tracer, ATTR

# Split on sentence boundaries so we can synthesize + stream sentence-by-sentence
# (audio starts after the first sentence instead of the whole reply).
_SENT = re.compile(r".*?[.!?…](?:\s+|$)", re.S)


def split_sentences(text: str, min_len: int = 30) -> list[str]:
    text = (text or "").strip()
    if not text:
        return []
    parts, pos = [], 0
    for m in _SENT.finditer(text):
        parts.append(m.group().strip())
        pos = m.end()
    if pos < len(text):
        parts.append(text[pos:].strip())
    # Merge tiny fragments into the previous chunk so each TTS call is meaningful,
    # but keep the FIRST chunk on its own for the fastest possible first audio.
    out: list[str] = []
    for p in parts:
        if out and len(out[-1]) < min_len:
            out[-1] = (out[-1] + " " + p).strip()
        else:
            out.append(p)
    return [p for p in out if p]

TTS_MODEL = os.getenv("VOICE_TTS_MODEL", "gemini-3.1-flash-tts-preview")
TTS_VOICE = os.getenv("VOICE_TTS_VOICE", "Kore")
TTS_SAMPLE_RATE = 24000  # Gemini TTS returns audio/l16 @ 24 kHz mono


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client()


def _audio_config() -> types.GenerateContentConfig:
    return types.GenerateContentConfig(
        response_modalities=["AUDIO"],
        speech_config=types.SpeechConfig(
            voice_config=types.VoiceConfig(
                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=TTS_VOICE)
            )
        ),
    )


async def synthesize_stream(text: str, usage_out: dict | None = None):
    """Yield 16-bit PCM chunks (24 kHz mono) as the model produces them.

    This is what makes voice feel fast: gemini-*-flash-tts streams audio out
    incrementally, so the first chunk arrives in ~1-2s instead of waiting for the
    whole reply to be synthesized. Yields nothing for empty input.

    If `usage_out` (a dict) is passed, the token usage of this synthesis is ADDED
    into usage_out["in"]/["out"] so the caller can price the call (Gemini reports
    usage on the stream's final event).
    """
    if not text.strip():
        return
    # Named span so this shows in telemetry as the TTS step (not a generic
    # AsyncGenerateContent). No-op when TELEMETRY is off; spans the whole synthesis.
    with get_tracer().start_as_current_span("tts") as _sp:
        _sp.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "VOICE")
        _sp.set_attribute("voice.stage", "tts")
        _sp.set_attribute("voice.model", TTS_MODEL)
        stream = await _client().aio.models.generate_content_stream(
            model=TTS_MODEL, contents=text, config=_audio_config())
        async for ev in stream:
            try:
                data = ev.candidates[0].content.parts[0].inline_data.data
            except (AttributeError, IndexError, TypeError):
                data = None
            if data:
                yield data
            if usage_out is not None:
                um = getattr(ev, "usage_metadata", None)
                if um:   # last event carries the totals; keep the largest seen
                    usage_out["in"] = max(usage_out.get("in", 0),
                                          getattr(um, "prompt_token_count", 0) or 0)
                    usage_out["out"] = max(usage_out.get("out", 0),
                                           getattr(um, "candidates_token_count", 0) or 0)


async def synthesize(text: str) -> bytes:
    """Non-streaming fallback: whole reply -> one PCM blob (b'' for empty)."""
    if not text.strip():
        return b""
    resp = await _client().aio.models.generate_content(
        model=TTS_MODEL, contents=text, config=_audio_config())
    part = resp.candidates[0].content.parts[0]
    return part.inline_data.data or b""
