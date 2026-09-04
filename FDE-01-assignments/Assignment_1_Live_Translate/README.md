# Assignment 1 — Live Translate

> Ship a browser widget that translates any English web page into **Mexican
> Spanish** in real time and on demand — then build the backend that powers it.

You are given a **working frontend** (a widget, a console loader, and a Chrome
extension). Your job is to build the **backend** it talks to. When your backend
works, the widget lights up on any page on the internet. That's the whole game.

This is the first assignment of the **Forward Deployed Engineer (FDE)** track.
It's deliberately shaped like real FDE work: you don't get a clean sandbox, you
get *someone else's page* and a widget you have to make useful by standing up a
real service behind it — with an LLM, a cache, logs, and a deploy.

---

## Why this assignment

A Forward Deployed Engineer takes a capability and makes it work **in the
customer's environment**, end to end. This assignment compresses that into one
afternoon:

- **Ship into an environment you don't control** — the browser, on pages you didn't write.
- **Own a service** — an LLM-backed API with caching, logging, and a health check.
- **Respect a contract** — a fixed API the frontend already speaks. You conform to it; you don't get to change it.
- **Separate concerns** — an app/gateway layer vs. an AI layer, talking over HTTP.
- **Make it observable** — prove your cache works with latency and hit-rate, not vibes.
- **Deploy it** — at minimum, run the whole thing locally with one command per service.

---

## Architecture

Three moving parts. The **frontend is done**. You build the **two backend services**.

```
   ┌─────────────────────────┐
   │  Browser (any web page) │
   │  ┌───────────────────┐  │
   │  │  🌐 Widget         │  │   ← PROVIDED, working
   │  │  (or extension)   │  │
   │  └─────────┬─────────┘  │
   └────────────┼────────────┘
                │  POST /translate           (JSON over HTTP, CORS)
                ▼
   ┌─────────────────────────┐
   │  Node Gateway  :8787     │   ← YOU (software backend) — ~2 TODOs
   │  CORS · validate · log  │
   │  serve widget · proxy   │
   └────────────┬────────────┘
                │  POST /translate
                ▼
   ┌─────────────────────────┐
   │  Python AI Service :8000 │   ← YOU (AI backend) — the real work
   │  LLM · cache · AI logs  │
   └────────────┬────────────┘
                │
       ┌────────┴────────┐
       ▼                 ▼
   LLM provider    SQLite cache (translations.db)
```

**Why two services?** The browser-facing concerns (CORS, validation, serving
assets, rate limiting, request logs) are genuinely different from the AI
concerns (prompts, model choice, caching, API keys). Splitting them is the FDE
habit: each deploys and fails independently, and your API keys never live on
the edge the browser can reach.

---

## What's provided vs. what you build

| Component | Status | Path |
|-----------|--------|------|
| Translation widget | ✅ Provided, working | `widget/translation-widget.js` |
| Console loader | ✅ Provided | `loader/console-snippet.js` |
| Chrome extension (MV3) | ✅ Provided | `extension/` |
| Demo page to test on | ✅ Provided | `demo-pages/index.html` |
| **Node gateway** | 🔨 **You** — 2 TODOs | `backend/gateway-node/` |
| **Python AI service** | 🔨 **You** — the core | `backend/ai-service-python/` |

You should not need to edit the widget. Read it to understand the contract, then
build a backend that satisfies it.

---

## The API contract (do not change it)

The widget speaks this to the **Node gateway**, and the gateway forwards the
same shapes to the **Python AI service**.

### `POST /translate`
```jsonc
// request
{ "text": "Good morning, welcome!", "target": "es-MX" }
// response
{ "translated": "¡Buenos días, bienvenido!", "cached": false, "latencyMs": 812, "model": "claude-sonnet-4-6" }
```

### `POST /translate/batch`  (used by "Translate page")
```jsonc
// request
{ "texts": ["Home", "Best sellers", "Add to cart"], "target": "es-MX" }
// response
{ "results": [ { "translated": "Inicio", "cached": true }, ... ], "latencyMs": 40 }
```

### `GET /health`
```jsonc
{ "status": "ok", "model": "claude-sonnet-4-6", "cacheSize": 128 }
```

### `GET /stats`
```jsonc
{ "requests": 40, "memory_hits": 22, "db_hits": 6, "misses": 12, "hit_rate_pct": 70.0 }
```

**Contract rules that matter:**
- `cached` must be **true** when the answer came from your cache (no LLM call).
- `latencyMs` must be measured on the server for both paths — a cache hit should be *dramatically* faster than a miss. That gap is the point.
- Identical `(text, target)` must **never** hit the LLM twice.
- Errors return a JSON body and a sensible status (`400` bad input, `502` upstream failure, `501` not-implemented).

---

## Build it — recommended order

Build the AI service first (you can test it with `curl`, no browser needed),
then the gateway, then load the widget.

### Part 1 — Python AI service (the real work)
`backend/ai-service-python/` · full guide in its own README.

1. `lib/llm.py` — write the Mexican-Spanish prompt and the LLM call.
2. `lib/cache.py` — implement the SQLite tier (`init` / `get` / `set`); the memory tier and stats are given.
3. `app.py` — wire the **cache→LLM→cache** flow in `translate_one()`.

```bash
cd backend/ai-service-python
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your API key
uvicorn app:app --reload --port 8000
```

Test it in isolation:
```bash
curl -s localhost:8000/translate -H 'content-type: application/json' \
  -d '{"text":"Good morning, welcome!","target":"es-MX"}'   # run twice → 2nd is cached
```

### Part 2 — Node gateway (software backend)
`backend/gateway-node/` · two TODOs in `server.js`.

1. Request-logging middleware (method, url, status, ms).
2. `callAiService()` — proxy to the Python service.

```bash
cd backend/gateway-node
npm install
cp .env.example .env
npm start                   # http://localhost:8787
```

### Part 3 — see it live

- **Extension (recommended — required for real sites):** `chrome://extensions` → enable
  Developer mode → *Load unpacked* → select the `extension/` folder. Its content script
  **injects the widget onto every page** and its background worker proxies to your gateway,
  so it works even on strict-CSP sites (homedepot.com, google, github). Use the popup to set
  the backend URL. **This is the widget — the extension is just how it gets onto the page.**
- **Console (quick one-off, permissive pages only):** open a page → DevTools → Console →
  paste `loader/console-snippet.js`. Note: strict-CSP sites will block this — that's why the
  live-website test uses the extension.
- **Demo page:** open `demo-pages/index.html`, uncomment the `<script src=".../widget.js">` line at the bottom.

Open the **translate button** bottom-right and click **Translate page** → the
whole page flips to Mexican Spanish. Click **Restore page**, then **Translate
page** again → the badges show **cache hits** and the latency drops.

> Note: the extension loads its own copy of the widget at
> `extension/translation-widget.js`. If you change the widget, re-copy it
> (`cp widget/translation-widget.js extension/`).

### Part 4 — ship it on Fly.io

Localhost proves it runs; a deploy proves it's a product. Put **both** services on
[Fly.io](https://fly.io) and point the extension at the public gateway.

```bash
# one app per service (run in each backend dir)
cd backend/ai-service-python && fly launch --no-deploy   # set secrets, then:
fly secrets set ANTHROPIC_API_KEY=...                     # or your provider's key — never bake it into the image
fly deploy

cd ../gateway-node && fly launch --no-deploy
fly secrets set AI_SERVICE_URL=https://<your-ai-app>.fly.dev
fly deploy
```

Then set the gateway's public URL (`https://<your-gateway-app>.fly.dev`) in the extension
popup. Your **live-website test must pass against the deployed gateway**, not localhost.

> Keep the AI service private if you can (Fly private networking / `flycast`) so only the
> gateway can reach it — the browser should only ever touch the gateway.

---

## Performance, SLAs & cost

A translation that's correct but slow or expensive fails in production. Your
backend must meet the SLA in `benchmark/sla.json`, and you **prove it with the
provided benchmark** — no eyeballing.

### The SLA (targets you must hit)

| Metric | Target | Why it matters |
|--------|--------|----------------|
| Cache **hit** latency, p95 | ≤ 60 ms | a cache hit should feel instant |
| Cache **miss** latency, p95 | ≤ 3500 ms | one LLM round-trip, end to end |
| **Cache hit rate** (benchmark workload) | ≥ 60 % | repeated text must be served from cache |
| Error rate | ≤ 1 % | reliability under concurrency |
| Warm **throughput** | ≥ 20 req/s | translate a page's worth of chunks fast |

### Cost & time-to-value

Every **cache miss** costs an LLM call; every **hit** is effectively free — so
your hit rate is a direct lever on cost. `bench.py` reports:

- **latency percentiles** (your "time to translate") and **throughput**
- **cost per miss** (token estimate × your provider's price)
- **monthly cost with vs. without cache** at the volume in `sla.json`, and the **savings**

> The prices in `sla.json` are **placeholders**. Set `input_usd_per_mtok` /
> `output_usd_per_mtok` to your provider's current published rates before you
> trust the dollar figures.

### Run the benchmark

```bash
# with both services running:
python benchmark/bench.py                  # end-to-end through the gateway
python benchmark/bench.py --direct         # straight to the AI service (:8000)
python benchmark/bench.py --json out.json  # also write machine-readable results
```

`bench.py` **exits non-zero if any SLA fails**, so it doubles as your grading
gate and a CI check.

---

## Requirements checklist

Your backend must:

- [ ] **LLM** — translate EN → **Mexican Spanish** (es-MX register, not generic Spanish) via a real LLM call.
- [ ] **Caching** — two-tier (in-memory + SQLite), keyed by a hash of `(text, target)`; identical input never calls the LLM twice; `cached`/`latencyMs`/`/stats` reflect it.
- [ ] **Logging** — one structured line per request in the gateway **and** per translation in the AI service; greppable.
- [ ] **Tracing** — a request ID at the gateway (reusing an inbound `X-Request-Id` if present, else generated), forwarded to the AI service, and logged by both; one request is greppable end-to-end across both services by that single ID.
- [ ] **Performance** — meets every SLA in `benchmark/sla.json`; `python benchmark/bench.py` exits `0`.
- [ ] **Runs locally** — each service starts with a single documented command; secrets come from `.env` (never committed).
- [ ] **Deployed on Fly.io** — both services deployed; the extension works against the public gateway URL, not just localhost.
- [ ] **Contract** — every endpoint matches the shapes above; the provided widget works unmodified.
- [ ] **Product evaluation** — a `PRODUCT_EVAL.md` (or PDF) generated by the `/fde-live-translate-eval` skill, including a live-website test on a real site you don't control (e.g. homedepot.com), submitted with your video.

---

## Definition of Done — non-negotiables

> **This section is written for your coding agent.** The same list lives in
> [`AGENTS.md`](AGENTS.md), which Claude Code and most agent harnesses read
> automatically. Treat every box as a hard requirement and **self-verify each
> one** with the commands at the bottom before claiming the work is done. Do not
> mark a box checked from inspection alone — run the check.

**Contract (must match exactly)**
- [ ] `POST /translate` → `{ "translated": string, "cached": boolean, "latencyMs": number, "model": string }`
- [ ] `POST /translate/batch` → `{ "results": [{ "translated": string, "cached": boolean }], "latencyMs": number }`
- [ ] `GET /health` → `{ "status": "ok", ... }` and `GET /stats` → cache stats incl. a hit rate
- [ ] Status codes: `400` invalid input, `501` not implemented, `502` upstream failure
- [ ] The provided widget works **unmodified** against the gateway at `:8787`

**LLM**
- [ ] Output is natural **Mexican Spanish (es-MX)**, translation only — no preamble, no wrapping quotes
- [ ] Numbers, prices (`$`), and product/model codes are preserved
- [ ] Provider is swappable via env; the API key is read from `.env`, never hard-coded
- [ ] **Errors surface, never swallowed** — on a provider/LLM failure the request returns `502` and the error is logged; the service **never returns the untranslated input as if it succeeded** (a silent "return the original text" fallback is an automatic fail)

**Caching (hard)**
- [ ] Identical `(text, target)` **never** calls the LLM twice
- [ ] `cached: true` appears **only** when the response came from cache
- [ ] Two tiers — in-memory **and** SQLite; the SQLite cache **survives a restart**
- [ ] Cache key is a hash of `(text, target)`

**Logging & tracing**
- [ ] Gateway logs one structured line per request: method, url, status, duration (ms)
- [ ] AI service logs one structured line per translation: cached, latencyMs, chars
- [ ] A request ID is set at the gateway (inbound `X-Request-Id` reused if present, else generated), forwarded to the AI service, and logged by both — one request is greppable end-to-end across both services by that single ID

**Performance (SLA gate)**
- [ ] `python benchmark/bench.py` exits `0` — every SLA in `benchmark/sla.json` passes

**Deploy**
- [ ] Each service starts locally with a single documented command
- [ ] Both services are deployed to Fly.io and the extension works against the public gateway URL

**Hygiene**
- [ ] `.env`, `node_modules/`, `.venv/`, `*.db`, `*.log` are git-ignored and NOT committed

**Self-verify (run all of these; all must pass)**
```bash
# 1. both services up
curl -sf localhost:8000/health && curl -sf localhost:8787/health

# 2. contract + cache: run twice — 2nd response must have "cached": true and a much lower latencyMs
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'
curl -s localhost:8787/translate -H 'content-type: application/json' -d '{"text":"Good morning","target":"es-MX"}'

# 3. cache survives restart: stop + restart the AI service, repeat the call above → still "cached": true

# 4. SLA gate — must exit 0
python benchmark/bench.py

# 5. no secrets / junk staged
git status --porcelain | grep -E '\.env$|node_modules|\.venv|\.db$' && echo "FAIL: unstage these" || echo "clean"

# 6. trace correlation: grab a request's id from the gateway log, then confirm it in BOTH logs
grep "<request-id>" gateway.log ai-service.log     # must appear in both services

# 7. deployed for real: the public Fly.io gateway answers
curl -sf https://<your-gateway-app>.fly.dev/health
```

---

## Grading (100 pts)

| Area | Pts | What we look for |
|------|-----|------------------|
| Widget lights up | 15 | Fresh clone → follow README → Translate page works end to end on the demo page and a real site |
| LLM & prompt quality | 20 | Natural Mexican Spanish; numbers/prices/model codes preserved; translation only (no preamble) |
| Caching correctness | 20 | Real two-tier cache; provable hits; big latency gap; survives a restart (SQLite) |
| Performance & SLA | 15 | `benchmark/bench.py` exits 0; hit/miss latency, hit rate, throughput all meet `sla.json` |
| Logging & observability | 10 | Structured, useful logs; a request ID correlates one request across both services; accurate `/stats`; `/health` reports the AI service |
| Service separation & contract | 10 | Clean gateway↔AI split; correct status codes; graceful errors |
| Deploy & docs | 10 | Both services deployed on Fly.io and reachable via the public gateway; one-command local run; clear `.env.example`; your own short run notes |

### Sample scorecard

This is what a strong submission looks like — the scored rubric your `PRODUCT_EVAL.md`
captures. **Illustrative only**; your numbers must come from your own run (fabricating
them is an automatic fail).

> **Assignment 1 — Live Translate · Jordan Lee · 93 / 100**

| Criterion | Pts | Awarded | Status | Evidence |
|-----------|-----|---------|--------|----------|
| Widget lights up | 15 | 15 | ✅ Pass | `/translate` + `/translate/batch` return valid shapes; page flips to es-MX live on homedepot.com |
| Caching correctness | 20 | 20 | ✅ Pass | 2nd identical call `cached: true`, **3 ms vs 812 ms**; `translations.db` has 214 rows; survives restart |
| Performance & SLA | 15 | 15 | ✅ Pass | `bench.py` exits 0 — hit p95 4 ms, miss p95 2.9 s, hit rate 71%, 34 req/s |
| Logging & observability | 10 | 10 | ✅ Pass | Structured lines in both services; one trace id correlates a request end-to-end; `/stats` hit rate accurate |
| Service separation & contract | 10 | 10 | ✅ Pass | Clean gateway↔AI split; `400` on empty text; gateway `/health` nests AI-service health |
| LLM & prompt quality | 20 | 17 | ⚠️ Partial | Natural es-MX, translation-only; `$1,299.00` and `SKU-4471` preserved; one idiom rendered a little stiff |
| Deploy & docs | 10 | 6 | ⚠️ Partial | Deployed on Fly.io, public gateway healthy; run notes present; AI service left publicly reachable (no `flycast`) |
| **Total** | **100** | **93** | | Auto: 70/70 · Manual: 23/30 |

**Red-line checks (auto-flagged):** ✅ no secrets committed · ✅ no edits to provided `widget/` · `extension/` · `benchmark/`

**Captured evidence (excerpt)**
- Samples: *"Good morning, welcome!"* → *"¡Buenos días, bienvenido!"* · *"Add to cart"* → *"Agregar al carrito"*
- Latency: miss p95 **2.9 s** · hit p95 **4 ms** (~700× faster on a cache hit)
- Cost: ~$0.0004 / miss · at 71% hit rate, projected monthly bill is ~⅓ of no-cache
- Deploy: `https://jordan-livetranslate-gw.fly.dev/health` → `{"status":"ok"}`

Read your `eval/REPORT.md` the same way: fix any **Fail/Partial** rows before you record the demo.

---

## Stretch goals (bonus)

- **Dockerize** both services + a `docker-compose.yml` so `docker compose up` runs everything.
- **Harden the deploy** — multi-region on Fly.io, autoscale (`fly autoscale`), a health-check-driven restart policy, and a GitHub Action that runs `bench.py` and `fly deploy` on green.
- **Rate limiting** on the gateway (per-IP) with a `429` + friendly widget message.
- **Streaming** long translations token-by-token into the widget.
- **Cache TTL / invalidation** and a `POST /clear-cache` endpoint.
- **Language picker** in the widget/popup (es-MX, es-ES, pt-BR…) threaded through the contract.

---

## Submit

Every FDE project is submitted as a **Product Evaluation + a video demo**.

1. **Generate the evaluation with the skill.** In Claude Code, run
   **`/fde-live-translate-eval`** (bundled in `.claude/skills/`). It runs the
   automated rubric + benchmark, performs a **live-website test on a real site you
   don't control (default homedepot.com)**, and writes **`PRODUCT_EVAL.md`** at the
   assignment root. Export a **PDF** if you prefer (`md-to-pdf` skill or `pandoc`).
   - Under the hood it runs `python eval/eval.py --student "…" --video "…"` and
     `python benchmark/bench.py` — you can run those directly too. See [`eval/`](eval/).
2. **Submit `PRODUCT_EVAL.md` (or the PDF)** and a **60–90s screen recording**:
   the widget translating a real page into Mexican Spanish, then a cache hit shown in the badges.
3. Push your repo with both `backend/` services implemented. Do **not** commit
   `.env`, `node_modules/`, `.venv/`, or `*.db`. Add a short **"How I ran it"**
   section to your README noting which LLM provider you used.

---

## Troubleshooting

- **Widget shows "Can't reach backend"** → the Node gateway isn't running, or the widget's `API_URL` doesn't match. Set it in the extension popup, or `window.FDE_CONFIG = { API_URL: "..." }` before pasting the console snippet.
- **"endpoint isn't implemented yet"** → expected until you finish the TODOs. That message *is* your progress bar.
- **CORS errors** → the gateway enables CORS for all origins in dev; make sure requests go to the gateway (`:8787`), not the AI service (`:8000`).
- **macOS port 5000 is taken** → that's AirPlay Receiver. We use `8787`/`8000` on purpose; keep them.
- **Extension didn't update after a code change** → re-copy the widget into `extension/` and hit *Reload* on `chrome://extensions`.
