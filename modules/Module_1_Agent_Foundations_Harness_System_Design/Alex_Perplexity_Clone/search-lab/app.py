"""
Search Lab: keyword retrieval and semantic retrieval, side by side.

A frontend for basic_keyword_semantic_search.py. Both retrievers run over the
same documents for the same query, so the difference between matching WORDS and
matching MEANING is something you watch happen rather than something you are
told.

Keyword side reproduces the notebook exactly: an inverted index, and
tf * log(N / (df + 1)) summed over the query's terms.
Semantic side uses nomic-embed-text-v1.5, which needs its documents and its
queries prefixed differently - a real detail people get wrong in production.
"""
import math
import os
import re
import sys
import threading

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# The module's .env lives one level up; without loading it the lab has no
# OPENAI_API_KEY and no EMBEDDING_PROVIDER, and silently falls back to defaults.
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env"))

app = FastAPI(title="Search Lab")
app.add_middleware(
    CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"]
)

DEFAULT_DOCUMENTS = [
    "The cat is playing in the garden",
    "A dog and cat are good pets",
    "Cats love to chase mice",
    "Machine learning is based on algorithms",
    "Deep learning uses neural networks",
    "Recurrent networks have connections",
    "The cost of this shirt is $15",
]

# Queries chosen because they make the two approaches disagree, with the
# explanations checked against what the code actually returns.
SAMPLE_QUERIES = [
    {
        "query": "cat that chases mouse",
        "why": "The notebook's own query, and keyword search gets it wrong. It ranks 'The cat is playing in the garden' first, because 'cat' is a literal match, while the document that is genuinely about a cat chasing a mouse never surfaces: 'mice' is not 'mouse' and 'Cats' is not 'cat'.",
    },
    {
        "query": "feline hunting rodents",
        "why": "Not one of these three words appears anywhere in the library. Keyword search returns nothing at all. A reader knows exactly which document is meant.",
    },
    {
        "query": "pet animals",
        "why": "Same again, in business language rather than zoology. 'Pets' is in a document, but 'pet' is a different string.",
    },
    {
        "query": "deep learning",
        "why": "A subtle one. Both approaches match, but keyword search puts 'Machine learning' first because 'learning' is common, while meaning-based search correctly puts 'Deep learning uses neural networks' first.",
    },
    {
        "query": "how much does the shirt cost",
        "why": "Worth showing so nobody concludes keyword search is simply broken. 'cost' and 'shirt' are both literal matches, and it wins outright here.",
    },
]


# --------------------------------------------------------------- tokenizing

# The notebook uses nltk's word_tokenize. We deliberately do not: importing
# nltk alongside torch segfaults on this Python build, and for sentences this
# short the two tokenizers are byte-identical (verified across every document
# and query shipped here). Same tokens, no crash.

def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+|[^\w\s]", text)


TOKENIZER = "regex, equivalent to nltk word_tokenize on these documents"


# ------------------------------------------------------- keyword retrieval

def build_index(documents: list[str]) -> dict:
    """Word -> list of document ids. Straight from the notebook."""
    index: dict[str, list[int]] = {}
    for i, doc in enumerate(documents):
        for word in tokenize(doc):
            index.setdefault(word, []).append(i)
    return index


def keyword_search(query: str, documents: list[str]) -> dict:
    tokenized = [tokenize(d) for d in documents]
    index = build_index(documents)
    n = len(documents)

    def tfidf(word: str, doc_id: int) -> float:
        tf = tokenized[doc_id].count(word)
        df = len(index[word]) if word in index else 0
        idf = math.log(n / (df + 1))
        return tf * idf

    query_words = tokenize(query)
    scores = {i: 0.0 for i in range(n)}
    # Per-term working, so the panel can show why a score is what it is.
    working = []
    for q in query_words:
        if q in index:
            hits = []
            for doc_id in set(index[q]):
                contribution = tfidf(q, doc_id)
                scores[doc_id] += contribution
                hits.append({"doc": doc_id, "contribution": round(contribution, 4)})
            working.append({
                "term": q,
                "in_index": True,
                "document_frequency": len(set(index[q])),
                "hits": sorted(hits, key=lambda h: -h["contribution"]),
            })
        else:
            working.append({
                "term": q,
                "in_index": False,
                "document_frequency": 0,
                "hits": [],
            })

    ranked = sorted(scores.items(), key=lambda kv: kv[1], reverse=True)
    return {
        "results": [
            {"doc": i, "score": round(s, 4), "matched": s > 0} for i, s in ranked
        ],
        "working": working,
        "matched_count": sum(1 for _, s in scores.items() if s > 0),
        "vocabulary": len(index),
        "tokenizer": TOKENIZER,
    }


# ------------------------------------------------------ semantic retrieval

# Same provider the main assistant uses, so one env var switches both:
#   EMBEDDING_PROVIDER=openai   text-embedding-3-small over the API
#   EMBEDDING_PROVIDER=local    nomic-embed-text-v1.5, offline, no key
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "backend"))
import embeddings  # noqa: E402
import gate  # noqa: E402

# See gate.py. Disabled when APP_PASSWORD is unset, which is the local default.
gate.install(app)

_warm_error: str | None = None
_warmed = False


def warm_model() -> None:
    global _warm_error, _warmed
    try:
        embeddings.embed_query("warm up")
        _warmed = True
        print(f"[search-lab] embeddings ready: {embeddings.model_name()}")
    except Exception as exc:
        _warm_error = str(exc)
        print(f"[search-lab] embeddings unavailable: {exc}")


@app.on_event("startup")
def _warm():
    threading.Thread(target=warm_model, daemon=True).start()


def semantic_search(query: str, documents: list[str]) -> dict:
    # Cosine by hand with numpy: importing scipy alongside torch pulls in a
    # second OpenMP runtime, which segfaults on macOS.
    import numpy as np

    doc_vecs = embeddings.embed_documents(documents)
    q_vec = embeddings.embed_query(query)

    q = np.asarray(q_vec, dtype=float)
    q_norm = float(np.linalg.norm(q)) or 1.0

    rows = []
    for i, vec in enumerate(doc_vecs):
        d = np.asarray(vec, dtype=float)
        similarity = float(q @ d / (q_norm * (float(np.linalg.norm(d)) or 1.0)))
        rows.append({
            "doc": i,
            "distance": round(1 - similarity, 4),
            "score": round(similarity, 4),
        })
    rows.sort(key=lambda r: -r["score"])
    return {
        "results": rows,
        "model": embeddings.model_name(),
        "provider": embeddings.provider(),
        "dimensions": len(doc_vecs[0]) if doc_vecs else 0,
    }


# ------------------------------------------------------------------ routes

class SearchRequest(BaseModel):
    query: str
    documents: list[str] | None = None
    # Left unset so it can follow the provider: every embedding model has its
    # own similarity floor, and a threshold tuned for one is wrong for another.
    threshold: float | None = None


@app.get("/api/setup")
def setup():
    return {
        "documents": DEFAULT_DOCUMENTS,
        "samples": SAMPLE_QUERIES,
        "tokenizer": TOKENIZER,
        "model": embeddings.model_name(),
        "provider": embeddings.provider(),
        "model_ready": _warmed,
        "model_error": _warm_error,
    }


@app.post("/api/search")
def search(req: SearchRequest):
    documents = req.documents or DEFAULT_DOCUMENTS
    # nomic scores unrelated text around 0.3-0.5; OpenAI sits much lower.
    default_threshold = 0.55 if embeddings.provider() == "local" else 0.30
    threshold = req.threshold if req.threshold is not None else default_threshold
    keyword = keyword_search(req.query, documents)

    try:
        semantic = semantic_search(req.query, documents)
        semantic_error = None
    except Exception as exc:
        semantic, semantic_error = None, str(exc)

    # Where the two disagree is the entire point, so compute it server-side
    # rather than leaving the audience to eyeball two lists.
    verdict = None
    if semantic:
        kw_hits = {r["doc"] for r in keyword["results"] if r["matched"]}
        sem_hits = {
            r["doc"] for r in semantic["results"] if r["score"] >= threshold
        }
        verdict = {
            "keyword_only": sorted(kw_hits - sem_hits),
            "semantic_only": sorted(sem_hits - kw_hits),
            "both": sorted(kw_hits & sem_hits),
            "threshold": threshold,
        }

    return {
        "query": req.query,
        "documents": documents,
        "keyword": keyword,
        "semantic": semantic,
        "semantic_error": semantic_error,
        "verdict": verdict,
    }


frontend_dir = os.path.join(os.path.dirname(__file__), "frontend")


class NoCacheStaticFiles(StaticFiles):
    def file_response(self, *args, **kwargs):
        response = super().file_response(*args, **kwargs)
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate"
        return response


app.mount("/", NoCacheStaticFiles(directory=frontend_dir, html=True), name="frontend")
