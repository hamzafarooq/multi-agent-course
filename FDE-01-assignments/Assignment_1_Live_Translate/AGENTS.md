# AGENTS.md — non-negotiables for this assignment

You are helping a student complete **FDE Assignment 1 — Live Translate**. Read
`README.md` for the full brief. This file is the contract you must satisfy. Do
not relax, reinterpret, or "improve" these requirements — conform to them.

## What you may and may not touch

- **BUILD:** `backend/ai-service-python/` (LLM, cache, logging — the core work)
  and `backend/gateway-node/` (two `TODO (YOU)` blocks: request-logging
  middleware + `callAiService()` proxy).
- **DO NOT EDIT:** `widget/`, `loader/`, `extension/`, `demo-pages/`,
  `benchmark/`. These are the provided frontend and the grader. The widget is
  the acceptance test — make it work unmodified. If something seems to require
  editing them, you've misread the contract.

## Hard requirements (all must hold)

### API contract — match exactly
- `POST /translate` → `{ "translated": string, "cached": boolean, "latencyMs": number, "model": string }`
- `POST /translate/batch` → `{ "results": [{ "translated": string, "cached": boolean }], "latencyMs": number }`
- `GET /health` → `{ "status": "ok", ... }`
- `GET /stats` → cache stats including a hit rate
- Status codes: `400` invalid input · `501` not implemented · `502` upstream failure
- The browser talks ONLY to the Node gateway (`:8787`); the gateway talks to the Python AI service (`:8000`).

### LLM
- Translate English → **Mexican Spanish (es-MX)** — not generic/Castilian Spanish.
- Return the translation ONLY: no preamble, no explanations, no wrapping quotes.
- Preserve numbers, prices (`$`), and product/model codes verbatim.
- Read the API key from `.env`. Never hard-code a key. Keep the provider swappable.
- **Fail loud on LLM errors.** If the provider call fails, propagate the error so the gateway returns `502` and log it. NEVER wrap the call in a `try/except` that returns the original English as if it were translated — a silent fallback that returns the input on failure is an **automatic fail**. (This is a real bug we've seen ship: a dependency mismatch made every call throw, the `except` returned the input untouched, and the "translator" silently served English for weeks.)

### Caching (this is the point of the assignment)
- Identical `(text, target)` MUST NOT call the LLM twice.
- `cached: true` ONLY when the response came from cache.
- Two tiers: in-memory dict + SQLite. The SQLite tier MUST survive a process restart.
- Cache key = SHA-256 of `(text, target)`.
- `latencyMs` is measured server-side on both paths; a hit must be dramatically faster than a miss.

### Logging & tracing
- Gateway: one structured line per request (method, url, status, duration ms).
- AI service: one structured line per translation (cached, latencyMs, chars). Use the provided `lib/logger.py`.
- **Trace correlation (your first trace):** the gateway derives a request ID for every request
  — reusing an inbound `X-Request-Id` header if present, otherwise generating one — logs it, and
  forwards it to the AI service (`x-request-id` header). The AI service logs that same ID on its
  translation line. One request must be greppable end-to-end across both services by that single
  ID. Keep it this simple — full tracing comes later.

### Performance / SLA gate
- `python benchmark/bench.py` MUST exit `0`. It enforces `benchmark/sla.json`:
  cache-hit p95 ≤ 60 ms, cache-miss p95 ≤ 3500 ms, hit rate ≥ 60 %, error rate ≤ 1 %, throughput ≥ 20 req/s.

### Deploy
- Each service starts locally with a single documented command (`npm start`; `uvicorn app:app --port 8000`).
- **Ship it for real on Fly.io.** Deploy both services (`fly launch` → `fly deploy`) and point
  the extension popup's backend URL at the public gateway. "Deployed, not a demo" is the point
  of this track — the live-website test must pass against the deployed gateway, not just localhost.

### Hygiene
- Never commit `.env`, `node_modules/`, `.venv/`, `*.db`, or `*.log`.

## Definition of done — verify, don't assume

Run every step and confirm it passes before telling the student you're done:

```bash
# 1. both services up
curl -sf localhost:8000/health && curl -sf localhost:8787/health

# 2. contract + cache proof: run twice; 2nd MUST be "cached": true with far lower latencyMs
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'

# 3. cache persistence: restart the AI service, repeat the call → still "cached": true

# 4. SLA gate (must exit 0)
python benchmark/bench.py

# 5. hygiene
git status --porcelain | grep -E '\.env$|node_modules|\.venv|\.db$' && echo "FAIL" || echo "clean"

# 6. widget still works UNMODIFIED (git diff must show no changes under widget/ or extension/)
git diff --stat -- widget extension

# 7. trace correlation: one request is greppable end-to-end by a single request ID
#    (make a request, grab its id from the gateway log, then:)
grep "<request-id>" gateway.log ai-service.log   # must appear in BOTH

# 8. deployed for real: the public Fly.io gateway answers
curl -sf https://<your-app>.fly.dev/health
```

If any check fails, fix the backend — not the frontend, not the benchmark, not the SLA.

## Submission

The deliverable is a **Product Evaluation + video demo**. Generate the report with
the bundled **`/fde-live-translate-eval`** skill: it runs the rubric (`eval/eval.py`)
and benchmark (`benchmark/bench.py`), does a **live-website test on a real site the
student doesn't control (e.g. homedepot.com)**, and writes `PRODUCT_EVAL.md` (PDF
optional). Do not fabricate any numbers or sample translations — every value comes
from an actual run.
