"""Chunk metadata enrichment (ingest-time, LLM, cached).

For each chunk, a single gpt-4o-mini call extracts five fields:
  - hypothetical_questions: questions this chunk answers (question-indexing)
  - keywords: salient medical entities (drugs, procedures, devices, anatomy)
  - acronyms_expanded: {acronym: expansion} found in the chunk
  - gist: one-line summary
  - section_type: lecture-structure label from SECTION_TYPES

Fields are merged back into the chunk JSON so everything downstream (the embed
stage, the Qdrant payload, the self-query filter) picks them up. Idempotent: a
chunk already carrying a `gist` is skipped unless force=True.
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor

from openai import OpenAI

from ..config import LLM_MODEL, SECTION_TYPES
from ..videos import load_videos
from .chunk import chunk_path, load_chunks

MAX_WORKERS = 8  # per-chunk LLM calls are independent — run them concurrently

META_FIELDS = ("hypothetical_questions", "keywords", "acronyms_expanded", "gist", "section_type")

PROMPT = '''You are indexing a chunk of a podcast interview transcript (Lenny's Podcast — product, growth, AI, leadership) for search.
Return STRICT JSON with exactly these keys:
- "hypothetical_questions": array of 2-4 specific questions a product/growth/AI professional could ask that THIS chunk answers.
- "keywords": array of 3-8 salient entities or concepts (people, companies, products, frameworks, metrics, tactics, technologies).
- "acronyms_expanded": object mapping each acronym appearing in the chunk to its expansion (e.g. {{"PMF": "product-market fit"}}); use {{}} if none.
- "gist": one concise sentence summarizing the chunk.
- "section_type": one of {sections}.

Chunk:
{text}
'''


def enrich_chunk(client: OpenAI, chunk: dict) -> dict:
    """Return the five metadata fields for one chunk (one LLM call)."""
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(sections=SECTION_TYPES, text=chunk["text"])}],
        response_format={"type": "json_object"},
        temperature=0.1,
    )
    data = json.loads(resp.choices[0].message.content)
    section = data.get("section_type")
    return {
        "hypothetical_questions": list(data.get("hypothetical_questions") or [])[:4],
        "keywords": list(data.get("keywords") or []),
        "acronyms_expanded": dict(data.get("acronyms_expanded") or {}),
        "gist": (data.get("gist") or "").strip(),
        "section_type": section if section in SECTION_TYPES else "other",
    }


def enrich_one(video_id: str, force: bool = False) -> None:
    chunks = load_chunks(video_id)
    if not force and chunks and all("gist" in c for c in chunks):
        print(f"[skip] {video_id} already enriched")
        return
    client = OpenAI()
    targets = [c for c in chunks if force or "gist" not in c]
    with ThreadPoolExecutor(max_workers=min(MAX_WORKERS, len(targets))) as ex:
        metas = list(ex.map(lambda c: enrich_chunk(client, c), targets))  # order preserved
    for c, meta in zip(targets, metas):
        c.update(meta)
    chunk_path(video_id).write_text(json.dumps(chunks))
    print(f"[meta] {video_id} -> enriched {len(targets)}/{len(chunks)} chunks")


def main():
    for v in load_videos():
        enrich_one(v["id"])


if __name__ == "__main__":
    main()
