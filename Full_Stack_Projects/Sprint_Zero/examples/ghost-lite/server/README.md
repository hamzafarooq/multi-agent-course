# Inkwell API (server)

Express + SQLite backend for the Sprint Zero build. Implements `docs/api-contract.md` exactly.

No account, no `.env`, no keys. The database is a single file at `server/data.db`, created on first run.

## Run it

```bash
cd server
npm install
node seed.js      # loads the Traversaal.ai demo site; prints the demo login
node index.js     # http://localhost:3001
```

The seed also runs automatically every time the server starts, so `node seed.js` is optional. It is idempotent: run it as often as you like and you still get one demo writer, one site and ten posts.

Demo writer credentials (printed by the seed on every run):

```
demo@traversaal.ai / inkwell-demo
```

Public demo site: `GET /sites/traversaal-ai` and `GET /sites/traversaal-ai/posts`.

## Optional environment variables

| Variable | Effect |
| --- | --- |
| `ANTHROPIC_API_KEY` | When set, Ask me writes an answer with Claude (`claude-opus-5`) from the matching passages. Without it, Ask me returns the matching passages as search results. Never required. |
| `JWT_SECRET` | Signing secret for writer tokens. Defaults to `sprint-zero-dev-secret`. |
| `PORT` | Defaults to `3001`. |
| `CORS_ORIGIN` | Comma-separated allowed origins. Defaults to `http://localhost:5173,http://127.0.0.1:5173`. |
| `DB_PATH` | Defaults to `server/data.db`. |

`GET /health` reports which mode the server is in: `{ "status": "ok", "fts5": true, "answer_mode": "search" }`.

## Layout

```
index.js        Express app, CORS, routes, error shape, runs the seed on start
db.js           SQLite schema (CREATE TABLE IF NOT EXISTS) and the FTS5 index
seed.js         Loads ../.sprint-zero/seed/traversaal-posts.json idempotently
auth.js         JWT signing and the requireAuth middleware
search.js       Ask me retrieval: FTS5 with LIKE fallback, <mark> snippets
answer.js       Ask me answer mode via @anthropic-ai/sdk (only when a key is set)
routes/auth.js  POST /auth/signup, POST /auth/login, GET /auth/me
routes/me.js    /me/site and /me/posts (writer, protected)
routes/sites.js /sites/:slug/... (public: site, posts, members, ask)
lib/            slug, excerpt, reading-time helpers and response serializers
```

## Ask me

Retrieval is SQLite FTS5 over the title and body of published posts only. Publish adds a post to the index, unpublish and delete remove it, and the index is rebuilt after every seed. If the bundled SQLite has no FTS5, the server logs a warning, falls back to LIKE search, and reports `fts5: false` from `/health`.

Answer mode is on only when `ANTHROPIC_API_KEY` is set. The model sees the snippets (not whole posts), is told to answer only from them, and cites by post id. If the call fails or exceeds 12 seconds, the response falls back to `mode: "search"` with `answer_error`. The reader never sees a 5xx from Ask me.
