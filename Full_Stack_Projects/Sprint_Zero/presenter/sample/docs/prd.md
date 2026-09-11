# Inkwell — PRD

_Built with Sprint Zero. Reference: Ghost. Level: MVP._

## 1. Problem statement

Independent writers want a place to publish that they own: a simple site with their name and colour on it, a plain editor, and a way for readers to raise a hand and say "keep me posted". Ghost does this well but arrives with a newsletter engine, payments, themes, integrations and a rich editor that a single writer starting out does not need and cannot run without a server or a subscription.

Readers have the opposite problem. Once a site has ten or twenty posts, finding the one that answers their question means scanning titles or trusting a search box that returns links. Nobody answers the question.

Inkwell is the smallest version of a writer's site that closes both gaps: one writer, one site, posts that go from draft to published, readers who become free members with an email address, and an "Ask me" box that answers a reader's question from the site's own published writing, with citations back to the posts it drew from. It runs locally with no external account, and it ships with a real demo site — the Traversaal.ai blog — so Ask me answers from real writing on first launch.

## 2. Goals

1. Enable a new writer to sign up, create a site, and publish their first post in under five minutes with no configuration.
2. Enable a reader with no account to open a site, read a published post, and become a free member in under one minute.
3. Enable a reader to ask a question in the Ask me box and get a response grounded in published posts — matching passages when no answer key is configured, a written answer with citations when one is — within a few seconds.
4. Ship a demo site seeded with ten real Traversaal.ai articles so that the first Ask me question on a fresh install returns a real, cited result.
5. Keep every draft private: zero draft content reachable from the public site or from Ask me.

## 3. Non-goals

This build explicitly will not include any of the following, per `docs/scope.md`:

- Paid tiers, Stripe, or any payments
- Static pages (only posts)
- Tags and collections
- Multiple newsletters
- Theme upload or a theme marketplace (one built-in theme, coloured by the site's accent colour)
- Integrations, webhooks, Zapier
- Comments
- Recommendations
- Multiple staff users and roles (one owner per site)
- Custom domains
- Real email sending (published posts appear in a member's in-app feed instead)
- Analytics and post stats
- SEO settings and code injection
- A rich text editor (plain textarea; markdown rendering optional)
- Embeddings or a vector database (keyword full-text search only for retrieval)

Also out of scope at this level, though Ghost does them: scheduled and email-only posts, members-only or paid-only post visibility, passwordless magic-link sign-in for members, feature images and image galleries, author profile pages, post revisions and autosave, preview modes, announcement bar, private (password-protected) sites, content export, and the fediverse features.

## 4. Users & use cases

**Maya, a writer.** Maya has been posting long essays on a social network and wants them on a site with her name on it. She signs up with her email and a password, names her site "Field Notes", writes a two-line description, picks a dark green accent, and lands in a plain editor with a title field and a body box. She writes for an hour, closes the tab, comes back the next morning still logged in, finishes the piece, and presses Publish. Her post is now at a public address she can share. Her posts list shows it labelled Published, next to two others still labelled Draft that nobody but her can see.

**Dev, a reader.** Dev follows a link to Maya's post on his phone. He has no account and is not asked for one. He reads the essay in a single clean column, and at the bottom there is an email box that says "Sign up for more like this." He types his email and is told he is now a member. When he comes back to the site later, he can open his member feed and see any new posts Maya has published since.

**Priya, a reader with a question.** Priya opens the demo site, which is the Traversaal.ai blog with ten technical articles. Rather than reading all of them she types "when does self-hosting an LLM pay off?" into the Ask me box. On a fresh install with no answer key configured, she gets back the passages from the posts that match her question, clearly labelled as search results, each linking to its post. On an install where the operator has configured an Anthropic API key, she gets a short written answer followed by citations to the posts it drew on. When she asks about something the blog has never covered, she is told nothing matched, not given a guess.

## 5. User stories

### Must-have

**Authentication (writers)**

1. As a new writer, I want to sign up with email and password so that I can access the product.
2. As a returning writer, I want to log in so that I can see my own site and posts.
3. As a signed-in writer, I want my session to persist across reloads so that I don't have to log in every time.
4. As a signed-in writer, I want to log out so that my session ends.

**Core loop**

5. As a signed-in writer, I want to create my site with a title, description and accent colour so that readers see a site that is recognisably mine.
6. As a writer, I want to write a post with a title and body and have it saved as a draft so that I can work on it before anyone sees it.
7. As a writer, I want to publish a draft so that it appears on my public site immediately.
8. As a writer, I want my drafts to stay private so that no reader, and no Ask me question, can reach unfinished writing.
9. As a reader, I want to visit a public site and read its published posts without an account so that there is nothing between me and the writing.
10. As a reader, I want to become a free member by entering my email so that I am connected to the site without creating a password.
11. As a reader, I want to ask the site a question in the Ask me box and, when no answer key is configured, get the matching passages from published posts labelled as search results so that I can find what the site has said about my topic.
12. As a reader, I want to ask the site a question and, when an answer key is configured, get a written answer with citations to the published posts it came from, and no answer at all when nothing matched, so that I can trust what I am told.
13. As a person evaluating the product, I want a fresh install to come with a demo writer whose site is the Traversaal.ai blog, loaded from the seed file, so that the demo answers from real writing rather than placeholder text.

### Should-have

14. As a writer, I want to see all my posts in one list, each labelled Draft or Published, so that I know what is live.
15. As a writer, I want to edit a post after it is published so that I can fix mistakes.
16. As a writer, I want to unpublish a post back to draft so that I can take something down without deleting it.
17. As a member, I want an in-app feed of the site's published posts so that I can catch up on what I have missed (this replaces email delivery, which is excluded).
18. As a reader, I want post bodies written in markdown to render as formatted text so that headings, links and lists read properly.

### Nice-to-have

Ghost features that are out of scope at this level but worth noting for a later pass:

19. As a writer, I want to schedule a post for a future date so that it publishes while I am away.
20. As a writer, I want to mark a post as members-only so that only free members can read it.
21. As a writer, I want to add a feature image to a post so that the home feed has visual variety.
22. As a writer, I want to preview a post as a reader would see it before publishing.
23. As a member, I want to sign back in by email link so that I can manage my membership from any device.

## 6. Acceptance criteria

This is an MVP build: every criterion below describes real data that survives a restart, and the full sign-up, log-in, reload, log-out dance on the core loop.

**Story 1 — Sign up**
- Given I am on the sign-up screen, when I enter a valid email and a password and submit, then an account is created, I am signed in, and I land on the site-setup screen.
- Given an account already exists with that email, when I try to sign up with it again, then I am told the email is taken and no second account is created.

**Story 2 — Log in**
- Given I have an account, when I enter my email and correct password, then I am signed in and see my own site and posts, not anyone else's.
- Given I enter a wrong password, when I submit, then I am told the credentials are invalid and I remain signed out.

**Story 3 — Session persistence**
- Given I am signed in, when I reload the page or close and reopen the tab, then I am still signed in and my site and posts are shown without logging in again.

**Story 4 — Log out**
- Given I am signed in, when I click Log out, then I am returned to the public or sign-in screen, and reloading does not restore my session.
- Given I have logged out, when I try to open the writer's admin screens directly, then I am sent to the sign-in screen.

**Story 5 — Create a site**
- Given I am a signed-in writer with no site yet, when I enter a title, a description and an accent colour and save, then the site is created, I am its owner, and the public site uses those three values (title in the header and cover, description under it, accent colour on the cover, links and buttons).
- Given I already have a site, when I return to the setup screen, then I see my existing values and can change them, and I cannot create a second site.

**Story 6 — Write a draft**
- Given I am a signed-in writer with a site, when I click New post, enter a title and body and save, then the post is stored as a draft, is labelled Draft in the editor, and appears in my posts list as Draft.
- Given a draft exists, when I reopen it later, then the saved title and body are exactly as I left them.

**Story 7 — Publish**
- Given I have a draft, when I click Publish, then its status becomes Published, its published date is set to now, the editor label changes to Published, and the post is visible on the public home feed and at its own public address.
- Given a post is published, when a reader opens the home page, then the post appears in the feed with its title, excerpt, author, date and reading time.

**Story 8 — Drafts stay private**
- Given a post is a draft, when anyone visits the public home feed, then it does not appear.
- Given a post is a draft, when anyone requests its public address directly, then they get a not-found response, not the post.
- Given a post is a draft whose body contains an unusual phrase, when a reader asks that phrase in Ask me, then no passage from the draft is returned in either mode.

**Story 9 — Read without an account**
- Given I am a visitor with no account and no session, when I open the site's home page, then I see the site title, description and accent colour, and a feed of published posts.
- Given I click a post, when the post page loads, then I see its title, excerpt, byline (author, date, reading time) and full body in a single reading column, with no sign-in required.

**Story 10 — Become a free member**
- Given I am reading a post, when I enter my email in the "Sign up for more like this" box and submit, then a free member is recorded for this site with my email and I see a confirmation that I am now a member.
- Given I submit the same email again, when the form submits, then I am told I am already a member and no duplicate is created.
- Given I submit something that is not an email address, when the form submits, then I am asked for a valid email and nothing is recorded.
- Membership never requires a password or an account; the email alone is enough.

**Story 11 — Ask me without an answer key**
- Given the site has published posts and no Anthropic API key is configured (the ANTHROPIC_API_KEY environment variable is absent), when I type a question into Ask me and submit, then I receive the passages from published posts that match my words, each showing its post title and linking to the post, and the results are clearly labelled as search results, not an answer.
- Given my question matches no published post, when I submit, then I see a "no matches" message and no passages.
- Given the operator has done no configuration of any kind, when the app starts, then Ask me works in this mode by default.

**Story 12 — Ask me with an answer key**
- Given an Anthropic API key is configured and my question matches one or more published posts, when I submit, then I receive a written answer composed from those posts, followed by citations that name and link each post it drew from.
- Given my question matches no published post, when I submit, then I see the same "no matches" message as Story 11 and no written answer is produced — the assistant is never asked to answer from nothing.
- Given the answer service fails or times out, when I submit, then I still see the matching passages as search results with a note that an answer could not be written.

**Story 13 — Seeded demo site**
- Given a fresh install, when the seed script runs, then it creates one demo writer with a known email and password and one site whose title, description and accent colour come from the seed file's `site` object (`title`, `description`, `accent_color`), and it loads every post in that file as a published post using each entry's `title`, `slug`, `author`, `published_at`, `excerpt` and `body_markdown`.
- Given the seed has run, when I open the demo site, then I see ten published Traversaal.ai posts in the feed, and asking Ask me a question about their subject matter returns cited results.
- Given the seed script is run a second time, when it completes, then there are still exactly ten posts and one demo writer, not duplicates.
- The seed file is `.sprint-zero/seed/traversaal-posts.json`; the script reads it rather than embedding article text.

### Design direction

The public site follows Ghost's Casper theme, not ghost.org's marketing pages. Text `#15171a`, secondary text `#979797`, borders `#e1e1e1`, white background, black footer; the site's accent colour paints the cover block, the header on inner pages, links inside post bodies, and the pill-shaped Subscribe button (48px radius). Headings and UI chrome use the system sans-serif stack at weight 800; post body text is Georgia at 20px. Home page: an 88px header (wordmark left, Sign in and Subscribe right), an accent cover with the site title and description in white, then a 1200px post feed with one large lead card and two-column cards below. Post page: a 720px reading column with title, excerpt, byline, body, then the "Sign up for more like this." email box. The writer's admin follows Ghost's Shade look: white, one left sidebar, 13px UI text, black primary buttons with 4–6px radius, and a two-field editor (title, body) on a centred white column with a Publish button and a Draft/Published label. Ask me can reuse the shell of Ghost's search modal (white, 512px, 8px radius) but shows a paragraph with cited links, or labelled passages, instead of a plain list. Full measurements are in `.sprint-zero/design/ghost-tokens.md`.

## 7. Risks & assumptions

**Risks**

- Keyword search is literal. SQLite full-text search matches the words a reader typed; a question phrased differently from the article ("cost of running my own model" vs "self-hosting") may return nothing. The "no matches" state must be honest rather than padded.
- Answer quality depends on retrieval. With a key present, Claude only sees the passages the full-text search returned, so a weak match yields a thin answer. Returning citations makes this visible rather than hidden.
- The Anthropic API is an external dependency in answer mode: cost per question, latency of a few seconds, and outages. The fallback to labelled search results (Story 12, third criterion) is what keeps the demo working when it fails.
- Draft leakage is the highest-consequence bug. Every public read path and the Ask me index must filter to published status; a single missed filter exposes unfinished writing.
- Seed dates: the seed file's `published_at` values are in RFC 2822 format (e.g. `Thu, 10 Sep 2026 18:42:09 GMT`) and must be parsed rather than stored as-is, or ordering and display will be wrong.
- The seed file's posts carry `source_url` and `word_count` fields that the product does not need; ignoring them is fine, but the schema should not fail on their presence.

**Assumptions**

- `[ASSUMPTION]` One writer owns exactly one site, and one install may hold many sites; a reader who follows a link always lands on the right site. How multiple sites are addressed publicly (by path or otherwise) is a decision for the API contract.
- `[ASSUMPTION]` Members belong to a site, not to the install; the same email can be a member of several sites.
- `[ASSUMPTION]` Membership is recorded on submit with no confirmation step, since email sending is excluded.
- `[ASSUMPTION]` A member's in-app feed is reached by entering the same email again; no password or link is involved. This is a should-have and may be cut.
- `[ASSUMPTION]` The demo writer's login is printed by the seed script so an evaluator can sign in as the Traversaal.ai owner.
- `[ASSUMPTION]` Reading time is computed from word count at roughly 250 words per minute, matching Ghost's convention.
- `[ASSUMPTION]` Excerpts are stored explicitly (the seed provides them) and, for new posts, fall back to the first sentences of the body when the writer leaves the field empty.

## 8. Open questions

- Should Ask me accept questions on a site that has zero published posts, or should the box be hidden until the first post is live?
- When a writer unpublishes a post (should-have), should its published date be cleared or kept for re-publishing?
- Does the writer's admin need a member count or member list at MVP, given analytics are excluded? A plain list of emails is cheap; a count alone may be enough.

## 9. Success metrics

**Leading indicators**

- A fresh clone reaches a published post on a brand-new site (sign up, create site, write, publish, view publicly) in one uninterrupted run with no configuration.
- The first Ask me question on the seeded demo returns at least one cited result in both modes (no key: labelled passages; key: written answer with citations).
- Zero draft content appears in any public response or Ask me result across the QA run.

**Lagging indicators**

- The full core loop (writer publishes, reader reads, reader becomes member, reader asks and receives a cited response) passes end to end in a real browser, with the session surviving reload and ending on log-out.
- Every must-have acceptance criterion above has a passing check in the QA report.
