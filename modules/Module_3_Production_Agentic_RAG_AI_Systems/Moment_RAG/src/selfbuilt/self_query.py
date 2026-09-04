"""Self-query: infer metadata filters from a natural-language query.

Given the filterable schema (content_labels and section_type, with their allowed
values), an LLM decides which hard filters the query implies and restates the
core semantic query. The filters become a Qdrant Filter applied to every
retrieval branch. The headline win is cross-specialty disambiguation — e.g.
"minimally invasive aortic valve replacement" pins content_labels to
cardiothoracic so an orthopaedic "minimally invasive" video can't win on lexical
overlap. Hallucinated filter values are dropped; an over-restrictive filter is
recovered by the caller's soft fallback.
"""
from __future__ import annotations

import json

from openai import OpenAI
from qdrant_client import models

from ..config import LLM_MODEL, SECTION_TYPES
from ..videos import load_videos

PROMPT = '''You route a podcast-interview search query (Lenny's Podcast — product, growth, AI, leadership). Using the metadata schema, decide which HARD filters (if any) the query clearly implies, and restate the core semantic query.

Return STRICT JSON: {{"semantic_query": "...", "filters": {{"content_labels": [...], "section_type": [...]}}}}.

Rules:
- Only include a filter value when the query clearly implies it; otherwise use an empty list. When unsure, prefer empty (no filter).
- "content_labels" values MUST come from: {labels}
- "section_type" values MUST come from: {sections}

Query: {query}
'''


def content_label_vocab() -> list[str]:
    return sorted({lbl for v in load_videos() for lbl in v.get("content_labels", [])})


def analyze(query: str) -> dict:
    """Return {"semantic_query": str, "filters": {content_labels, section_type}}."""
    labels = content_label_vocab()
    client = OpenAI()
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(labels=labels, sections=SECTION_TYPES, query=query)}],
        response_format={"type": "json_object"},
        temperature=0.0,
    )
    data = json.loads(resp.choices[0].message.content)
    f = data.get("filters") or {}
    # Validate against the vocab — drop anything the model invented.
    filters = {
        "content_labels": [x for x in (f.get("content_labels") or []) if x in labels],
        "section_type": [x for x in (f.get("section_type") or []) if x in SECTION_TYPES],
    }
    return {"semantic_query": (data.get("semantic_query") or query).strip(), "filters": filters}


def build_filter(filters: dict) -> models.Filter | None:
    """Translate validated filters into a Qdrant Filter (None if no filters)."""
    must = []
    if filters.get("content_labels"):
        must.append(models.FieldCondition(
            key="content_labels", match=models.MatchAny(any=filters["content_labels"])))
    if filters.get("section_type"):
        must.append(models.FieldCondition(
            key="section_type", match=models.MatchAny(any=filters["section_type"])))
    return models.Filter(must=must) if must else None
