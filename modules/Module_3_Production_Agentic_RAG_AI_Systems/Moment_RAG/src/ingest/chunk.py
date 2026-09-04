"""Chunk word-level transcripts into ~256-token windows with 25% stride.

Matches the spec: token windows of ~256 tokens, ~25% stride, timestamps preserved
from the underlying word list.
"""
from __future__ import annotations

import json
from pathlib import Path

import tiktoken

from ..config import CHUNK_DIR, CHUNK_STRIDE, CHUNK_TOKENS, SEMANTIC_CHUNKING, TRANSCRIPT_DIR
from ..videos import load_videos
from .semantic import semantic_chunks

ENC = tiktoken.get_encoding("cl100k_base")


def chunk_path(video_id: str) -> Path:
    return CHUNK_DIR / f"{video_id}.json"


def _word_token_counts(words: list[dict]) -> list[int]:
    """Token count per word."""
    return [len(ENC.encode(w["word"])) for w in words]


def chunk_one(video_id: str, force: bool = False) -> Path:
    out = chunk_path(video_id)
    if out.exists() and not force:
        print(f"[skip] {video_id} already chunked -> {out}")
        return out

    src = TRANSCRIPT_DIR / f"{video_id}.json"
    data = json.loads(src.read_text())
    words = data["words"]

    if SEMANTIC_CHUNKING:
        chunks = semantic_chunks(video_id, words)
        out.write_text(json.dumps(chunks))
        print(f"[chunk] {video_id} -> {len(chunks)} chunks (semantic)")
        return out

    return _window_chunks(video_id, words, out)


def _window_chunks(video_id: str, words: list[dict], out: Path) -> Path:
    """Legacy fixed-window chunker (256 tokens, 25% stride) — fallback path."""
    counts = _word_token_counts(words)
    chunks: list[dict] = []
    stride_tokens = int(CHUNK_TOKENS * CHUNK_STRIDE)
    if stride_tokens <= 0:
        stride_tokens = 1

    i = 0
    while i < len(words):
        tokens_so_far = 0
        j = i
        while j < len(words) and tokens_so_far + counts[j] <= CHUNK_TOKENS:
            tokens_so_far += counts[j]
            j += 1
        if j == i:  # safety: single oversized word
            j = i + 1
        chunk_words = words[i:j]
        text = " ".join(w["word"] for w in chunk_words).strip()
        if text:
            chunks.append({
                "chunk_id": f"{video_id}_c{len(chunks):04d}",
                "video_id": video_id,
                "text": text,
                "start_ms": chunk_words[0]["start_ms"],
                "end_ms": chunk_words[-1]["end_ms"],
                "n_tokens": tokens_so_far,
            })
        if j >= len(words):
            break
        # Advance by (window - stride) so the next window overlaps by `stride_tokens`.
        advance = max(1, j - i - stride_tokens)
        i += advance

    out.write_text(json.dumps(chunks))
    print(f"[chunk] {video_id} -> {len(chunks)} chunks")
    return out


def load_chunks(video_id: str) -> list[dict]:
    return json.loads(chunk_path(video_id).read_text())


def all_chunks() -> list[dict]:
    out = []
    for v in load_videos():
        out.extend(load_chunks(v["id"]))
    return out


def main():
    for v in load_videos():
        chunk_one(v["id"])


if __name__ == "__main__":
    main()
