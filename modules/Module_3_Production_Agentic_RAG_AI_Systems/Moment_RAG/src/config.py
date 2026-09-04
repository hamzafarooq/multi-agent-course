"""Central config for the moment-level RAG demo (seeded from the original spec)."""
import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
TRANSCRIPT_DIR = DATA / "transcripts"
CHUNK_DIR = DATA / "chunks"
EMBED_DIR = DATA / "embeddings"

for d in (TRANSCRIPT_DIR, CHUNK_DIR, EMBED_DIR):
    d.mkdir(parents=True, exist_ok=True)

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
EMBED_MODEL = os.getenv("EMBED_MODEL", "text-embedding-3-large")
EMBED_DIM = int(os.getenv("EMBED_DIM", "1024"))
LLM_MODEL = os.getenv("LLM_MODEL", "gpt-4o-mini")        # cheap internal calls (decompose, self-query, enrich)
SYNTH_MODEL = os.getenv("SYNTH_MODEL", "gpt-4o")          # the user-facing cited answer

# Qdrant hybrid store. ":memory:" rebuilds the index in-process each run (demo-grade);
# point at a path or URL to persist.
QDRANT_LOCATION = os.getenv("QDRANT_LOCATION", ":memory:")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "moment_rag_chunks")
SPARSE_MODEL = os.getenv("SPARSE_MODEL", "Qdrant/bm25")


def _envbool(name: str, default: bool) -> bool:
    return os.getenv(name, str(default)).strip().lower() in ("1", "true", "yes", "on")


# Cross-encoder reranker — rescores the top-N fused candidates. Light ONNX model
# (~3s/query on CPU); set RERANKER_MODEL to a heavier BGE reranker on GPU.
RERANKER_ENABLED = _envbool("RERANKER_ENABLED", True)
RERANKER_MODEL = os.getenv("RERANKER_MODEL", "jinaai/jina-reranker-v1-tiny-en")
RERANK_TOP_N = int(os.getenv("RERANK_TOP_N", "50"))

# Pipeline feature flags.
ENABLE_QUESTION_INDEX = _envbool("ENABLE_QUESTION_INDEX", True)  # index per-chunk HyDE questions as a multivector branch
ENABLE_SELF_QUERY = _envbool("ENABLE_SELF_QUERY", True)          # LLM infers metadata filters from the query
SELF_QUERY_MIN_RESULTS = int(os.getenv("SELF_QUERY_MIN_RESULTS", "3"))  # below this, drop the filter (soft fallback)

# Retrieval / fusion.
RRF_RANK_CONSTANT = 60
KNN_K = 50
KNN_INNER_HITS_SIZE = 3

# Chunking.
CHUNK_TOKENS = 256
CHUNK_STRIDE = 0.25  # 25% stride (fixed-window fallback)

# Semantic chunking. Transcripts carry no punctuation, so units are small fixed
# word-windows; a boundary is placed where the cosine distance between consecutive
# units exceeds the percentile threshold. Boundary detection uses a local model.
SEMANTIC_CHUNKING = _envbool("SEMANTIC_CHUNKING", True)
SEMANTIC_UNIT_WORDS = int(os.getenv("SEMANTIC_UNIT_WORDS", "30"))
SEMANTIC_BUFFER = int(os.getenv("SEMANTIC_BUFFER", "1"))
SEMANTIC_BREAKPOINT_PERCENTILE = float(os.getenv("SEMANTIC_BREAKPOINT_PERCENTILE", "90"))
SEMANTIC_MIN_TOKENS = int(os.getenv("SEMANTIC_MIN_TOKENS", "50"))
SEMANTIC_EMBED_MODEL = os.getenv("SEMANTIC_EMBED_MODEL", "BAAI/bge-small-en-v1.5")

# Chunk-metadata vocabulary — shared by the ingest enricher and the self-query filter.
SECTION_TYPES = [
    "introduction", "background_story", "framework", "tactic", "lesson",
    "prediction", "debate", "anecdote", "qa", "conclusion", "other",
]
