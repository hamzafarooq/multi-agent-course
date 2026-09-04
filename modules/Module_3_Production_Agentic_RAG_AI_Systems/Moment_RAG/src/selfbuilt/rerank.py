"""Cross-encoder reranker over fused retrieval candidates.

Qdrant's RRF fusion gives a strong but purely rank-based ordering. A cross-encoder
rescores the (query, chunk) pairs jointly, which sharpens *which* chunk — and so
which cited moment — is actually most relevant. It runs only on the top-N fused
candidates, so cost stays bounded.

Backed by fastembed's ONNX cross-encoders (CPU-optimized, same dependency as the
sparse BM25 vectors) rather than torch/sentence-transformers. The model is
configurable via RERANKER_MODEL — a heavyweight BGE reranker is great on GPU, a
light model (jina-tiny / ms-marco-MiniLM) is the practical choice on CPU. Loaded
lazily on first use.
"""
from __future__ import annotations

from ..config import RERANK_TOP_N, RERANKER_MODEL


class Reranker:
    def __init__(self, model_name: str = RERANKER_MODEL, top_n: int = RERANK_TOP_N):
        self.model_name = model_name
        self.top_n = top_n
        self._model = None  # lazy — avoid the model load until first query

    def _ensure(self):
        if self._model is None:
            from fastembed.rerank.cross_encoder import TextCrossEncoder
            self._model = TextCrossEncoder(model_name=self.model_name)
        return self._model

    def rerank(
        self,
        query: str,
        items: list[tuple[int, str]],
        top_n: int | None = None,
    ) -> list[tuple[int, float]]:
        """Rescore (query, text) pairs and reorder.

        `items` are (chunk_idx, text) in fused order; only the first `top_n` are
        rescored. Returns [(chunk_idx, rerank_score)] sorted by relevance desc.
        """
        if not items:
            return []
        cand = items[: (top_n or self.top_n)]
        scores = self._ensure().rerank(query, [text for _, text in cand])
        return sorted(
            ((idx, float(s)) for (idx, _), s in zip(cand, scores)),
            key=lambda x: x[1],
            reverse=True,
        )
