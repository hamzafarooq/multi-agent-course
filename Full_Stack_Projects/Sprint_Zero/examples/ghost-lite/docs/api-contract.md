# API contract

_Sprint Zero build (Inkwell). Stack: node-react. Data layer: local. Level: MVP._

This file is law. The backend implements exactly these routes and shapes; the frontend consumes exactly these routes and shapes; QA tests against them. The two engineers never talk to each other, so nothing here is implied — if a field is not listed, it is not returned.

## Auth

The backend exposes `POST /auth/signup`, `POST /auth/login` and `GET /auth/me`. Signup and login return `{ access_token, user, site }`. The client stores `access_token` (in `localStorage`, so the session survives reload and a new tab; log out deletes it) and sends it as `Authorization: Bearer <token>` on every protected call.

Tokens are JWTs the backend signs itself with HS256, secret from `process.env.JWT_SECRET` defaulting to `"sprint-zero-dev-secret"`, payload `{ sub: <user id>, email: <email> }`, expiry 7 days. Protected-route middleware verifies the token and sets `req.user = { id, email }`. A missing, malformed, expired or badly signed token returns `401` with `{ "error": "unauthorized", "message": "Missing or invalid token." }`.

Scoping: every writer owns at most one site. Every `/me/*` route acts on the site owned by `req.user.id`. Posts are scoped through their site; a writer reaching a post on someone else's site gets `403`. The backend never returns `owner_id`, `user_id` or `password_hash` in any response body.

Members are not users. They have no password, no token and no login. Membership is a `(site, email)` row created by a public endpoint.

## Base URL

`http://localhost:3001` (node-react profile, `server/`, `node index.js`). The frontend runs on `http://localhost:5173`; the backend enables CORS for that origin (all methods, `Authorization` and `Content-Type` headers).

## Frontend routes

Both engineers agree on these so every link and every `ask-citation` href is the same string.

| Route | Screen |
| --- | --- |
| `/` | Landing page (`hero-cta-signup`, `nav-login`) |
| `/signup`, `/login` | Writer sign-up / log-in |
| `/admin` | Writer's posts list |
| `/admin/setup` | Create or edit the writer's site |
| `/admin/posts/new`, `/admin/posts/:id` | Editor (new / existing post by id) |
| `/s/:slug` | Public site home (feed + Ask me) |
| `/s/:slug/:postSlug` | Public post page |
| `/s/:slug/feed` | Member feed page — not backed by an endpoint in this contract (see "Deferred") |

An `ask-citation` href is always `/s/<site slug>/<post slug>` on the frontend origin, built from the `slug` in the ask response plus the site slug of the page being viewed. The API never returns frontend URLs; the frontend builds them.

## Entities

- `User` — a writer. Email and password. Owns at most one site.
- `Site` — one writer's publication: title, description, accent colour, slug. Addressed publicly by slug.
- `Post` — belongs to a site. Title, slug, markdown body, excerpt, `draft` or `published`, published date, author name.
- `Member` — a reader's email attached to one site. No password. Unique per `(site_id, email)`.

### JSON shapes

All IDs are UUID v4 strings. All timestamps are ISO 8601 UTC strings.

**User**

```json
{
  "id": "6f1c2e1a-9d3b-4c6e-8a7f-1b2c3d4e5f60",
  "email": "maya@fieldnotes.blog",
  "created_at": "2026-09-10T09:12:44.000Z"
}
```

**Site**

```json
{
  "id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d",
  "slug": "field-notes",
  "title": "Field Notes",
  "description": "Essays on soil and weather",
  "accent_color": "#1f6f43",
  "created_at": "2026-09-10T09:14:02.000Z",
  "updated_at": "2026-09-10T09:14:02.000Z"
}
```

`slug` is derived from `title` on create: lowercase, non-alphanumerics collapsed to single hyphens, leading/trailing hyphens trimmed (`"Traversaal.ai"` → `traversaal-ai`). Site slugs are unique across the install; on collision append `-2`, `-3`, ... The slug is fixed at creation and does not change when the title is edited. `accent_color` is always a 7-character `#rrggbb` string.

**Post** (full)

```json
{
  "id": "c7d8e9f0-1a2b-4c3d-9e4f-5a6b7c8d9e0f",
  "site_id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d",
  "title": "On mulch",
  "slug": "on-mulch",
  "body_markdown": "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms.",
  "excerpt": "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms.",
  "status": "draft",
  "published_at": null,
  "author_name": "Field Notes",
  "reading_time_minutes": 1,
  "created_at": "2026-09-10T09:20:11.000Z",
  "updated_at": "2026-09-10T09:20:11.000Z"
}
```

**Post summary** — the same object without `body_markdown`. Used in every list response.

Rules that apply to every Post:

- `status` is exactly `"draft"` or `"published"`.
- `published_at` is `null` until the first publish. Publish sets it to now if it is `null`. Unpublish sets `status` back to `"draft"` and leaves `published_at` as it was, so republishing keeps the original date (Ghost's behaviour). A post with `status: "draft"` may therefore carry a non-null `published_at`; consumers filter on `status`, never on `published_at`.
- `slug` is derived from the title on create with the same algorithm as site slugs, unique per site (append `-2`, `-3`, ...). It never changes after creation, including when the title is edited.
- `excerpt` is always a non-empty string. If the writer supplies one it is stored as given. If the writer supplies none (or an empty string), the server stores the first two sentences of `body_markdown` with markdown syntax stripped, cut to at most 300 characters. It is recomputed on update only while no explicit excerpt has ever been given.
- `reading_time_minutes` is computed, never stored: `max(1, round(word_count / 250))` over `body_markdown`.
- `author_name` is a plain string. If omitted on create it defaults to the site's `title`.

**Member**

```json
{
  "id": "e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b",
  "site_id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d",
  "email": "dev@example.com",
  "status": "free",
  "created_at": "2026-09-10T10:02:30.000Z"
}
```

`status` is always `"free"`. Emails are trimmed and lowercased before storage and comparison everywhere in this API (users and members).

## Endpoints

Protected routes require `Authorization: Bearer <token>` and return the standard `401` when it is missing or invalid. "Public" routes ignore the header entirely.

---

### GET /health

**Purpose:** Liveness check; also tells QA which Ask me mode the server is in.
**Auth:** public
**Request body:** none
**Response:** `200`

```json
{ "status": "ok", "fts5": true, "answer_mode": "search" }
```

**Notes:** `fts5` is `false` when the backend fell back to `LIKE` search. `answer_mode` is `"answer"` when `process.env.ANTHROPIC_API_KEY` was set at startup, else `"search"`.

---

### POST /auth/signup

**Purpose:** Create a writer account and sign them in.
**Auth:** public
**Request body:**

```json
{ "email": "maya@fieldnotes.blog", "password": "compost-2026" }
```

**Response:** `201`

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": "6f1c2e1a-9d3b-4c6e-8a7f-1b2c3d4e5f60", "email": "maya@fieldnotes.blog", "created_at": "2026-09-10T09:12:44.000Z" },
  "site": null
}
```

**Error responses:**
- `400` `{ "error": "validation_error", "message": "Email must be a valid address and password at least 8 characters." }` — missing/invalid email, or password shorter than 8 characters.
- `409` `{ "error": "email_taken", "message": "An account with that email already exists." }` — the message must contain the word "already" (QA asserts on it).

**Notes:** Passwords are hashed with `bcryptjs`. `site` is always `null` here because a new writer has no site yet; the frontend routes to `/admin/setup`.

---

### POST /auth/login

**Purpose:** Sign in an existing writer.
**Auth:** public
**Request body:**

```json
{ "email": "maya@fieldnotes.blog", "password": "compost-2026" }
```

**Response:** `200` — same shape as signup. `site` is the writer's Site or `null` if they have not created one.

```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": { "id": "6f1c2e1a-9d3b-4c6e-8a7f-1b2c3d4e5f60", "email": "maya@fieldnotes.blog", "created_at": "2026-09-10T09:12:44.000Z" },
  "site": { "id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d", "slug": "field-notes", "title": "Field Notes", "description": "Essays on soil and weather", "accent_color": "#1f6f43", "created_at": "2026-09-10T09:14:02.000Z", "updated_at": "2026-09-10T09:14:02.000Z" }
}
```

**Error responses:**
- `400` `{ "error": "validation_error", "message": "Email and password are required." }`
- `401` `{ "error": "invalid_credentials", "message": "Invalid email or password." }` — same response for unknown email and wrong password; the message must contain "Invalid".

**Notes:** The frontend routes to `/admin` when `site` is non-null and to `/admin/setup` when it is `null`.

---

### GET /auth/me

**Purpose:** Restore a session on reload: who am I and do I have a site.
**Auth:** required
**Request body:** none
**Response:** `200`

```json
{
  "user": { "id": "6f1c2e1a-9d3b-4c6e-8a7f-1b2c3d4e5f60", "email": "maya@fieldnotes.blog", "created_at": "2026-09-10T09:12:44.000Z" },
  "site": null
}
```

**Error responses:** `401` standard.
**Notes:** Log out is client-side only (delete the stored token). There is no `/auth/logout` route.

---

### POST /me/site

**Purpose:** Create the signed-in writer's site.
**Auth:** required
**Request body:**

```json
{ "title": "Field Notes", "description": "Essays on soil and weather", "accent_color": "#1f6f43" }
```

**Response:** `201` — the Site.

```json
{ "id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d", "slug": "field-notes", "title": "Field Notes", "description": "Essays on soil and weather", "accent_color": "#1f6f43", "created_at": "2026-09-10T09:14:02.000Z", "updated_at": "2026-09-10T09:14:02.000Z" }
```

**Error responses:**
- `400` `{ "error": "validation_error", "message": "Title is required; accent_color must be a #rrggbb hex colour." }` — `title` empty or over 120 characters, `accent_color` not matching `/^#[0-9a-fA-F]{6}$/`. `description` may be empty (stored as `""`), max 500 characters.
- `409` `{ "error": "site_exists", "message": "You already have a site. Use PUT /me/site to change it." }`

**Notes:** `accent_color` is stored lowercased. Slug derived from title as described under Site.

---

### GET /me/site

**Purpose:** Fetch the signed-in writer's site (pre-fills `/admin/setup`, names the sidebar).
**Auth:** required
**Request body:** none
**Response:** `200` — the Site.
**Error responses:** `404` `{ "error": "not_found", "message": "You have not created a site yet." }`

---

### PUT /me/site

**Purpose:** Edit title, description or accent colour of the writer's site.
**Auth:** required
**Request body:** same three fields as create; all three required (the form always sends all three).

```json
{ "title": "Field Notes", "description": "Essays on soil, weather and patience", "accent_color": "#1f6f43" }
```

**Response:** `200` — the updated Site. `slug` is unchanged.
**Error responses:** `400` as on create; `404` if the writer has no site.

---

### GET /me/posts

**Purpose:** List every post on the writer's site, all statuses, for `/admin`.
**Auth:** required
**Request body:** none
**Response:** `200`

```json
{
  "posts": [
    { "id": "c7d8e9f0-1a2b-4c3d-9e4f-5a6b7c8d9e0f", "site_id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d", "title": "On mulch", "slug": "on-mulch", "excerpt": "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms.", "status": "published", "published_at": "2026-09-10T09:31:05.000Z", "author_name": "Field Notes", "reading_time_minutes": 1, "created_at": "2026-09-10T09:20:11.000Z", "updated_at": "2026-09-10T09:31:05.000Z" },
    { "id": "d8e9f0a1-2b3c-4d4e-8f5a-6b7c8d9e0f1a", "site_id": "a3b9d2f4-5c6e-4a7b-8c9d-0e1f2a3b4c5d", "title": "Compost secrets", "slug": "compost-secrets", "excerpt": "Nobody tells you the pile should smell like a forest floor.", "status": "draft", "published_at": null, "author_name": "Field Notes", "reading_time_minutes": 1, "created_at": "2026-09-10T09:18:40.000Z", "updated_at": "2026-09-10T09:18:40.000Z" }
  ]
}
```

**Error responses:** `404` if the writer has no site.
**Notes:** Post summaries (no `body_markdown`). Ordered by `created_at` descending. Only the caller's own site's posts, ever.

---

### POST /me/posts

**Purpose:** Create a post. Always created as a draft.
**Auth:** required
**Request body:**

```json
{ "title": "On mulch", "body_markdown": "Mulch is the cheapest thing you can do for soil. It shades the surface and feeds the worms.", "excerpt": "", "author_name": "Maya Ortiz" }
```

`title` required (1–200 chars). `body_markdown` required, may be an empty string. `excerpt` optional. `author_name` optional (defaults to site title).

**Response:** `201` — the full Post with `status: "draft"`, `published_at: null`.
**Error responses:**
- `400` `{ "error": "validation_error", "message": "Title is required." }`
- `404` `{ "error": "not_found", "message": "You have not created a site yet." }`

**Notes:** The frontend navigates to `/admin/posts/<id>` using the returned `id`. Slug uniqueness per site is handled by the server (`on-mulch`, then `on-mulch-2`).

---

### GET /me/posts/:id

**Purpose:** Open one post in the editor, any status.
**Auth:** required
**Request body:** none
**Response:** `200` — the full Post.
**Error responses:**
- `404` `{ "error": "not_found", "message": "Post not found." }` — no post with that id.
- `403` `{ "error": "forbidden", "message": "You do not own this post." }` — the post exists on another writer's site.

---

### PUT /me/posts/:id

**Purpose:** Save edits to title, body, excerpt or author name. Does not change status, slug or `published_at`.
**Auth:** required
**Request body:** same fields as create; `title` and `body_markdown` required, `excerpt` and `author_name` optional.

```json
{ "title": "On mulch", "body_markdown": "Mulch is the cheapest thing you can do for soil. It shades the surface, feeds the worms, and holds water through August.", "excerpt": "" }
```

**Response:** `200` — the full updated Post.
**Error responses:** `400` (empty title), `403`, `404` as above.
**Notes:** Works on published posts too (Story 15): the public page shows the new body immediately, `published_at` and `slug` are unchanged. The FTS index is refreshed if the post is published.

---

### POST /me/posts/:id/publish

**Purpose:** Move a post to `published`.
**Auth:** required
**Request body:** none (send `{}` or nothing)
**Response:** `200` — the full Post with `status: "published"` and a non-null `published_at`.
**Error responses:** `403`, `404` as above.
**Notes:** Sets `published_at` to now only if it was `null`. Idempotent: publishing an already-published post returns `200` and changes nothing. The post enters the FTS index on this call.

---

### POST /me/posts/:id/unpublish

**Purpose:** Return a post to `draft` without deleting it.
**Auth:** required
**Request body:** none
**Response:** `200` — the full Post with `status: "draft"`; `published_at` is kept as it was.
**Error responses:** `403`, `404` as above.
**Notes:** Idempotent. The post leaves the FTS index and every public surface on this call.

---

### DELETE /me/posts/:id

**Purpose:** Permanently delete a post.
**Auth:** required
**Request body:** none
**Response:** `204 No Content`
**Error responses:** `403`, `404` as above.
**Notes:** Removes the post from the FTS index. The frontend is not required to expose a delete button at MVP; the route exists so the entity has full CRUD.

---

### GET /sites/:slug

**Purpose:** Public site header: title, description, accent colour.
**Auth:** public
**Request body:** none
**Response:** `200` — the Site.

```json
{ "id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e", "slug": "traversaal-ai", "title": "Traversaal.ai", "description": "Technical insights and updates from the forefront of AI orchestration", "accent_color": "#fc654a", "created_at": "2026-09-10T08:00:00.000Z", "updated_at": "2026-09-10T08:00:00.000Z" }
```

**Error responses:** `404` `{ "error": "not_found", "message": "Site not found." }`

---

### GET /sites/:slug/posts

**Purpose:** Public home feed: published posts only, newest first.
**Auth:** public
**Request body:** none
**Response:** `200`

```json
{
  "posts": [
    { "id": "f0a1b2c3-d4e5-4f6a-8b7c-9d0e1f2a3b4c", "site_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e", "title": "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)", "slug": "self-hosting-llms-cost-benefit-framework-api-vs-on-premise", "excerpt": "Most teams compare API price per token to GPU rental and stop there. The real break-even depends on tokens per day, utilisation and the engineers you no longer have.", "status": "published", "published_at": "2026-09-10T18:42:09.000Z", "author_name": "Hamza Farooq", "reading_time_minutes": 9, "created_at": "2026-09-10T08:00:00.000Z", "updated_at": "2026-09-10T08:00:00.000Z" }
  ]
}
```

**Error responses:** `404` if the site slug does not exist.
**Notes:** Post summaries (no `body_markdown`). `WHERE status = 'published'` — no other filter. Ordered by `published_at` descending. An empty site returns `{ "posts": [] }`. Drafts must never appear here regardless of `published_at`.

---

### GET /sites/:slug/posts/:postSlug

**Purpose:** Public post page.
**Auth:** public
**Request body:** none
**Response:** `200` — the full Post (with `body_markdown`).
**Error responses:** `404` `{ "error": "not_found", "message": "Post not found." }` — for an unknown slug **and** for a post that exists but is a draft. The two cases are indistinguishable to the caller.
**Notes:** The frontend renders `body_markdown` to HTML with a sanitiser (Story 18: no `<script>` reaches the DOM).

---

### POST /sites/:slug/members

**Purpose:** Become a free member of a site with an email address. No password, no account.
**Auth:** public
**Request body:**

```json
{ "email": "dev@example.com" }
```

**Response:**
- `201` when a new member row was created:

```json
{ "member": { "id": "e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b", "site_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e", "email": "dev@example.com", "status": "free", "created_at": "2026-09-10T10:02:30.000Z" }, "already_member": false }
```

- `200` when that email is already a member of this site (idempotent; never `409`):

```json
{ "member": { "id": "e1f2a3b4-c5d6-4e7f-8a9b-0c1d2e3f4a5b", "site_id": "b2c3d4e5-f6a7-4b8c-9d0e-1f2a3b4c5d6e", "email": "dev@example.com", "status": "free", "created_at": "2026-09-10T10:02:30.000Z" }, "already_member": true }
```

**Error responses:**
- `400` `{ "error": "validation_error", "message": "Please enter a valid email address." }` — missing or not an email.
- `404` if the site slug does not exist.

**Notes:** Email is trimmed and lowercased before the uniqueness check, so `Dev@Example.com` after `dev@example.com` returns `200` with `already_member: true`. The same email may join several sites; each is its own row. The frontend shows `member-confirmation` containing "member" on `201` and an "already a member" message on `200`.

---

### POST /sites/:slug/ask

**Purpose:** Ask me. Full-text search over this site's published posts; optionally a written answer with citations.
**Auth:** public
**Request body:**

```json
{ "question": "when does self-hosting an LLM pay off?" }
```

`question` required, 1–500 characters after trimming.

**Response:** always `200` when the site exists. Shape:

```json
{
  "mode": "answer",
  "results": [
    {
      "post_id": "f0a1b2c3-d4e5-4f6a-8b7c-9d0e1f2a3b4c",
      "title": "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)",
      "slug": "self-hosting-llms-cost-benefit-framework-api-vs-on-premise",
      "excerpt": "Most teams compare API price per token to GPU rental and stop there. The real break-even depends on tokens per day, utilisation and the engineers you no longer have.",
      "snippet": "...the break-even for <mark>self</mark>-<mark>hosting</mark> arrives somewhere between 50 and 100 million tokens per day, and only if utilisation stays above 60%..."
    }
  ],
  "answer": "Self-hosting starts to pay off once you are consistently pushing tens of millions of tokens per day with steady utilisation; below that, API pricing wins because idle GPUs and the engineers who babysit them cost more than the per-token premium.",
  "citations": [
    { "post_id": "f0a1b2c3-d4e5-4f6a-8b7c-9d0e1f2a3b4c", "title": "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)", "slug": "self-hosting-llms-cost-benefit-framework-api-vs-on-premise" }
  ]
}
```

Field rules:

- `mode` is exactly `"search"` or `"answer"`.
- `results` is always present, an array of 0 to 5 items, ranked best match first, from **published posts of this site only**. Each item has exactly `post_id`, `title`, `slug`, `excerpt` (the post's stored plain-text excerpt) and `snippet` (an FTS5 `snippet()` of the matching passage, matched words wrapped in `<mark>...</mark>`; every other character HTML-escaped; `...` marks truncation). In `LIKE` fallback mode `snippet` is a ~200-character window around the first match with the same `<mark>` wrapping.
- `answer` (string) and `citations` (array) are present **only** when `mode` is `"answer"`. Every citation's `post_id` must also appear in `results`. `citations` may be an empty array if the model cited nothing; the frontend still renders the answer.
- `answer_error` (string) is present only when `mode` is `"search"` **and** the server tried to write an answer but could not. Its value must contain the phrase "could not be written", e.g. `"An answer could not be written; showing matching passages instead."`

How the server picks the mode, deterministically:

1. Run the search. If `results` is empty → `200 { "mode": "search", "results": [] }`. No `answer`, no `citations`, no `answer_error`, and the model is **never called**. This is also the response for a site with zero published posts. The frontend shows "No matches".
2. If `results` is non-empty and `process.env.ANTHROPIC_API_KEY` is unset → `mode: "search"` with `results`.
3. If `results` is non-empty and the key is set → call the model with the snippets (not whole posts), instructed to answer only from them, say when they do not cover the question, and cite by `post_id`. On success → `mode: "answer"` with `answer` and `citations` filtered to ids present in `results`.
4. If the model call fails, is refused, or exceeds the timeout (12 seconds; Story 12 allows 15 end to end) → `mode: "search"` with `results` and `answer_error`. Never a 5xx to the reader.

**Example, no match (either mode):**

```json
{ "mode": "search", "results": [] }
```

**Example, key present but the call failed:**

```json
{ "mode": "search", "results": [ { "post_id": "…", "title": "…", "slug": "…", "excerpt": "…", "snippet": "…" } ], "answer_error": "An answer could not be written; showing matching passages instead." }
```

**Error responses:**
- `400` `{ "error": "validation_error", "message": "Please enter a question." }`
- `404` if the site slug does not exist.

**Notes (informational for the backend; the contract's job is the shape):** the model is `claude-opus-5` via `@anthropic-ai/sdk` with an explicit client `timeout` in milliseconds. Do not substitute another model id. The FTS query must be built from the reader's words with FTS5 operators and quotes escaped so punctuation in a question cannot raise a syntax error; the search covers `title` and `body_markdown`. Draft content must be absent from the index at all times: a phrase that exists only in a draft returns `results: []`.

---

## Seed

The seed runs on server start and on `node server/seed.js`; it is idempotent (writer keyed by email, site by owner, posts by slug). It reads `.sprint-zero/seed/traversaal-posts.json` at run time and exits with a clear message if the file is missing. It prints the demo writer's credentials to the terminal on every run. After any run the database holds exactly:

| Item | Value |
| --- | --- |
| Demo writer email | `demo@traversaal.ai` |
| Demo writer password | `inkwell-demo` |
| Site title / slug | `Traversaal.ai` / **`traversaal-ai`** |
| Site description | `Technical insights and updates from the forefront of AI orchestration` |
| Site accent | `#fc654a` |
| Posts | 10, all `status: "published"`, `author_name: "Hamza Farooq"`, slugs taken verbatim from the seed file |

Seed `published_at` values are RFC 2822 (`Thu, 10 Sep 2026 18:42:09 GMT`) and are parsed to ISO 8601 on load. Newest is `self-hosting-llms-cost-benefit-framework-api-vs-on-premise` (10 Sep 2026); oldest is the LLM caching post (7 Sep 2026). `source_url` and `word_count` in the file are ignored. QA and the frontend rely on `GET /sites/traversaal-ai`, `GET /sites/traversaal-ai/posts` and `/s/traversaal-ai` in the browser.

## Deferred

The member feed (PRD should-have Story 17) has no endpoint in this contract. The stories want a member to open a feed by re-entering their email, which would make an email alone a credential; the PRD marks the story cuttable and the decision was to leave it out rather than add a second auth model for members. If it is added later it will be `GET /me/feed` for a signed-in user's memberships, and this file changes first. The frontend may omit the `/s/:slug/feed` route entirely; QA does not test Story 17.

## Conventions

- All request and response bodies are JSON (`Content-Type: application/json`). A body that is not valid JSON returns `400 validation_error`.
- Timestamps are ISO 8601 UTC strings with milliseconds, e.g. `"2026-09-10T09:30:00.000Z"`.
- IDs are UUID v4 strings.
- The backend never returns `owner_id`, `user_id` or `password_hash`. `site_id` on posts and members is returned.
- `POST` that creates returns `201` with the created resource. `POST` actions (publish, unpublish, ask) return `200`. `PUT` returns `200` with the updated resource. `DELETE` returns `204` with no body.
- Lists are wrapped: `{ "posts": [...] }`, `{ "results": [...] }`. Single resources are returned bare (the Site, the Post), except auth and member responses, whose shapes are given above.
- Error responses always use `{ "error": "short_code", "message": "Human readable." }` with these codes: `validation_error` (400), `unauthorized` (401, bad/missing token), `invalid_credentials` (401, login only), `forbidden` (403, not the owner), `not_found` (404), `email_taken` (409), `site_exists` (409). Unknown routes return `404 not_found`. Unexpected failures return `500 { "error": "internal_error", "message": "Something went wrong." }` — but `POST /sites/:slug/ask` never surfaces a model failure as 500.
- Emails are trimmed and lowercased on the server before storage and comparison.

## What agents must NOT do

- Do not add or remove endpoints without updating this file first.
- Do not change response shapes or rename fields. The frontend and backend engineers build against this document in parallel — shape drift breaks the build.
- Do not skip JWT middleware on any `/me/*` or `/auth/me` route.
- Do not return draft posts from any `/sites/:slug/...` route or include them in the Ask me index, under any condition.
- Do not call the model when `results` is empty, and do not return a citation whose `post_id` is not in `results`.
- Do not return 409 from `POST /sites/:slug/members` on a repeat email; it is `200` with `already_member: true`.
- Do not require `ANTHROPIC_API_KEY`, `JWT_SECRET` or any `.env` for the server to start.
- Do not add password auth, tokens or a login of any kind for members.
