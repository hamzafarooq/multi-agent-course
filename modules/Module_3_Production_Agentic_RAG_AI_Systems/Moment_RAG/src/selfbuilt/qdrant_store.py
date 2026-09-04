"""Qdrant hybrid store for the self-built path.

One point per transcript chunk carrying two named vectors — a dense vector
(OpenAI text-embedding-3-large) and a BM25 sparse vector (fastembed) — plus the
chunk payload. Retrieval, lexical matching, rank fusion, and metadata filtering
all happen inside Qdrant, replacing the previous FAISS + rank-bm25 + client-side
RRF stack.

A single query fans out into one dense + one sparse prefetch per (HyDE-vector,
sub-query) pair; Qdrant fuses every branch with Reciprocal Rank Fusion in one
call, so cross-sub-query fusion is server-side too.
"""
from __future__ import annotations

import numpy as np
from fastembed import SparseTextEmbedding
from qdrant_client import QdrantClient, models

from ..config import (
    EMBED_DIM,
    QDRANT_COLLECTION,
    QDRANT_LOCATION,
    SPARSE_MODEL,
)
from ..videos import load_videos

DENSE = "text"
SPARSE = "bm25"
QUESTIONS = "questions"

# Metadata fields carried in the payload (present once chunks are enriched).
_META_FIELDS = ("keywords", "acronyms_expanded", "gist", "section_type", "hypothetical_questions")


def _sparse_doc(c: dict) -> str:
    """Lexical document for BM25: chunk text plus enrichment (keywords, gist,
    hypothetical questions, and acronym expansions) so e.g. a bare-acronym query
    can match a chunk that only spells the term out, and vice versa."""
    parts = [c["text"]]
    if c.get("keywords"):
        parts.append(" ".join(c["keywords"]))
    if c.get("gist"):
        parts.append(c["gist"])
    if c.get("hypothetical_questions"):
        parts.append(" ".join(c["hypothetical_questions"]))
    if c.get("acronyms_expanded"):
        parts.append(" ".join(f"{k} {v}" for k, v in c["acronyms_expanded"].items()))
    return " ".join(parts)


class QdrantHybridStore:
    """Dense + sparse hybrid index over chunks, fused with RRF server-side."""

    def __init__(
        self,
        vecs: np.ndarray,
        chunks: list[dict],
        question_vecs: dict[int, np.ndarray] | None = None,
        location: str = QDRANT_LOCATION,
        collection: str = QDRANT_COLLECTION,
        recreate: bool = True,
    ):
        self.chunks = chunks
        self.collection = collection
        self.question_vecs = question_vecs or {}
        self.has_questions = bool(self.question_vecs)
        self.client = QdrantClient(location=location)
        self._sparse = SparseTextEmbedding(SPARSE_MODEL)
        self._build(vecs, chunks, recreate)

    # -- build -------------------------------------------------------------

    def _build(self, vecs: np.ndarray, chunks: list[dict], recreate: bool):
        exists = self.client.collection_exists(self.collection)
        if exists and recreate:
            self.client.delete_collection(self.collection)
            exists = False
        if exists and not recreate:
            return  # trust a persisted collection
        vectors_config = {DENSE: models.VectorParams(size=EMBED_DIM, distance=models.Distance.COSINE)}
        if self.has_questions:
            # Hypothetical-question vectors per chunk, compared MaxSim: a query
            # matches the chunk's *closest* indexed question (question->question).
            vectors_config[QUESTIONS] = models.VectorParams(
                size=EMBED_DIM, distance=models.Distance.COSINE,
                multivector_config=models.MultiVectorConfig(
                    comparator=models.MultiVectorComparator.MAX_SIM),
            )
        self.client.create_collection(
            self.collection,
            vectors_config=vectors_config,
            sparse_vectors_config={SPARSE: models.SparseVectorParams(modifier=models.Modifier.IDF)},
        )
        # Video-level content labels propagated to each chunk for specialty filtering.
        video_labels = {v["id"]: v.get("content_labels", []) for v in load_videos()}
        sparse_docs = self._sparse.embed([_sparse_doc(c) for c in chunks])
        points = []
        for i, (c, sp) in enumerate(zip(chunks, sparse_docs)):
            vec = {
                DENSE: vecs[i].tolist(),
                SPARSE: models.SparseVector(indices=sp.indices.tolist(), values=sp.values.tolist()),
            }
            if self.has_questions:
                # Local mode can't query a multivector slot that some points lack,
                # so every point gets one — fall back to the chunk's own text vector.
                qm = self.question_vecs.get(i)
                vec[QUESTIONS] = qm.tolist() if qm is not None and len(qm) else [vecs[i].tolist()]
            points.append(models.PointStruct(
                id=i,
                vector=vec,
                payload={
                    "idx": i,
                    "chunk_id": c["chunk_id"],
                    "video_id": c["video_id"],
                    "start_ms": c["start_ms"],
                    "end_ms": c["end_ms"],
                    "text": c["text"],
                    "content_labels": video_labels.get(c["video_id"], []),
                    **{f: c[f] for f in _META_FIELDS if f in c},
                },
            ))
        self.client.upsert(self.collection, points)

    # -- query -------------------------------------------------------------

    def _sparse_query(self, text: str) -> models.SparseVector:
        emb = next(iter(self._sparse.query_embed(text)))
        return models.SparseVector(indices=emb.indices.tolist(), values=emb.values.tolist())

    def query(
        self,
        dense_qvecs,
        text_queries: list[str],
        k: int,
        question_qvecs=None,
        query_filter: models.Filter | None = None,
    ) -> list[tuple[int, float]]:
        """Hybrid multi-branch retrieval fused with RRF.

        Per sub-query: a dense branch (HyDE answer vector vs chunk text), a sparse
        branch (BM25), and — when question indexing is on — a questions branch
        (the *question* embedding vs each chunk's hypothetical questions, MaxSim).
        Qdrant RRF-fuses all branches. `query_filter` applies to every branch
        (used later by the self-query metadata filter). Returns [(chunk_idx, score)].
        """
        if question_qvecs is None:
            question_qvecs = dense_qvecs
        prefetch: list[models.Prefetch] = []
        for dvec, tq, qvec in zip(dense_qvecs, text_queries, question_qvecs):
            dlist = np.asarray(dvec, dtype=np.float32).tolist()
            prefetch.append(models.Prefetch(query=dlist, using=DENSE, limit=k, filter=query_filter))
            prefetch.append(models.Prefetch(
                query=self._sparse_query(tq), using=SPARSE, limit=k, filter=query_filter))
            if self.has_questions:
                # query is a 1xD matrix; MaxSim picks the best-matching stored question
                prefetch.append(models.Prefetch(
                    query=[np.asarray(qvec, dtype=np.float32).tolist()],
                    using=QUESTIONS, limit=k, filter=query_filter))
        res = self.client.query_points(
            self.collection,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            limit=k,
            with_payload=False,
        ).points
        return [(p.id, p.score) for p in res]
