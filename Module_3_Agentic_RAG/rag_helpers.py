"""
rag_helpers.py — Helper functions for Agentic RAG with Semantic Cache
These are the helper functions for the Agentic RAG with Semantic Cache notebook.

All heavy lifting lives here so the notebook stays clean and focused
on demonstrating the system behaviour.

Quick start in a Colab/Jupyter notebook:
    import sys, nest_asyncio
    sys.path.insert(0, '/content/multi-agent-course/Module_3_Agentic_RAG')
    nest_asyncio.apply()

    from rag_helpers import init_rag, SemanticCaching, agentic_rag_with_cache

    init_rag(openai_api_key="...", serp_api_key="...", qdrant_path="...")
    cache = SemanticCaching(clear_on_init=True)
    agentic_rag_with_cache("What was Uber's revenue in 2021?", cache)
"""

import faiss
import json
import re
import time
import asyncio
import os

import numpy as np
import requests

from sentence_transformers import SentenceTransformer
from transformers import AutoTokenizer, AutoModel
from openai import OpenAI, OpenAIError
import qdrant_client as _qdrant_lib


# ── Module-level shared state (populated by init_rag) ────────────────────────
_openaiclient   = None
_serp_api_key   = None
_qdrant         = None
_text_tokenizer = None
_text_model     = None


# ── Initialisation ────────────────────────────────────────────────────────────

def init_rag(openai_api_key: str, serp_api_key: str, qdrant_path: str) -> None:
    """
    Initialise all shared state for the Agentic RAG pipeline.

    Must be called once before using any other function in this module.

    Args:
        openai_api_key: OpenAI API key — used for routing and RAG generation.
        serp_api_key:   SerpApi key  — used for live Google search results.
        qdrant_path:    Absolute path to the local Qdrant vector database
                        (contains 'opnai_data' and '10k_data' collections).
    """
    global _openaiclient, _serp_api_key, _qdrant, _text_tokenizer, _text_model

    _openaiclient = OpenAI(api_key=openai_api_key)
    _serp_api_key = serp_api_key
    _qdrant = _qdrant_lib.AsyncQdrantClient(path=qdrant_path)

    print("Loading Nomic text model for Qdrant retrieval embeddings...")
    _text_tokenizer = AutoTokenizer.from_pretrained(
        "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True
    )
    _text_model = AutoModel.from_pretrained(
        "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True
    )
    print("✅ RAG pipeline ready.")


# ── SemanticCaching ───────────────────────────────────────────────────────────

class SemanticCaching:
    """
    FAISS-backed semantic cache with a time-sensitivity filter.

    Routing logic for agentic_rag_with_cache():
        is_time_sensitive → True   →  skip cache, run Agentic RAG live
        check_cache       → HIT    →  return stored answer instantly ⚡
        check_cache       → MISS   →  run Agentic RAG, store answer, return
    """

    TIME_SENSITIVE_KEYWORDS = [
        "today", "tonight", "now", "currently", "current",
        "latest", "recent", "recently", "right now", "at the moment",
        "at present", "as of now", "this week", "this month", "this year",
        "this quarter", "this season", "this morning", "this afternoon",
        "this evening", "this weekend", "yesterday", "tomorrow",
        "last week", "last month", "last year", "upcoming", "live",
        "breaking", "just happened", "what time", "what day", "what date",
        "happening now", "events today", "news today", "news this week",
        "stock price", "share price", "weather", "forecast", "temperature",
        "real-time", "realtime", "schedule today",
    ]

    def __init__(
        self,
        json_file: str = "rag_cache.json",
        threshold: float = 0.2,
        clear_on_init: bool = False,
    ):
        """
        Args:
            json_file:      Path to the JSON file used for cache persistence.
            threshold:      Max Euclidean distance for a cache hit (lower = stricter).
            clear_on_init:  If True, wipe any existing cache on startup.
        """
        self.embedding_dim = 768
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.euclidean_threshold = threshold
        self.json_file = json_file

        print("Loading Nomic embedding model for semantic cache...")
        self.encoder = SentenceTransformer(
            "nomic-ai/nomic-embed-text-v1.5", trust_remote_code=True
        )
        print("Cache embedding model ready.")

        if clear_on_init:
            self.clear_cache()
        else:
            self.load_cache()

    # ── Time-sensitivity ─────────────────────────────────────────────────────

    def is_time_sensitive(self, question: str) -> bool:
        """
        Return True if the question contains temporal indicators whose
        answers change over time and should never be served from cache.

        Examples that return True  → bypass cache, always fetch live:
            'What is the current stock price of AAPL?'
            'What are the latest AI news this week?'
            'Are there any AWS outages right now?'

        Examples that return False → safe to cache:
            'What was Uber revenue in 2021?'
            'How do OpenAI Agents work?'
            'What is machine learning?'
        """
        q = question.lower()
        return any(kw in q for kw in self.TIME_SENSITIVE_KEYWORDS)

    # ── Persistence ───────────────────────────────────────────────────────────

    def clear_cache(self):
        """Reset in-memory state and overwrite the JSON file."""
        self.cache = {"questions": [], "embeddings": [], "response_text": []}
        self.index = faiss.IndexFlatL2(self.embedding_dim)
        self.save_cache()
        print("Semantic cache cleared.")

    def load_cache(self):
        """Load entries from JSON and rebuild the FAISS index."""
        try:
            with open(self.json_file, "r") as f:
                self.cache = json.load(f)
            if self.cache["embeddings"]:
                vecs = np.array(self.cache["embeddings"], dtype=np.float32)
                self.index.add(vecs)
            print(f"Cache loaded: {len(self.cache['questions'])} entries.")
        except FileNotFoundError:
            self.cache = {"questions": [], "embeddings": [], "response_text": []}
            print("No existing cache found — starting fresh.")

    def save_cache(self):
        """Persist the current cache to disk."""
        with open(self.json_file, "w") as f:
            json.dump(self.cache, f)

    # ── Lookup & storage ──────────────────────────────────────────────────────

    def check_cache(self, question: str):
        """
        Encode the question and search the FAISS index for a near-enough neighbour.

        Returns:
            tuple: (hit, answer, embedding, similarity, row_id)
                hit        (bool)          — True if a cached answer was found
                answer     (str | None)    — The cached answer, or None on miss
                embedding  (np.ndarray)    — Computed embedding; reuse on miss to avoid re-encoding
                similarity (float | None)  — Score in [0, 1], or None on miss
                row_id     (int | None)    — Cache row index, or None on miss
        """
        embedding = self.encoder.encode([question], normalize_embeddings=True)

        if self.index.ntotal == 0:
            return False, None, embedding, None, None

        D, I = self.index.search(embedding, 1)
        if I[0][0] != -1 and D[0][0] <= self.euclidean_threshold:
            row_id = int(I[0][0])
            similarity = float(1.0 - D[0][0])
            return True, self.cache["response_text"][row_id], embedding, similarity, row_id

        return False, None, embedding, None, None

    def add_to_cache(self, question: str, answer: str, embedding: np.ndarray):
        """Store a new question-answer pair and persist to disk."""
        self.cache["questions"].append(question)
        self.cache["embeddings"].append(embedding[0].tolist())
        self.cache["response_text"].append(answer)
        self.index.add(embedding)
        self.save_cache()


# ── Agentic RAG pipeline internals ───────────────────────────────────────────

def get_internet_content(user_query: str, action: str = "INTERNET_QUERY") -> str:
    """
    Live Google search via SerpApi.

    Used for INTERNET_QUERY routes and for all time-sensitive queries.
    Results are structured as an answer-box snippet + top organic results.

    Args:
        user_query: The user's question.
        action:     Route label (unused here, kept for signature compatibility).

    Returns:
        str: Formatted search results, or an error message.
    """
    print("Getting your response from the internet 🌐 ...")
    if not _serp_api_key:
        return "Error: SERP_API_KEY not set — call init_rag() first."

    params = {"q": user_query, "api_key": _serp_api_key, "engine": "google", "num": 5}
    try:
        resp = requests.get("https://serpapi.com/search.json", params=params)
        resp.raise_for_status()
        data = resp.json()

        parts = []
        ab = data.get("answer_box", {})
        if ab.get("answer"):
            parts.append(f"[Direct Answer] {ab['answer']}")
        elif ab.get("snippet"):
            parts.append(f"[Direct Answer] {ab['snippet']}")

        for i, r in enumerate(data.get("organic_results", [])[:5], 1):
            if r.get("snippet"):
                parts.append(
                    f"[{i}] {r.get('title', '')}\n"
                    f"    {r['snippet']}\n"
                    f"    Source: {r.get('link', '')}"
                )
        return "\n\n".join(parts) if parts else "No results found."

    except requests.exceptions.RequestException as e:
        return f"SerpApi request error: {e}"
    except Exception as e:
        return f"Unexpected error: {e}"


def route_query(user_query: str) -> dict:
    """
    Use GPT-4o to classify the query into one of three route labels.

    Returns:
        dict with keys 'action', 'reason', 'answer'.
        action is one of: 'OPENAI_QUERY', '10K_DOCUMENT_QUERY', 'INTERNET_QUERY'.
    """
    if not _openaiclient:
        return {"action": "INTERNET_QUERY", "reason": "RAG not initialised — call init_rag().", "answer": ""}

    prompt = f"""
    Classify the user query into exactly one of three categories:
    1. "OPENAI_QUERY"       — Questions about OpenAI documentation: agents, APIs, models, embeddings.
    2. "10K_DOCUMENT_QUERY" — Questions about company financials or 10-K filings (Uber, Lyft).
    3. "INTERNET_QUERY"     — Everything else: general knowledge, trends, comparisons, real-time data.

    Respond ONLY with this JSON (no other text):
    {{
        "action": "OPENAI_QUERY" or "10K_DOCUMENT_QUERY" or "INTERNET_QUERY",
        "reason": "brief justification",
        "answer": "AT MAX 5 words. Leave empty if INTERNET_QUERY"
    }}

    User: {user_query}
    """
    try:
        response = _openaiclient.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "system", "content": prompt}],
        )
        content = response.choices[0].message.content
        match = re.search(r"\{.*\}", content, re.DOTALL)
        return json.loads(match.group())
    except (OpenAIError, json.JSONDecodeError, AttributeError) as e:
        return {"action": "INTERNET_QUERY", "reason": f"Routing error: {e}", "answer": ""}


def _get_text_embeddings(text: str) -> np.ndarray:
    """Mean-pooled token embeddings used for Qdrant similarity search."""
    inputs = _text_tokenizer(text, return_tensors="pt", padding=True, truncation=True)
    outputs = _text_model(**inputs)
    return outputs.last_hidden_state.mean(dim=1)[0].detach().numpy()


def _rag_formatted_response(user_query: str, context: list) -> str:
    """Generate a GPT-4o answer grounded in retrieved Qdrant chunks, with citations."""
    prompt = f"""
    Based on the given context, answer the user query: {user_query}
    Context: {context}
    Cite sources as [1][2]...
    """
    response = _openaiclient.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": prompt}],
    )
    return response.choices[0].message.content


async def _retrieve_and_respond(user_query: str, action: str) -> str:
    """Embed query → search the right Qdrant collection → generate RAG answer."""
    collections = {"OPENAI_QUERY": "opnai_data", "10K_DOCUMENT_QUERY": "10k_data"}
    if action not in collections:
        return f"Invalid action: {action}"
    try:
        embedding = _get_text_embeddings(user_query)
        hits = await _qdrant.query_points(
            collection_name=collections[action], query=embedding, limit=3
        )
        contents = [p.payload["content"] for p in hits.points]
        if not contents:
            return "No relevant content found in the database."
        return _rag_formatted_response(user_query, contents)
    except Exception as e:
        return f"Retrieval error: {e}"


def _run_rag_pipeline(user_query: str) -> str:
    """
    Route the query and call the appropriate handler.

    Internal helper used by agentic_rag_with_cache() so the answer string
    can be captured for caching before being displayed.

    Returns:
        str: The final answer from the selected knowledge source.
    """
    GREY, RESET = "\033[90m", "\033[0m"

    route = route_query(user_query)
    action = route.get("action", "INTERNET_QUERY")
    reason = route.get("reason", "")
    print(f"{GREY}📍 Route: {action}  |  {reason}{RESET}")

    handlers = {
        "OPENAI_QUERY":       lambda q: asyncio.run(_retrieve_and_respond(q, "OPENAI_QUERY")),
        "10K_DOCUMENT_QUERY": lambda q: asyncio.run(_retrieve_and_respond(q, "10K_DOCUMENT_QUERY")),
        "INTERNET_QUERY":     lambda q: get_internet_content(q),
    }
    handler = handlers.get(action)
    if not handler:
        return f"Unsupported action: {action}"

    try:
        return handler(user_query)
    except Exception as e:
        return f"Execution error: {e}"


# ── Public entry point ────────────────────────────────────────────────────────

def agentic_rag_with_cache(user_query: str, cache: SemanticCaching) -> str:
    """
    Agentic RAG with a semantic cache layer.

    Query flow:
        1. Time-sensitive?  → skip cache, run full RAG pipeline live
        2. Cache HIT        → return stored answer instantly ⚡
        3. Cache MISS       → run full RAG pipeline, store answer, return

    Args:
        user_query: The user's question.
        cache:      A SemanticCaching instance to check and update.

    Returns:
        str: The final answer text.
    """
    CYAN, GREEN, YELLOW, BOLD, RESET = (
        "\033[96m", "\033[92m", "\033[93m", "\033[1m", "\033[0m"
    )

    print(f"{BOLD}{CYAN}👤 Query:{RESET} {user_query}\n")

    # 1. Time-sensitivity bypass
    if cache.is_time_sensitive(user_query):
        print(f"{YELLOW}⏰ Time-sensitive — bypassing cache for a fresh answer.{RESET}\n")
        result = _run_rag_pipeline(user_query)
        print(f"\n{BOLD}{CYAN}🤖 Response (live):{RESET}\n{result}\n")
        return result

    # 2. Semantic cache lookup
    start = time.time()
    hit, cached_answer, embedding, similarity, row_id = cache.check_cache(user_query)

    if hit:
        elapsed = time.time() - start
        print(
            f"{GREEN}✅ Cache HIT{RESET} "
            f"(row {row_id}, similarity: {similarity:.3f}, {elapsed:.3f}s)\n"
        )
        print(f"{BOLD}{CYAN}🤖 Response (cached):{RESET}\n{cached_answer}\n")
        return cached_answer

    # 3. Cache miss → full RAG pipeline
    print(f"{YELLOW}❌ Cache MISS — running Agentic RAG pipeline...{RESET}\n")
    result = _run_rag_pipeline(user_query)

    cache.add_to_cache(user_query, result, embedding)
    print(f"\n{GREEN}💾 Cached for future similar queries.{RESET}")
    print(f"\n{BOLD}{CYAN}🤖 Response:{RESET}\n{result}\n")
    return result
