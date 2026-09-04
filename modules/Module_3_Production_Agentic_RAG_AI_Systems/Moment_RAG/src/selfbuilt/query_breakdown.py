"""Decompose a user query into 2-4 sub-queries that hit different facets.

For a query like "how do OpenAI and Figma differ on the AI-era moat" we want:
  - the original query verbatim
  - "OpenAI strategy moat AI era"        (one entity facet)
  - "Figma design craft quality moat"    (other entity facet)
  - "what is a durable moat in AI"        (concept facet)
This widens the lexical net and gives the vector path more chances at relevant chunks.
"""
from __future__ import annotations

import json

from openai import OpenAI

from ..config import LLM_MODEL

PROMPT = '''You are helping a podcast search engine over Lenny's Podcast (product, growth, AI, leadership). Decompose the user's query into 2-4 short sub-queries that capture different facets a product/growth/AI professional would want results for.

Rules:
- Stay strictly within the topic and entities of the query — do NOT introduce unrelated domains (e.g. never add "medical"/"healthcare" unless the query is about them). For a comparison, give each compared person/approach its own facet.
- Keep names, companies, products, and acronyms; expand an acronym once if helpful (e.g. "AEO (answer engine optimization)").
- Each sub-query is a search query, not a sentence.
- Include the original query verbatim as one of the sub-queries.
- Return strict JSON: {{"sub_queries": ["...", "..."]}}.

User query: {query}
'''


def decompose(query: str) -> list[str]:
    client = OpenAI()
    resp = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[{"role": "user", "content": PROMPT.format(query=query)}],
        response_format={"type": "json_object"},
        temperature=0.2,
    )
    data = json.loads(resp.choices[0].message.content)
    subs = data.get("sub_queries", [])
    if query not in subs:
        subs = [query] + subs
    return subs[:4]
