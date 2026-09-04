"""
Level 4 building block: retrieval over a prebuilt embedding index.

The heavy work happens offline in build_index.py: documents are chunked,
embedded, and written to index/. This module only loads that file and, per
question, embeds the query and takes a dot product. That is why the deployed
function needs neither a PDF parser nor a model - just numpy and one API call.

Documents -> chunks -> embeddings -> index/ (committed)
Question -> embedding -> cosine against the index -> top matches
"""
import json
import os
import threading

import numpy as np

import embeddings

TOP_K = 8

# Cosine similarity below this is treated as "no match". Every embedding model
# has a high similarity floor - unrelated text still scores well above zero -
# so without a floor an off-topic question returns the least-bad chunks anyway
# and the model dutifully cites them.
#
# The right value is model-specific, so it cannot be one constant. Both figures
# below were measured on this corpus, five on-topic questions against four
# off-topic ones:
#
#   openai  on-topic 0.469-0.699, off-topic peaks at 0.245. A wide gap, so 0.30
#           sits clear of the noise while keeping weaker but real matches.
#   local   on-topic 0.639-0.773, off-topic reaches 0.596. Much tighter, hence
#           the higher and less comfortable 0.62.
#
# The gap being four times wider under OpenAI is itself worth showing: a better
# embedding model does not just rank better, it makes "no good match" separable
# from "a weak match" at all.
DEFAULT_MIN_SCORE = {"openai": 0.30, "local": 0.62}
FALLBACK_MIN_SCORE = 0.30


def min_score_for(provider: str) -> float:
    override = os.environ.get("RAG_MIN_SCORE")
    if override:
        return float(override)
    return DEFAULT_MIN_SCORE.get(provider, FALLBACK_MIN_SCORE)

HERE = os.path.dirname(os.path.abspath(__file__))
DEFAULT_INDEX_DIR = os.path.join(HERE, "..", "index")


class VectorStore:
    """A prebuilt index: chunk metadata plus one unit vector per chunk."""

    def __init__(self, index_dir: str, min_score: float | None = None):
        self.index_dir = index_dir

        meta_path = os.path.join(index_dir, "chunks.json")
        vec_path = os.path.join(index_dir, "vectors.json")
        if not (os.path.exists(meta_path) and os.path.exists(vec_path)):
            raise FileNotFoundError(
                f"No index at {index_dir}. Build one first:\n"
                f"    python backend/build_index.py\n"
                f"(or EMBEDDING_PROVIDER=local python backend/build_index.py "
                f"to build without an API key)"
            )

        with open(meta_path) as f:
            meta = json.load(f)
        with open(vec_path) as f:
            vectors = json.load(f)

        self.chunks: list[dict] = meta["chunks"]
        self.documents: list[str] = meta["documents"]
        self.provider: str = meta.get("provider", "unknown")
        self.model: str = meta.get("model", "unknown")
        self.dimensions: int = meta.get("dimensions", 0)
        # Threshold follows whichever model built the index, not whichever is
        # configured now - mixing those up silently breaks retrieval.
        self.min_score = (
            min_score if min_score is not None else min_score_for(self.provider)
        )

        if len(vectors) != len(self.chunks):
            raise ValueError(
                f"index is inconsistent: {len(vectors)} vectors for "
                f"{len(self.chunks)} chunks. Rebuild it."
            )

        # Normalise once at load, so each query is a single matrix multiply.
        matrix = np.asarray(vectors, dtype=np.float32)
        norms = np.linalg.norm(matrix, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        self.matrix = matrix / norms

    def _embed_query(self, query: str) -> np.ndarray:
        """Embed a question, refusing loudly if the configured model does not
        match the one that built the index. Different models produce different
        dimensions, and even at equal dimensions their vectors are unrelated -
        so a mismatch is silent nonsense rather than an error."""
        if embeddings.provider() != self.provider:
            raise RuntimeError(
                f"index was built with EMBEDDING_PROVIDER={self.provider} "
                f"({self.model}) but the app is configured for "
                f"{embeddings.provider()}. Rebuild the index with "
                f"'python backend/build_index.py' or change EMBEDDING_PROVIDER."
            )

        q = np.asarray(embeddings.embed_query(query), dtype=np.float32)
        if q.shape[0] != self.matrix.shape[1]:
            raise RuntimeError(
                f"query embedding has {q.shape[0]} dimensions but the index has "
                f"{self.matrix.shape[1]}. Rebuild the index."
            )
        return q

    def search(self, query: str, top_k: int = TOP_K) -> list[dict]:
        q = self._embed_query(query)
        norm = float(np.linalg.norm(q)) or 1.0
        scores = self.matrix @ (q / norm)

        results = []
        for i in np.argsort(scores)[::-1][:top_k]:
            score = float(scores[i])
            if score < self.min_score:
                continue
            chunk = self.chunks[int(i)]
            results.append(
                {
                    "chunk_index": chunk["chunk_index"],
                    "document": chunk["document"],
                    "page": chunk["page"],
                    "text": chunk["text"],
                    "score": round(score, 4),
                }
            )
        return results


_store: VectorStore | None = None
_store_lock = threading.Lock()
_store_error: str | None = None


def get_store() -> VectorStore:
    global _store, _store_error
    with _store_lock:
        if _store is None:
            index_dir = os.environ.get("RAG_INDEX_DIR", DEFAULT_INDEX_DIR)
            try:
                _store = VectorStore(index_dir)
            except Exception as exc:
                _store_error = str(exc)
                raise
    return _store


def warm_store() -> None:
    """Load the index at startup. Cheap now - it is a file read, not a build."""
    try:
        store = get_store()
        print(
            "[rag] index ready: %d chunks across %d documents, %s (%d dims)"
            % (
                len(store.chunks),
                len(store.documents),
                store.model,
                store.dimensions,
            )
        )
    except Exception as exc:
        print(f"[rag] index unavailable: {exc}")


def store_status() -> dict:
    if _store is not None:
        return {
            "ready": True,
            "chunks": len(_store.chunks),
            "documents": _store.documents,
            "model": _store.model,
            "dimensions": _store.dimensions,
            "min_score": _store.min_score,
        }
    return {"ready": False, "error": _store_error, "detail": "loading"}


def document_summary() -> list[dict]:
    """Per-document chunk counts, for the Level 4 knowledge-base list."""
    if _store is None:
        return []
    counts: dict[str, int] = {}
    for c in _store.chunks:
        counts[c["document"]] = counts.get(c["document"], 0) + 1
    return [{"title": t, "chunks": counts.get(t, 0)} for t in _store.documents]


def chunk_breakdown(document: str, limit: int = 12) -> dict:
    """How one document was cut up, for the 'How RAG works' walkthrough."""
    store = get_store()
    picked = [c for c in store.chunks if c["document"] == document][:limit]
    if not picked:
        return {"document": document, "chunks": [], "total_chunks": 0}

    rows = []
    prev = None
    for c in picked:
        # How many leading characters this chunk shares with the previous one.
        overlap = 0
        if prev is not None and prev["page"] == c["page"]:
            k = min(150, len(prev["text"]), len(c["text"]))
            while k > 0 and prev["text"][-k:] != c["text"][:k]:
                k -= 1
            overlap = k

        # A slice of the actual vector, so the walkthrough can show what a chunk
        # really turns into rather than an illustration of it.
        row_index = store.chunks.index(c)
        preview = [round(float(v), 3) for v in store.matrix[row_index][:24]]

        rows.append(
            {
                "chunk_index": c["chunk_index"],
                "page": c["page"],
                "text": c["text"],
                "characters": len(c["text"]),
                "overlap_with_previous": overlap,
                "dimensions": store.dimensions,
                "vector_preview": preview,
            }
        )
        prev = c

    total = sum(1 for c in store.chunks if c["document"] == document)
    return {
        "document": document,
        "chunks": rows,
        "total_chunks": total,
        "showing": len(rows),
        "chunk_size": 900,
        "chunk_overlap": 150,
        "model": store.model,
        "dimensions": store.dimensions,
    }


def score_all(query: str, document: str | None = None, limit: int = 12) -> dict:
    """Every chunk scored against a query, for the walkthrough."""
    store = get_store()
    q = store._embed_query(query)
    norm = float(np.linalg.norm(q)) or 1.0
    scores = store.matrix @ (q / norm)

    selected = {r["chunk_index"] for r in store.search(query)}

    order = [
        i
        for i in np.argsort(scores)[::-1]
        if document is None or store.chunks[int(i)]["document"] == document
    ][:limit]

    rows = []
    for rank, i in enumerate(order, start=1):
        c = store.chunks[int(i)]
        score = float(scores[i])
        rows.append(
            {
                "rank": rank,
                "chunk_index": c["chunk_index"],
                "document": c["document"],
                "page": c["page"],
                "score": round(score, 4),
                "above_threshold": score >= store.min_score,
                "selected": c["chunk_index"] in selected,
                "text": c["text"][:260],
            }
        )

    return {
        "query": query,
        "scored": rows,
        "threshold": store.min_score,
        "top_k": TOP_K,
        "total_chunks": len(store.chunks),
        "selected_count": len(selected),
        "model": store.model,
        "dimensions": store.dimensions,
    }
