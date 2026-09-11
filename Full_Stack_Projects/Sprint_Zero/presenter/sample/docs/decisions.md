# Decisions

_Sprint Zero build (Inkwell) compared to Ghost. Level: MVP._

## Why this document exists

We built Inkwell, the smallest version of a writer's site that closes one loop end to end: a writer signs up, creates a site, writes a post and publishes it; a reader visits with no account, reads it, becomes a free member with an email address, and asks the site a question in an "Ask me" box that answers from the site's own published writing with citations. We compared it against Ghost, the open-source publishing platform, whose feature inventory is in `docs/reference-brief.md`.

Ghost is a mature product with 95 database tables, a newsletter engine, payments, a theme marketplace and a rich editor. At MVP level we keep real login and real data on the core loop and cut everything that is not on that loop. The cuts below are deliberate. Each one names what Ghost does, what we do instead, and why the build level or the core loop in `docs/scope.md` justifies it. Ask me is our addition; Ghost has no equivalent, and its technical choices are recorded here because the build agents read this file.

## Scope decisions

### Site settings are a table, not key/value rows

- **Reference does:** One Ghost install is one publication. Title, description and accent colour live as rows in a `settings` table; there is no "site" object.
- **We chose to:** Make `sites` a first-class table (title, description, accent colour, owner) because one Inkwell install hosts many sites, one per writer.
- **Reason:** The core loop starts with "a writer creates a site". Many writers on one install means the site needs its own row with an owner, which Ghost never had to model.

### One owner per site, no staff roles

- **Reference does:** Owner, Administrator, Editor, Author and Contributor roles, with invites by email and per-plan staff caps.
- **We chose to:** One writer owns exactly one site. No invites, no roles.
- **Reason:** Listed in the scope excludes. The core loop has one writer; roles only matter once a second person needs access.

### Two post states: draft and published

- **Reference does:** Four statuses: draft, published, scheduled and sent (email-only), with scheduling rules.
- **We chose to:** Draft and published only. Publishing sets the published date to now; unpublishing returns the post to draft.
- **Reason:** MVP covers the draft-to-published transition on the core loop. Scheduling and email-only posts depend on a scheduler and an email pipeline we are not building.

### Plain textarea instead of a rich editor

- **Reference does:** A Lexical-based editor with cards for images, galleries, embeds, callouts, code, paywalls, autosave and revision history.
- **We chose to:** A title field and a plain body textarea. Markdown rendering on the public side is optional.
- **Reason:** Listed in the scope excludes. The loop needs a title and a body to publish; a rich editor is weeks of work that does not change whether the loop works.

### No post settings panel

- **Reference does:** A sidebar for slug, publish date, tags, access level, custom excerpt, authors, template, featured flag, metadata, canonical URL, social cards and code injection.
- **We chose to:** Slug is generated from the title. Excerpt is stored and falls back to the first sentences of the body. Nothing else is editable.
- **Reason:** Every field in that panel belongs to a feature we cut (tags, gating, SEO, code injection). Slug and excerpt are the two that the public page and Ask me need.

### No preview modes

- **Reference does:** Preview a post as desktop, mobile, email or social card, and as visitor, free member or paid member.
- **We chose to:** No preview. The writer publishes and views the public page.
- **Reason:** MVP covers the core loop only. With one visibility level and no email, there is one rendering to preview and the public page already shows it.

### Posts only, no pages

- **Reference does:** A second post type, `page`, for About and Contact style content, excluded from feeds.
- **We chose to:** Posts only.
- **Reason:** Listed in the scope excludes. The site description on the cover does the job an About page would do at this level.

### No tags or collections

- **Reference does:** Tags with public or internal visibility, tag archive pages, and curated collections.
- **We chose to:** No tags, no collections. The home feed is every published post, newest first.
- **Reason:** Listed in the scope excludes. With ten to twenty posts a flat feed is enough; Ask me covers "find the post about X".

### No author pages

- **Reference does:** Public author profiles with avatar, bio and archive.
- **We chose to:** Author name appears in the byline only.
- **Reason:** One owner per site means the author page would duplicate the home page.

### One built-in theme coloured by the accent

- **Reference does:** Handlebars themes, two shipped in the repo, upload of custom zips, and a marketplace of hundreds.
- **We chose to:** One built-in Casper-style theme. The site's accent colour paints the cover, header, links and Subscribe pill.
- **Reason:** Listed in the scope excludes. A theme engine is a product in itself; the accent colour delivers the "recognisably mine" feeling the core loop asks for.

### Members join on submit, no magic link

- **Reference does:** Passwordless membership by emailed magic link or one-time code; "Now check your email!" confirmation step.
- **We chose to:** A reader enters an email in the "Sign up for more like this" box and is a member immediately. No password, no confirmation email. Members are keyed by (site, email).
- **Reason:** Real email sending is in the scope excludes, so a magic link has nowhere to go. The loop needs "reader becomes a free member with their email", which this delivers in one step.

### No Portal modal

- **Reference does:** An embedded membership modal with a floating button, deep links, tier selection, signup terms and an account page.
- **We chose to:** The inline post-footer email box. A modal is optional.
- **Reason:** MVP covers one signup path. The inline box is Ghost's own simplest pattern and needs no separate app.

### Free members only, no paid tiers

- **Reference does:** Stripe Connect, monthly and yearly prices, tiers, benefits, complimentary access, gifts, tips and offers.
- **We chose to:** Free membership only. No payments of any kind.
- **Reason:** Listed in the scope excludes. Payments are the largest single dependency in Ghost and sit entirely off the core loop.

### In-app feed replaces email newsletters

- **Reference does:** Posts can be emailed to all members or a segment, across multiple newsletters, via Mailgun with open and click tracking.
- **We chose to:** A member's in-app feed lists the site's published posts. No email leaves the system.
- **Reason:** Real email sending and multiple newsletters are both in the scope excludes. The feed keeps the "member sees new posts" promise without an email provider.

### All published posts are public

- **Reference does:** Post visibility of public, members-only, paid-only or specific tiers, enforced on the server with a paywall marker.
- **We chose to:** Every published post is public. The only filter is draft versus published.
- **Reason:** MVP reproduces exactly the two filters that matter (status is published, and there is no gating). Gating needs tiers and member sign-in we cut.

### Ask me replaces site search

- **Reference does:** A client-side search modal over post titles and excerpts, returning links. No question answering.
- **We chose to:** An Ask me box that runs full-text search over the complete body of published posts and returns matching passages, or a written answer with citations when an answer key is configured.
- **Reason:** This is the core loop's addition, not a cut. It is specced as new behaviour because Ghost has nothing like it. Technical choices are below.

### No comments

- **Reference does:** Member comments under posts with likes, replies, reports and moderation.
- **We chose to:** No comments.
- **Reason:** Listed in the scope excludes. Comments need moderation tooling that belongs well beyond the core loop.

### No recommendations or fediverse

- **Reference does:** Publishers recommend other Ghost sites; readers one-click subscribe; Ghost 6 publishes to and follows the fediverse.
- **We chose to:** Neither.
- **Reason:** Recommendations are in the scope excludes; the fediverse features depend on ActivityPub infrastructure far outside an MVP.

### No analytics

- **Reference does:** A dashboard of member counts and growth, post analytics, email rates, web analytics via Tinybird, and a per-member activity feed.
- **We chose to:** No stats. Whether the admin shows even a member count is an open question in the PRD.
- **Reason:** Listed in the scope excludes. Analytics needs event tables and a time-series store; the loop is complete without knowing how it performed.

### No integrations, webhooks or Zapier

- **Reference does:** Custom integrations with API keys, webhooks on post and member events, built-in Slack and Unsplash, thousands of Zapier connections.
- **We chose to:** None.
- **Reason:** Listed in the scope excludes. Integrations presuppose an audience of other systems; the loop has one writer and one reader.

### No custom navigation or announcement bar

- **Reference does:** Editable primary and secondary menus stored as settings, and a site-wide announcement banner.
- **We chose to:** Fixed header: wordmark, Sign in, Subscribe.
- **Reason:** MVP covers one theme with fixed chrome. Menus only earn their place once there are pages and tags to link to, both of which are cut.

### No SEO settings or code injection

- **Reference does:** Meta title and description, canonical URL, Open Graph and X cards, sitemap, structured data, site-wide and per-post head/foot HTML.
- **We chose to:** Plain HTML with the post title in the page title. Nothing injectable.
- **Reason:** Listed in the scope excludes. These matter once a site competes for search traffic, which is not the loop we are proving.

### No custom domains

- **Reference does:** Free custom domain with SSL on hosted plans; Let's Encrypt for self-hosters.
- **We chose to:** Sites are addressed within one install. How a site is addressed publicly (by path or otherwise) is decided in the API contract.
- **Reason:** Listed in the scope excludes. The build runs locally; there is no domain to point.

### No member import, export, labels or content export

- **Reference does:** CSV import and export of members, labels for segmentation, and a full JSON content export.
- **We chose to:** None. Members are created one at a time from the public site.
- **Reason:** MVP covers the loop, not migration in or out of it. Labels depend on segmentation for email, which is cut.

### No private sites or internationalisation

- **Reference does:** Password-protect an entire site; translate Portal, search and comments by locale.
- **We chose to:** Every site is public and in English.
- **Reason:** Both sit off the core loop, and the embedded apps they translate (Portal, comments) are cut.

### No feature images

- **Reference does:** A feature image per post, shown wide on the post page and on feed cards, with wide and full-bleed styles.
- **We chose to:** Text-only posts and cards.
- **Reason:** Images need upload, storage and resizing. The loop is complete without them, and the Casper layout still reads well as text.

### No admin toolbar

- **Reference does:** Staff see a floating toolbar on the live site linking to admin, edit and analytics.
- **We chose to:** The writer navigates between admin and public site through the header.
- **Reason:** A convenience layered over analytics we cut. MVP covers the loop, not the shortcuts around it.

## Technical decisions

### Stack: React (Vite) frontend, Express backend, local SQLite with self-issued JWT

- **We chose:** The `web-app` project type on the `node-react` profile with the `local` data layer, as `docs/scope.md` specifies. React + Vite in `client/` on port 5173, Express in `server/` on port 3001, a single `better-sqlite3` database file at `server/data.db`, and writer login by email and password with a self-issued JWT signed by a secret that defaults to a baked-in dev value.
- **Reason:** The core loop must run with zero configuration. A local SQLite file needs no account, no `.env` and no network, so a fresh clone reaches a published post in one uninterrupted run. Sprint Zero ships from a small catalog of profiles so the build stays predictable.

### Sites are a first-class table

- **We chose:** A `sites` table with `id`, `owner_id`, `title`, `description`, `accent_color` and timestamps. Each writer owns exactly one site; posts and members carry a `site_id`.
- **Reason:** Ghost keeps site settings as key/value rows in a `settings` table because one Ghost install is one site. Inkwell hosts many sites on one install, so the site needs its own row with an owner. Every public read and every Ask me query is scoped by `site_id`.

### Members are keyed by (site, email) with no password

- **We chose:** A `members` table separate from the writers' `users` table, with a unique constraint on (`site_id`, `email`), a `status` of `free`, and no password column. The same email may be a member of several sites.
- **Reason:** Ghost keeps members and staff as two identity systems so the public site never exposes staff auth; we keep that split. Membership is one email submit because email sending is excluded and a password would turn readers into account holders, which the core loop does not ask for.

### Ask me retrieval: SQLite FTS5

- **We chose:** An FTS5 table over published posts' `title` and `body`, built as an external-content (or contentless) table against the `posts` table, kept in sync by triggers on insert, update and delete, or by re-indexing on publish and unpublish. The index only ever contains posts whose status is published; a draft is removed from it the moment it stops being published. Queries return matching passages (via FTS5 `snippet()` or `highlight()`) grouped by post, each carrying the post id, title and slug.
- **Reason:** The scope excludes embeddings and vector databases, so keyword full-text search is the retrieval layer. FTS5 needs no configuration, no separate process and no network; it ships inside the same `better-sqlite3` database file as everything else, so the zero-setup promise holds.
- **Check the backend must do:** On startup, confirm the SQLite bundled with `better-sqlite3` has FTS5 compiled in (current releases do) by attempting to create the FTS5 table or by reading `PRAGMA compile_options`. If FTS5 is missing, fall back to a `LIKE`-based search over `title` and `body` of published posts, and log the fallback clearly so anyone reading the terminal knows retrieval is degraded. Never fail startup over it.

### Ask me answer synthesis: Claude through the official Node SDK

- **We chose:** When `process.env.ANTHROPIC_API_KEY` is set, the backend calls Claude through `@anthropic-ai/sdk` with model id `claude-opus-5` to write an answer from the passages FTS5 returned. The key is optional and never required; the app starts and Ask me works without it. When no key is set, Ask me returns the matching passages labelled as search results. When the key is set but the search matched nothing, the model is not called at all and the reader sees the same "no matches" message.
- **Prompt rules:** The prompt must instruct the model to answer only from the supplied passages, to say when the passages do not answer the question, and to cite by post id so the backend can attach title and link to each citation. The passages, not the whole posts, are what the model sees.
- **Failure handling:** A failed, refused or timed-out call degrades to the passages response with a note that an answer could not be written. It never returns an error to the reader. Set an explicit request timeout on the SDK client (the Node SDK takes it in milliseconds) so a slow call cannot hang the request.
- **Reason:** The core loop says Ask me uses Claude when a key is present and returns passages when it is not. Keeping the key optional preserves zero-setup; keeping the fallback keeps the demo working through an outage. The PRD names the external API as a risk and this decision is the mitigation. Do not substitute another model id.

### Seed: the real Traversaal.ai blog, loaded idempotently

- **We chose:** The seed script reads `.sprint-zero/seed/traversaal-posts.json` at run time rather than embedding article text. It creates one demo writer with a known email and password (printed by the script), one site from the file's `site` object (`title`, `description`, `accent_color`), and every entry in `posts` as a published post using `title`, `slug`, `author`, `published_at`, `excerpt` and `body_markdown`. The script is idempotent: posts are keyed by `slug` and the writer by email, so re-running updates or skips rather than duplicating. After any run there are exactly ten posts and one demo writer.
- **Details the seed must respect:** `published_at` values are RFC 2822 strings (for example `Thu, 10 Sep 2026 18:42:09 GMT`) and must be parsed to a stored timestamp, not copied as text, or ordering and display break. The entries also carry `source_url` and `word_count`, which the product ignores and the schema must not choke on. Seeding published posts must also populate the FTS5 index.
- **Reason:** The core loop says seed content is real so Ask me answers from real writing on first launch. Idempotency comes from the `local` data layer's rule that seed runs on start and on demand without side effects.

### Publishing rules copied from Ghost

- **We chose:** On the draft-to-published transition, set `published_at` to now if it is empty. Unpublish returns the post to draft. Every public read path and the Ask me index filter to `status = 'published'` and nothing else.
- **Reason:** The reference brief flags these as the rules worth reproducing exactly. Draft leakage is the highest-consequence bug in the PRD, and one filter applied everywhere is the defence.

### Testing: Playwright via MCP

- **We chose:** Playwright driven by the QA sub-agent through the Playwright MCP, against the resolved ports (5173 and 3001).
- **Reason:** Browser-driven tests catch the real user journey, including the login and session dance across reload and log-out. MCP means the agent drives the browser without us wiring a test framework by hand. The QA run must include the draft-leak check from the PRD (an unusual phrase in a draft never appears in the public feed, at its address, or in either Ask me mode) and both Ask me modes.

### Build level: MVP

- **We chose:** MVP.
- **Reason:** The goal in `docs/scope.md` is real login and real data on one core loop, end to end. A clickable build could not prove that Ask me answers from real stored posts, and Prod-level hardening would spend effort on error paths before the loop itself is proven.

## What we'd add next

1. **Members-only posts.** A `visibility` column and a member sign-in by email link. It restores the one Ghost feature that makes membership mean something, and the two-table split is already in place for it.
2. **Markdown rendering on the public page.** Small, high-value: the seeded Traversaal.ai posts are markdown and read far better with headings, links and code blocks. Listed as optional in scope; make it default.
3. **Scheduled publishing.** A `scheduled` status and a small interval check on the server. Low effort on top of the existing publish rules, and the most-asked-for editor feature after images.
4. **Feature images.** Local file upload to a `server/uploads` folder and one image per post. The Casper layout has a slot waiting for it.
5. **A member list in the admin.** A plain list of emails per site, cheap to build, and the first thing a writer asks for once readers start joining.
