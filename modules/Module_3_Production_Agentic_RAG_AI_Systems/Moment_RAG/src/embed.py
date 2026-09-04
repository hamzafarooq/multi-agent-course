"""Batch-embed chunk texts via OpenAI text-embedding-3-large @ dim=1024.

Matches the spec verbatim. Embeddings are cached on disk so reruns are cheap.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from openai import OpenAI
from tqdm import tqdm

from .config import EMBED_DIM, EMBED_DIR, EMBED_MODEL
from .ingest.chunk import all_chunks

CACHE = EMBED_DIR / "chunks.npz"
INDEX_JSON = EMBED_DIR / "chunks_index.json"
Q_CACHE = EMBED_DIR / "questions.npz"
BATCH = 64


def embed_texts(texts: list[str], model: str = EMBED_MODEL, dim: int = EMBED_DIM) -> np.ndarray:
    client = OpenAI()
    vecs: list[list[float]] = []
    for i in tqdm(range(0, len(texts), BATCH), desc="embed"):
        batch = texts[i:i + BATCH]
        resp = client.embeddings.create(model=model, input=batch, dimensions=dim)
        vecs.extend([d.embedding for d in resp.data])
    return np.array(vecs, dtype=np.float32)


def build_chunk_embeddings(force: bool = False) -> tuple[np.ndarray, list[dict]]:
    if CACHE.exists() and INDEX_JSON.exists() and not force:
        data = np.load(CACHE)
        index = json.loads(INDEX_JSON.read_text())
        print(f"[embed] cache hit ({len(index)} chunks)")
        return data["vecs"], index
    chunks = all_chunks()
    print(f"[embed] computing {len(chunks)} chunk embeddings")
    vecs = embed_texts([c["text"] for c in chunks])
    np.savez_compressed(CACHE, vecs=vecs)
    INDEX_JSON.write_text(json.dumps(chunks))
    return vecs, chunks


def embed_query(query: str) -> np.ndarray:
    return embed_texts([query])[0]


def _group(vecs: np.ndarray, owners: np.ndarray) -> dict[int, np.ndarray]:
    """Group flat question vectors back into per-chunk matrices keyed by chunk idx."""
    out: dict[int, list] = {}
    for v, o in zip(vecs, owners):
        out.setdefault(int(o), []).append(v)
    return {k: np.array(v, dtype=np.float32) for k, v in out.items()}


def build_question_embeddings(chunks: list[dict], force: bool = False) -> dict[int, np.ndarray]:
    """Embed every chunk's `hypothetical_questions` (post-enrichment) and cache.

    Returns {chunk_idx: matrix[n_questions, dim]} for chunks that have questions;
    {} when none are present (chunks not yet enriched). Cached to questions.npz —
    delete it (like chunks.npz) when chunks change.
    """
    if Q_CACHE.exists() and not force:
        d = np.load(Q_CACHE)
        print(f"[embed] question cache hit ({len(d['vecs'])} questions)")
        return _group(d["vecs"], d["owners"])
    flat_texts: list[str] = []
    owners: list[int] = []
    for i, c in enumerate(chunks):
        for q in c.get("hypothetical_questions") or []:
            flat_texts.append(q)
            owners.append(i)
    if not flat_texts:
        print("[embed] no hypothetical_questions found; skipping question vectors")
        return {}
    print(f"[embed] embedding {len(flat_texts)} hypothetical questions")
    vecs = embed_texts(flat_texts)
    owners_arr = np.array(owners, dtype=np.int32)
    np.savez_compressed(Q_CACHE, vecs=vecs, owners=owners_arr)
    return _group(vecs, owners_arr)


if __name__ == "__main__":
    build_chunk_embeddings()
