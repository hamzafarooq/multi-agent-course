# Gateway (Node / Express) — the "software backend"

The only server the browser talks to. It serves the widget, validates and
forwards requests to the Python AI service, exposes `/health` + `/stats`, and
logs traffic. It is ~90% done — you implement **two** `TODO (YOU)` blocks in
`server.js`:

1. **Request logging middleware** — one structured line per request (method, url, status, ms).
2. **`callAiService()`** — POST JSON to the Python service and return its response.

## Run it

```bash
npm install
cp .env.example .env      # PORT=8787, AI_SERVICE_URL=http://localhost:8000
npm start                 # or: npm run dev  (auto-restart)
```

Start the Python AI service first (port 8000), then this gateway (port 8787).

## Check it

```bash
curl -s localhost:8787/health           # should report the AI service health too
curl -s localhost:8787/translate -H 'content-type: application/json' \
  -d '{"text":"Hello there","target":"es-MX"}'
```

Once both `TODO`s are done and the AI service works, load the widget (console
snippet or extension) on any page and it will translate through this gateway.

## Why split gateway from AI service?

This is the FDE lesson: the browser-facing app layer (CORS, validation,
logging, serving assets, rate limits later) is a different concern from the AI
layer (prompts, models, caching, keys). Keeping them as separate services lets
each scale, deploy, and fail independently — and keeps your API keys off the
edge that the browser can reach.
