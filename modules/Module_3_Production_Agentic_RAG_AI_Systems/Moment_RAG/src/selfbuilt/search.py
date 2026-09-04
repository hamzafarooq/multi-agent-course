"""Self-built pipeline:
  0. Self-query: infer metadata filters (e.g. specialty) from the query.
  1. Decompose user query into 2-4 sub-queries (query breakdown).
  2. Embed the sub-queries and hybrid-retrieve in Qdrant: dense + BM25 sparse +
     hypothetical-question (multivector) branches, RRF-fused server-side.
  3. Cross-encoder rerank the top-N fused chunks against the original query.
  4. Roll up chunk hits to video-level with score_mode=max (per spec).

HyDE lives only at ingestion (the per-chunk hypothetical_questions indexed in
the `questions` branch) — there is no query-time hypothetical-answer generation.
This intentionally moves "intelligence" to the query side, vs. Lucene-RRF which
relies on a richer index.
"""
from __future__ import annotations

import time

from ..config import (
    ENABLE_QUESTION_INDEX,
    ENABLE_SELF_QUERY,
    KNN_INNER_HITS_SIZE,
    KNN_K,
    RERANKER_ENABLED,
    SELF_QUERY_MIN_RESULTS,
)
from ..embed import build_chunk_embeddings, build_question_embeddings, embed_texts
from ..videos import load_videos
from .qdrant_store import QdrantHybridStore
from .query_breakdown import decompose
from .rerank import Reranker
from .self_query import analyze as self_query_analyze, build_filter


class SelfBuiltEngine:
    def __init__(self):
        vecs, chunks = build_chunk_embeddings()
        self.chunks = chunks
        self.video_labels = {v["id"]: v.get("content_labels", []) for v in load_videos()}
        question_vecs = build_question_embeddings(chunks) if ENABLE_QUESTION_INDEX else {}
        self.store = QdrantHybridStore(vecs, chunks, question_vecs=question_vecs)
        self.reranker = Reranker()

    # -- pipeline stages (each independently callable for the demo trace) -----

    def stage_self_query(self, query: str, enabled: bool | None = None):
        """Return (filters, qdrant_filter). filters={} when disabled/none implied."""
        enabled = ENABLE_SELF_QUERY if enabled is None else enabled
        if not enabled:
            return {}, None
        sq = self_query_analyze(query)
        return sq["filters"], build_filter(sq["filters"])

    def stage_decompose(self, query: str, use_breakdown: bool = True) -> list[str]:
        return decompose(query) if use_breakdown else [query]

    def stage_embed(self, sub_queries: list[str]):
        return embed_texts(sub_queries)

    def stage_retrieve(self, qvecs, sub_queries, query_filter):
        """Hybrid retrieve with the self-query filter; soft-fallback if it
        over-restricts. Returns (fused, fell_back)."""
        fused = self.store.query(qvecs, sub_queries, k=KNN_K * 2, query_filter=query_filter)
        fell_back = False
        if query_filter is not None and len(fused) < SELF_QUERY_MIN_RESULTS:
            fused = self.store.query(qvecs, sub_queries, k=KNN_K * 2, query_filter=None)
            fell_back = True
        return fused, fell_back

    def stage_rerank(self, query: str, fused, enabled: bool | None = None):
        enabled = RERANKER_ENABLED if enabled is None else enabled
        if not enabled:
            return fused
        items = [(idx, self.chunks[idx]["text"]) for idx, _ in fused]
        return self.reranker.rerank(query, items)

    def rollup(self, fused, size: int = 10) -> list[dict]:
        """Chunk hits -> video-level hits with score_mode=max + top moments."""
        by_video: dict[str, dict] = {}
        for idx, score in fused:
            chunk = self.chunks[idx]
            vid = chunk["video_id"]
            entry = by_video.setdefault(vid, {"video_id": vid, "score": 0.0, "moments": []})
            entry["score"] = max(entry["score"], float(score))
            entry["moments"].append({
                "text": chunk["text"],
                "start_ms": chunk["start_ms"],
                "end_ms": chunk["end_ms"],
                "score": float(score),
            })
        hits = sorted(by_video.values(), key=lambda x: x["score"], reverse=True)[:size]
        for h in hits:
            h["moments"].sort(key=lambda m: m["score"], reverse=True)
            h["moments"] = h["moments"][:KNN_INNER_HITS_SIZE]
        return hits

    def candidate_trace(self, fused, limit: int = 8) -> list[dict]:
        """Inspectable view of fused/reranked chunks for the demo UI — score plus
        the ingestion artifacts (keywords, gist, section_type, acronyms, questions)."""
        out = []
        for idx, score in fused[:limit]:
            c = self.chunks[idx]
            out.append({
                "chunk_id": c["chunk_id"],
                "video_id": c["video_id"],
                "score": round(float(score), 4),
                "start_ms": c["start_ms"],
                "end_ms": c["end_ms"],
                "content_labels": self.video_labels.get(c["video_id"], []),
                "text": c["text"][:240],
                "keywords": c.get("keywords", []),
                "gist": c.get("gist", ""),
                "section_type": c.get("section_type"),
                "acronyms_expanded": c.get("acronyms_expanded", {}),
                "hypothetical_questions": c.get("hypothetical_questions", []),
            })
        return out

    def search(
        self,
        query: str,
        size: int = 10,
        use_breakdown: bool = True,
        use_rerank: bool | None = None,
        use_self_query: bool | None = None,
    ) -> dict:
        timings: dict[str, float] = {}

        t0 = time.perf_counter()
        filters, query_filter = self.stage_self_query(query, use_self_query)
        timings["self_query"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sub_queries = self.stage_decompose(query, use_breakdown)
        timings["breakdown"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        qvecs = self.stage_embed(sub_queries)
        timings["embed"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        fused, fell_back = self.stage_retrieve(qvecs, sub_queries, query_filter)
        timings["retrieve"] = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        fused = self.stage_rerank(query, fused, use_rerank)
        timings["rerank"] = (time.perf_counter() - t0) * 1000

        hits = self.rollup(fused, size)
        timings["total"] = sum(timings.values())
        return {
            "hits": hits,
            "sub_queries": sub_queries,
            "filters": {**filters, "_fallback": True} if fell_back else filters,
            "timings_ms": {k: round(v, 1) for k, v in timings.items()},
        }
