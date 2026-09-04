"""Semantic chunking for word-timestamped transcripts.

The whisper word stream carries no punctuation, so we cannot split on sentences.
Instead we form small fixed word-window "units" (each a slice of the word list,
so it keeps start_ms/end_ms), embed them with a local model, and place a chunk
boundary wherever the cosine distance between consecutive units spikes above a
percentile threshold — i.e. where the topic shifts. Units between boundaries are
merged into chunks bounded by a max (CHUNK_TOKENS) and min (SEMANTIC_MIN_TOKENS)
token budget. Output schema matches the fixed-window chunker exactly.
"""
from __future__ import annotations

import numpy as np
import tiktoken

from ..config import (
    CHUNK_TOKENS,
    SEMANTIC_BREAKPOINT_PERCENTILE,
    SEMANTIC_BUFFER,
    SEMANTIC_EMBED_MODEL,
    SEMANTIC_MIN_TOKENS,
    SEMANTIC_UNIT_WORDS,
)

ENC = tiktoken.get_encoding("cl100k_base")
_embedder = None


def _embed(texts: list[str]) -> np.ndarray:
    """Local dense embeddings for boundary detection (free/offline)."""
    global _embedder
    if _embedder is None:
        from fastembed import TextEmbedding
        _embedder = TextEmbedding(SEMANTIC_EMBED_MODEL)
    return np.asarray(list(_embedder.embed(texts)), dtype=np.float32)


def _unit_text(words: list[dict], a: int, b: int) -> str:
    return " ".join(w["word"] for w in words[a:b]).strip()


def semantic_chunks(video_id: str, words: list[dict], embed_fn=None) -> list[dict]:
    """Chunk a word list at semantic boundaries. `embed_fn` is injectable for
    testing; defaults to a local fastembed model."""
    if not words:
        return []
    embed_fn = embed_fn or _embed

    # 1. Atomic units: fixed word-windows (no punctuation to split sentences on).
    spans = [(i, min(i + SEMANTIC_UNIT_WORDS, len(words)))
             for i in range(0, len(words), SEMANTIC_UNIT_WORDS)]
    texts = [_unit_text(words, a, b) for a, b in spans]
    unit_tokens = [len(ENC.encode(t)) for t in texts]

    # 2. Embed each unit with a buffer of neighbours for context, then measure
    #    cosine distance between consecutive units.
    buf = SEMANTIC_BUFFER
    buffered = [" ".join(texts[max(0, i - buf):i + buf + 1]) for i in range(len(texts))]
    embs = embed_fn(buffered)
    norm = embs / (np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9)
    dists = 1.0 - np.sum(norm[:-1] * norm[1:], axis=1) if len(norm) > 1 else np.array([])

    # 3. A breakpoint after unit i means "cut here"; threshold is data-relative.
    cut_after: set[int] = set()
    if dists.size:
        thr = np.percentile(dists, SEMANTIC_BREAKPOINT_PERCENTILE)
        cut_after = {int(i) for i in np.where(dists > thr)[0]}

    # 4. Merge units into chunks: cut at breakpoints (once past the min-token
    #    floor) and force-cut before exceeding the max-token budget.
    segments: list[tuple[int, int]] = []  # [start_unit, end_unit)
    seg_start = 0
    cur_tokens = 0
    n = len(spans)
    for i in range(n):
        if cur_tokens > 0 and cur_tokens + unit_tokens[i] > CHUNK_TOKENS:
            segments.append((seg_start, i))
            seg_start, cur_tokens = i, 0
        cur_tokens += unit_tokens[i]
        last = i == n - 1
        if not last and i in cut_after and cur_tokens >= SEMANTIC_MIN_TOKENS:
            segments.append((seg_start, i + 1))
            seg_start, cur_tokens = i + 1, 0
    if seg_start < n:
        segments.append((seg_start, n))

    # 5. Emit chunk dicts — identical schema to the fixed-window chunker.
    out: list[dict] = []
    for su, eu in segments:
        a, b = spans[su][0], spans[eu - 1][1]
        text = _unit_text(words, a, b)
        if not text:
            continue
        out.append({
            "chunk_id": f"{video_id}_c{len(out):04d}",
            "video_id": video_id,
            "text": text,
            "start_ms": words[a]["start_ms"],
            "end_ms": words[b - 1]["end_ms"],
            "n_tokens": len(ENC.encode(text)),
        })
    return out
