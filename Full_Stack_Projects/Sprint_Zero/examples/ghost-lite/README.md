# ghost-lite

A complete Sprint Zero run, committed exactly as the pipeline produced it. Reference: [Ghost](https://ghost.org) ([TryGhost/Ghost](https://github.com/TryGhost/Ghost)). Scope: MVP, web-app, node-react, local. Run on 10 and 11 September 2026.

What it is: one writer owns one site, posts move from draft to published, readers become free members with an email, and an "Ask me" box answers a reader's question from the site's published posts with citations. The seeded site is the [Traversaal.ai blog](https://blog.traversaal.ai/), ten real articles loaded from `.sprint-zero/seed/traversaal-posts.json`.

## Run

```
cd server && npm install && node index.js      # :3001, creates and seeds server/data.db on start
cd client && npm install && npm run dev        # :5173
```

Demo login: `demo@traversaal.ai` / `inkwell-demo`. Public site: `http://localhost:5173/s/traversaal-ai`.

Ask me works with no configuration: it returns matching passages from SQLite full-text search. To have Claude write the answer instead, export `ANTHROPIC_API_KEY` in the shell that starts the server. `GET http://localhost:3001/health` reports which mode the server is in.

## What is here

- `docs/` the six generated specs: scope, reference brief, PRD, decisions, user stories, API contract. The contract is the file both engineers built from.
- `server/` Express 5, better-sqlite3 with an FTS5 index over published posts, a self-issued JWT, an idempotent seed. `server/tests/integration.test.js` is QA's test: run `node tests/integration.test.js` from `server/` against a running server.
- `client/` React 18 on Vite. Public pages follow Ghost's Casper theme; the admin follows Ghost's Shade look.

## What QA verified

All 19 routes matched the contract on both sides. Integration tests: 97/97 in search mode, 102/102 in answer mode, 99/99 with an invalid key (degradation). In a real browser: the full auth dance including an expired token, the core loop with a fresh writer, a draft-leak check across every public surface, member idempotency, and Ask me in all three modes. No application code needed fixing. After QA, the backend was re-spawned once to hand the model fuller passages so answers were substantive; the response shape did not change and the tests still pass.

Known gaps, by design: no member feed (members have no login), no error-path browser tests (Prod scope), search-mode snippets can show raw markdown because search runs over the stored markdown.
