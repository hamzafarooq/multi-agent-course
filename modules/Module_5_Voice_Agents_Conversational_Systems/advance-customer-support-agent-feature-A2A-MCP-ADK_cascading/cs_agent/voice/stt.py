"""STT stage of the voice cascade — Gemini audio-in, one call per finished utterance.

The browser sends raw 16-bit PCM at 16 kHz; Gemini's generate_content wants a real
container, so we wrap it in an in-memory WAV header before sending.
"""

import io
import os
import re
import wave
from functools import lru_cache

from google import genai
from google.genai import types

from telemetry import get_tracer, ATTR

STT_MODEL = os.getenv("VOICE_STT_MODEL", "gemini-3.1-flash-lite")

_TRANSCRIBE_PROMPT = (
    "You are a speech-to-text engine. Transcribe ONLY the words the speaker says. "
    "Rules: output plain text of the spoken words and nothing else. Do NOT add "
    "timestamps, time codes, WEBVTT/SRT cue markers, speaker labels, brackets, or "
    "any commentary. If the audio contains no clear, intelligible speech, respond "
    "with exactly the token NO_SPEECH and nothing else."
)

# Gemini transcription occasionally leaks subtitle formatting (WEBVTT cues,
# "00:00:01.093 --> 00:00:02.500", bare "00:00:01" lines). Strip it defensively.
_VTT_ARROW = re.compile(r"\d{1,2}:\d{2}(?::\d{2})?[.,:]?\d*\s*-->\s*\d{1,2}:\d{2}(?::\d{2})?[.,:]?\d*")
_TIMECODE = re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?([.,:]\d{1,3})?\b")


def _clean(text: str) -> str:
    text = text.strip()
    if not text or text.upper() == "NO_SPEECH":
        return ""
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if not s or s.upper() == "WEBVTT":
            continue
        s = _VTT_ARROW.sub("", s)
        s = _TIMECODE.sub("", s).strip(" -\t")
        if s:
            lines.append(s)
    out = " ".join(lines).strip()
    # If nothing but punctuation/whitespace survived, treat as no speech.
    return out if re.search(r"[A-Za-z0-9]", out) else ""


@lru_cache(maxsize=1)
def _client() -> genai.Client:
    return genai.Client()


def pcm16_to_wav(pcm: bytes, sample_rate: int = 16000) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(sample_rate)
        w.writeframes(pcm)
    return buf.getvalue()


async def transcribe(pcm: bytes, sample_rate: int = 16000):
    """Raw PCM utterance -> (transcript, usage_metadata).

    transcript is '' if no speech was recognized. usage_metadata is the google-genai
    usage object (audio-in / text-out token counts) so the caller can price the call.
    """
    wav = pcm16_to_wav(pcm, sample_rate)
    # Named span so this shows in telemetry as the STT step (not a generic
    # AsyncGenerateContent). No-op when TELEMETRY is off; the model call nests under it.
    with get_tracer().start_as_current_span("stt") as _sp:
        _sp.set_attribute(ATTR.OPENINFERENCE_SPAN_KIND, "VOICE")
        _sp.set_attribute("voice.stage", "stt")
        _sp.set_attribute("voice.model", STT_MODEL)
        resp = await _client().aio.models.generate_content(
            model=STT_MODEL,
            contents=[types.Content(role="user", parts=[
                types.Part.from_bytes(data=wav, mime_type="audio/wav"),
                types.Part(text=_TRANSCRIBE_PROMPT),
            ])],
        )
    return _clean(resp.text or ""), getattr(resp, "usage_metadata", None)
