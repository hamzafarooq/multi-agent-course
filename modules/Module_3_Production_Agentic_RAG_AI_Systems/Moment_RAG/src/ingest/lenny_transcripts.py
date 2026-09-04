"""Adapt Lenny's Podcast transcripts (from traversaal-ai/lennyhub-rag) into the
word-level transcript JSON the rest of the pipeline already consumes.

The repo transcripts are clean, diarized, and timestamped — each paragraph is a
line like `Noah Weiss (00:00:00):` followed by the spoken text. We:
  1. fetch the matching `data/<transcript>.txt` (cached to data/lenny_raw/<id>.txt),
  2. parse it into speaker cues {speaker, start_ms, text},
  3. emit data/transcripts/<id>.json shaped exactly like the Whisper output
     ({video_id, text, words:[{word,start_ms,end_ms}]}) by linearly interpolating
     word timings across each cue's span — so chunk.py / semantic.py / the demo
     all work unchanged. Cue starts are exact (precise seek targets); intra-cue
     word timing is approximate (fine for highlighting). A `cues` array is also
     stored for the transcript panel (the chunker ignores extra keys).

No Whisper, no OpenAI cost — this just reshapes existing text.
"""
from __future__ import annotations

import json
import re
import urllib.parse
import urllib.request
from pathlib import Path

from ..config import DATA, TRANSCRIPT_DIR
from ..videos import load_videos

RAW_DIR = DATA / "lenny_raw"
REPO_RAW = "https://raw.githubusercontent.com/traversaal-ai/lennyhub-rag/main/data/{name}.txt"

# A cue header: "Speaker Name (HH:MM:SS):" or "(MM:SS):", optionally with text
# trailing on the same line.
_HEADER = re.compile(r"^(?P<spk>.{1,60}?)\s*\((?P<ts>\d{1,2}:\d{2}(?::\d{2})?)\):\s*(?P<txt>.*)$")

WORDS_PER_SEC_FALLBACK = 2.5  # used to estimate the final cue's end time


def raw_path(video_id: str) -> Path:
    return RAW_DIR / f"{video_id}.txt"


def _ts_to_ms(ts: str) -> int:
    parts = [int(p) for p in ts.split(":")]
    if len(parts) == 2:  # MM:SS
        m, s = parts
        h = 0
    else:  # HH:MM:SS
        h, m, s = parts
    return ((h * 60 + m) * 60 + s) * 1000


def fetch_raw(transcript_name: str, video_id: str, force: bool = False) -> str:
    """Return the raw transcript text, caching the download under data/lenny_raw/."""
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    out = raw_path(video_id)
    if out.exists() and not force:
        return out.read_text()
    url = REPO_RAW.format(name=urllib.parse.quote(transcript_name))
    with urllib.request.urlopen(url, timeout=60) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    out.write_text(text)
    return text


def parse_cues(text: str) -> list[dict]:
    """Parse `Speaker (HH:MM:SS): text` blocks into [{speaker, start_ms, text}]."""
    cues: list[dict] = []
    cur: dict | None = None
    for line in text.splitlines():
        stripped = line.strip()
        m = _HEADER.match(stripped)
        if m:
            if cur and cur["text"].strip():
                cues.append(cur)
            cur = {
                "speaker": m.group("spk").strip(),
                "start_ms": _ts_to_ms(m.group("ts")),
                "text": m.group("txt").strip(),
            }
        elif cur is not None and stripped:
            cur["text"] = (cur["text"] + " " + stripped).strip()
    if cur and cur["text"].strip():
        cues.append(cur)
    # Monotonic guard: drop cues whose timestamp goes backwards (rare formatting noise).
    clean = []
    last = -1
    for c in cues:
        if c["start_ms"] >= last:
            clean.append(c)
            last = c["start_ms"]
    return clean


def _interpolate_words(cues: list[dict]) -> list[dict]:
    """Spread each cue's words evenly across [cue.start_ms, next.start_ms)."""
    words: list[dict] = []
    for i, c in enumerate(cues):
        toks = c["text"].split()
        if not toks:
            continue
        start = c["start_ms"]
        if i + 1 < len(cues):
            end = max(cues[i + 1]["start_ms"], start + 1)
        else:
            end = start + int(len(toks) / WORDS_PER_SEC_FALLBACK * 1000) + 1
        span = end - start
        step = span / len(toks)
        for j, tok in enumerate(toks):
            w_start = int(start + j * step)
            w_end = int(start + (j + 1) * step)
            words.append({"word": tok, "start_ms": w_start, "end_ms": max(w_end, w_start + 1)})
    return words


def adapt_one(video: dict, force: bool = False) -> Path:
    """Build data/transcripts/<id>.json from the repo transcript for one video."""
    vid = video["id"]
    name = video.get("transcript") or video.get("guest") or vid
    out = TRANSCRIPT_DIR / f"{vid}.json"
    if out.exists() and not force:
        print(f"[skip] {vid} transcript already adapted -> {out}")
        return out
    raw = fetch_raw(name, vid, force=force)
    cues = parse_cues(raw)
    if not cues:
        raise ValueError(f"no cues parsed for {vid} ({name!r}) — check transcript format")
    words = _interpolate_words(cues)
    full_text = " ".join(w["word"] for w in words).strip()
    out.write_text(json.dumps({
        "video_id": vid,
        "text": full_text,
        "words": words,
        "cues": [{"speaker": c["speaker"], "start_ms": c["start_ms"],
                  "end_ms": cues[i + 1]["start_ms"] if i + 1 < len(cues) else words[-1]["end_ms"],
                  "text": c["text"]} for i, c in enumerate(cues)],
    }))
    print(f"[lenny] {vid} ({name}) -> {len(cues)} cues, {len(words)} words")
    return out


def main():
    for v in load_videos():
        adapt_one(v)


if __name__ == "__main__":
    main()
