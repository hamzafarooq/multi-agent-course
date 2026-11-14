# AI Service (Python / FastAPI) — the core of Assignment 1

This service does the actual translating, caching, and AI-side logging. The
Node gateway forwards requests here; the browser never talks to it directly.

## What you implement

| File | What's there | Your job |
|------|--------------|----------|
| `app.py` | Endpoints wired, logging wired | The cache→LLM flow in `translate_one()` |
| `lib/llm.py` | Prompt guidance + a Claude example | The LLM call itself |
| `lib/cache.py` | Class + memory tier + stats | The SQLite tier (`init`/`get`/`set`) |
| `lib/logger.py` | ✅ Done — structured JSON logs | Nothing (extend if you want) |

## Run it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # add your API key, pick your MODEL
uvicorn app:app --reload --port 8000
```

Then hit it directly to test without the browser:

```bash
curl -s localhost:8000/health
curl -s localhost:8000/translate -H 'content-type: application/json' \
  -d '{"text":"Good morning, welcome!","target":"es-MX"}'
# run the same command twice — the second should show "cached": true and a far lower latencyMs
curl -s localhost:8000/stats
```

## The three things this teaches

1. **LLM call** — a tight, register-specific prompt (Mexican Spanish, not generic Spanish).
2. **Caching** — memory + SQLite, keyed by a hash of `(text, target)`. Identical text must never hit the LLM twice. Prove it with `latencyMs` and `/stats`.
3. **Logging** — one structured line per translation, greppable in `ai-service.log`.
