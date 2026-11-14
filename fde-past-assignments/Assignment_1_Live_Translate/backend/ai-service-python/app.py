"""
FDE · Assignment 1 · Python AI Service  (this is the real assignment)
=====================================================================
A small FastAPI service that translates English → Mexican Spanish with:
  - an LLM call            (lib/llm.py)
  - a two-tier cache       (lib/cache.py)  — memory + SQLite
  - structured logging     (lib/logger.py) — provided, wired for you

The Node gateway forwards the browser's requests here. You implement the
TODOs so the widget lights up. Run:

    python -m venv .venv && source .venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env          # then add your API key
    uvicorn app:app --reload --port 8000
"""
import os
import time

from dotenv import load_dotenv
from fastapi import FastAPI
from pydantic import BaseModel

from lib.cache import TwoTierCache
from lib.llm import translate_text
from lib.logger import get_logger

load_dotenv()

MODEL = os.getenv("MODEL", "claude-sonnet-4-6")
DB_PATH = os.getenv("TRANSLATION_DB_PATH", "translations.db")

app = FastAPI(title="FDE Live Translate — AI Service")
log = get_logger("ai-service")
cache = TwoTierCache(DB_PATH)

# request/response shapes ----------------------------------------------------
class TranslateIn(BaseModel):
    text: str
    target: str = "es-MX"

class BatchIn(BaseModel):
    texts: list[str]
    target: str = "es-MX"


@app.on_event("startup")
async def startup():
    await cache.init()
    log.info("ai_service_started", extra={"model": MODEL, "db": DB_PATH})


# --- core: translate one string --------------------------------------------
async def translate_one(text: str, target: str) -> dict:
    """Translate a single string, using the cache first.

    Returns a dict shaped exactly like the widget expects:
        {"translated": str, "cached": bool, "latencyMs": int, "model": str}
    """
    text = (text or "").strip()
    if not text:
        return {"translated": "", "cached": False, "latencyMs": 0, "model": MODEL}

    t0 = time.perf_counter()

    # -----------------------------------------------------------------------
    # TODO (YOU) — the caching flow. This is the heart of the assignment.
    #   1. Ask the cache for `text` (cache.get). If it's a HIT, use it and set
    #      cached=True — do NOT call the LLM.
    #   2. On a MISS, call the LLM (translate_text), then store the result
    #      (cache.set) so the next identical request is a hit. cached=False.
    #   3. Measure latencyMs from t0 in BOTH paths (a cache hit should be
    #      dramatically faster — that's the point you're demonstrating).
    #
    # cached_value = await cache.get(text, target)
    # if cached_value is not None:
    #     ...
    # else:
    #     translated = await translate_text(text, target, model=MODEL)
    #     await cache.set(text, target, translated, model=MODEL)
    #     ...
    # -----------------------------------------------------------------------
    raise NotImplementedError("Implement the cache/LLM flow in translate_one()")


@app.post("/translate")
async def translate(body: TranslateIn):
    result = await translate_one(body.text, body.target)
    log.info(
        "translate",
        extra={"cached": result["cached"], "latencyMs": result["latencyMs"], "chars": len(body.text)},
    )
    return result


@app.post("/translate/batch")
async def translate_batch(body: BatchIn):
    t0 = time.perf_counter()
    results = []
    for t in body.texts:
        results.append(await translate_one(t, body.target))
    latency = int((time.perf_counter() - t0) * 1000)
    hits = sum(1 for r in results if r["cached"])
    log.info("translate_batch", extra={"count": len(results), "hits": hits, "latencyMs": latency})
    # widget expects {results: [{translated, cached}], latencyMs}
    return {"results": [{"translated": r["translated"], "cached": r["cached"]} for r in results], "latencyMs": latency}


@app.get("/health")
async def health():
    return {"status": "ok", "model": MODEL, "cacheSize": await cache.size()}


@app.get("/stats")
async def stats():
    return await cache.stats()
