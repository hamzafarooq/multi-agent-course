"""Moment-level RAG over podcast episodes — Module 3 demo.

Ask a complex question and get a streamed, cited answer. Each citation deep-links
into the source YouTube episode at the exact moment, with a synced transcript.

Pipeline (see src/selfbuilt/search.py):
    query -> self-query filters -> decompose into sub-queries
          -> hybrid retrieve in Qdrant (dense + BM25 sparse + HyDE-question vectors, RRF-fused)
          -> cross-encoder re-rank -> streamed, cited synthesis

Run:
    uvicorn app:app --reload --port 8000
    # then open http://localhost:8000
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import yaml
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from openai import OpenAI

from src.config import LLM_MODEL, SYNTH_MODEL
from src.selfbuilt.search import SelfBuiltEngine

ROOT = Path(__file__).resolve().parent
VIDEOS = {v["id"]: v for v in yaml.safe_load((ROOT / "videos.yaml").read_text())["videos"]}

app = FastAPI(title="Moment RAG")
_engine: SelfBuiltEngine | None = None


def get_engine() -> SelfBuiltEngine:
    global _engine
    if _engine is None:
        _engine = SelfBuiltEngine()
    return _engine


def youtube_id(url: str) -> str:
    m = re.search(r"(?:youtu\.be/|v=)([\w-]{11})", url or "")
    return m.group(1) if m else ""


# --- citations -----------------------------------------------------------------

def _citations_from_hits(hits: list[dict], max_moments: int = 10) -> list[dict]:
    """Flatten video hits into ranked, numbered citation moments."""
    flat = []
    for hit in hits:
        v = VIDEOS.get(hit["video_id"], {})
        for m in hit["moments"]:
            flat.append({
                "video_id": hit["video_id"],
                "title": v.get("title", hit["video_id"]),
                "guest": v.get("guest", ""),
                "youtube_id": youtube_id(v.get("url", "")),
                "start_ms": m["start_ms"],
                "end_ms": m["end_ms"],
                "text": m["text"],
                "score": m["score"],
            })
    flat.sort(key=lambda x: x["score"], reverse=True)
    cites = flat[:max_moments]
    for i, c in enumerate(cites, 1):
        c["n"] = i
    return cites


# --- streamed, cited synthesis -------------------------------------------------

EDITORIAL_PROMPT = """You are a sharp, opinionated editor writing an in-depth explainer that genuinely teaches the reader, using ONLY the numbered transcript snippets below from a podcast (product, growth, AI, leadership).

Write GitHub-flavored markdown in this order:
1. `## ` a specific, non-generic headline that states the actual takeaway (never the question restated).
2. One italicized *standfirst* sentence that frames the real tension or stakes.
3. `**Key takeaways**` then 3-4 `- ` bullets — each a concrete claim with substance, not a category label.
4. 2-4 `### ` sections. In each: explain the WHY and the MECHANISM, name the specific guest/company, and use the actual example, number, framework, or vivid phrasing they gave. Where guests differ, say so explicitly. Quote a short striking phrase when it earns its place.
5. If the question compares options/people, include a markdown comparison table with real, differentiated cells (never "varies"/"depends").
6. `**Bottom line:**` one sharp, earned closing sentence.

Hard rules — this must NOT read like generic AI filler:
- Be specific and concrete. Prefer the guest's real example/number/story over abstract paraphrase.
- No platitudes, no hedging, no filler transitions, no restating the question.
- Attribute every claim to the specific guest/company and cite inline with [n] (e.g. [1] or [2,3]).
- Every section must add NEW information; never repeat a takeaway in different words.
- Output raw markdown directly. Do NOT wrap the whole answer in a ``` code fence.

Question: {query}

Snippets:
{snippets}

Write the markdown answer now."""


def _format_snippets(citations: list[dict]) -> str:
    return "\n\n".join(
        f"[{c['n']}] ({c['title']}, {c['start_ms']//1000//60:02d}:{(c['start_ms']//1000)%60:02d}) {c['text']}"
        for c in citations
    )


def stream_editorial(query: str, citations: list[dict]):
    """Yield markdown deltas. Uses SYNTH_MODEL; falls back to LLM_MODEL only if it never produced text."""
    client = OpenAI()
    messages = [{"role": "user", "content": EDITORIAL_PROMPT.format(
        query=query, snippets=_format_snippets(citations))}]
    for model in (SYNTH_MODEL, LLM_MODEL):
        produced = False
        try:
            stream = client.chat.completions.create(
                model=model, messages=messages, temperature=0.45, stream=True)
            for chunk in stream:
                delta = chunk.choices[0].delta.content if chunk.choices else None
                if delta:
                    produced = True
                    yield delta
            return
        except Exception:
            if produced:
                raise
            continue


def _sse(stage: str, status: str, ms: float | None = None, detail: dict | None = None) -> str:
    payload: dict = {"stage": stage, "status": status}
    if ms is not None:
        payload["ms"] = round(ms, 1)
    if detail is not None:
        payload["detail"] = detail
    return f"data: {json.dumps(payload)}\n\n"


@app.get("/ask_stream")
def ask_stream(q: str):
    """SSE: run the pipeline with a light progress trace, send citations, then stream the answer."""
    eng = get_engine()

    def gen():
        try:
            yield _sse("self_query", "running")
            t = time.perf_counter()
            filters, qfilter = eng.stage_self_query(q)
            yield _sse("self_query", "done", (time.perf_counter() - t) * 1000, {"filters": filters})

            yield _sse("decompose", "running")
            t = time.perf_counter()
            subs = eng.stage_decompose(q)
            yield _sse("decompose", "done", (time.perf_counter() - t) * 1000, {"sub_queries": subs})

            yield _sse("retrieve", "running")
            t = time.perf_counter()
            qvecs = eng.stage_embed(subs)
            fused, fell_back = eng.stage_retrieve(qvecs, subs, qfilter)
            yield _sse("retrieve", "done", (time.perf_counter() - t) * 1000,
                       {"total": len(fused), "fallback": fell_back})

            yield _sse("rerank", "running")
            t = time.perf_counter()
            reranked = eng.stage_rerank(q, fused)
            yield _sse("rerank", "done", (time.perf_counter() - t) * 1000)

            hits = eng.rollup(reranked, 10)
            citations = _citations_from_hits(hits, max_moments=10)
            yield _sse("citations", "done", None, {"citations": citations, "sub_queries": subs})
            if citations:
                yield _sse("answer", "running")
                for delta in stream_editorial(q, citations):
                    yield f"data: {json.dumps({'stage': 'delta', 'text': delta})}\n\n"
                yield _sse("answer", "done")
            else:
                yield f"data: {json.dumps({'stage': 'delta', 'text': 'No relevant moments found.'})}\n\n"
            yield _sse("end", "done")
        except Exception as e:
            yield _sse("error", "done", None, {"message": str(e)})

    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.get("/transcript/{video_id}")
def transcript(video_id: str):
    src = ROOT / "data" / "transcripts" / f"{video_id}.json"
    if not src.exists():
        raise HTTPException(status_code=404, detail="No transcript for this video")
    cues = json.loads(src.read_text()).get("cues", [])
    v = VIDEOS.get(video_id, {})
    return {"video_id": video_id, "title": v.get("title", video_id),
            "guest": v.get("guest", ""), "cues": cues}


@app.get("/videos")
def videos():
    return {vid: {"title": v.get("title", vid), "guest": v.get("guest", ""),
                  "youtube_id": youtube_id(v.get("url", ""))} for vid, v in VIDEOS.items()}


@app.get("/", response_class=HTMLResponse)
def index():
    return (ROOT / "studio_ui.html").read_text()
