# User stories

_Level: MVP. Expanded from `docs/prd.md`._

Data-testid values named below are the contract between the frontend and QA. The frontend must use them exactly; Playwright finds elements by them. The first eight (`hero-cta-signup`, `nav-login`, `go-to-signup`, `email-input`, `password-input`, `signup-button`, `login-button`, `logout-button`) are fixed by the kit's QA agent and must not be renamed. Writer admin screens live under `/admin`; the sign-up and log-in screens are `/signup` and `/login`; a site's public pages are reached at the public path the API contract assigns to it (written below as "the site's public home page" and "the post's public address").

## Must-have

### Story 1 — Sign up with email and password

**Story:** As a new writer, I want to sign up with email and password so that I can access the product.

**Acceptance criteria:**

- Given I am on the landing page, when I click `hero-cta-signup` (or `nav-login` then `go-to-signup`), then the URL is `/signup` and `email-input`, `password-input` and `signup-button` are visible.
- Given I am on `/signup`, when I fill `email-input` with an unused email and `password-input` with a password of at least 8 characters and click `signup-button`, then a session is created, the URL becomes `/admin/setup` (the site-setup screen), and `logout-button` is visible.
- Given an account already exists for that email, when I submit `/signup` with the same email, then an error message containing "already" is shown, the URL stays `/signup`, and logging in with the original password still works (no second account was created).
- Given I submit `/signup` with an empty email or an empty password, when I click `signup-button`, then a validation message is shown and no request succeeds.

**Priority:** Must-have
**Effort:** Small

### Story 2 — Log in with email and password

**Story:** As a returning writer, I want to log in so that I can see my own site and posts.

**Acceptance criteria:**

- Given I am signed out on the landing page, when I click `nav-login`, then the URL is `/login` and `email-input`, `password-input` and `login-button` are visible.
- Given I have an account with a site, when I fill `email-input` and `password-input` with correct credentials and click `login-button`, then the URL becomes `/admin` and the posts list shows only posts whose site I own (a second writer's post titles never appear).
- Given I have an account but no site yet, when I log in, then the URL becomes `/admin/setup`.
- Given I enter a correct email and a wrong password, when I click `login-button`, then a message containing "Invalid" is shown, the URL stays `/login`, and `logout-button` is not present.

**Priority:** Must-have
**Effort:** Small

### Story 3 — Session persists across reload

**Story:** As a signed-in writer, I want my session to persist across reloads so that I don't have to log in every time.

**Acceptance criteria:**

- Given I am signed in and on `/admin`, when I reload the page, then I remain on `/admin`, my posts list is shown, and `logout-button` is visible without any log-in form appearing.
- Given I am signed in, when I close the tab and open `/admin` in a new tab of the same browser context, then I am still signed in and my site title is shown in the admin sidebar.
- Given I am signed in and viewing a draft in the editor, when I reload, then the same draft is open with the saved title and body.

**Priority:** Must-have
**Effort:** Small

### Story 4 — Log out

**Story:** As a signed-in writer, I want to log out so that my session ends.

**Acceptance criteria:**

- Given I am signed in on any `/admin` page, when I click `logout-button`, then the URL becomes `/login` (or the landing page) and `nav-login` is visible.
- Given I have logged out, when I reload the page, then I am still signed out: `logout-button` is absent and `nav-login` is visible.
- Given I have logged out, when I navigate directly to `/admin` or `/admin/posts/new`, then I am redirected to `/login`.

**Priority:** Must-have
**Effort:** Small

### Story 5 — Create a site

**Story:** As a signed-in writer, I want to create my site with a title, description and accent colour so that readers see a site that is recognisably mine.

**Acceptance criteria:**

- Given I am a signed-in writer with no site, when I open `/admin/setup`, then `site-title-input`, `site-description-input`, `site-accent-input` and `create-site-button` are visible.
- Given I fill `site-title-input` with "Field Notes", `site-description-input` with "Essays on soil and weather" and `site-accent-input` with `#1f6f43`, when I click `create-site-button`, then the URL becomes `/admin`, the sidebar shows "Field Notes", and I am recorded as the site's owner.
- Given the site exists, when I open its public home page, then the header wordmark and cover heading read "Field Notes", the cover shows "Essays on soil and weather", and the cover block's computed background colour is `rgb(31, 111, 67)`.
- Given I already have a site, when I open `/admin/setup`, then the three inputs are pre-filled with my saved values, the button reads "Save changes" (still `create-site-button`), and saving updates the same site rather than creating a second one (the public site reflects the new title after reload).
- Given I submit with an empty title, when I click `create-site-button`, then a validation message is shown and no site is created.

**Priority:** Must-have
**Effort:** Medium

### Story 6 — Write a draft

**Story:** As a writer, I want to write a post with a title and body and have it saved as a draft so that I can work on it before anyone sees it.

**Acceptance criteria:**

- Given I am a signed-in writer with a site on `/admin`, when I click `new-post-button`, then the URL is `/admin/posts/new` and `post-title-input`, `post-body-input`, `save-draft-button` and `publish-button` are visible.
- Given I fill `post-title-input` with "On mulch" and `post-body-input` with at least two sentences, when I click `save-draft-button`, then the status label `post-status-label` reads "Draft", the URL changes to `/admin/posts/<id>`, and the post appears in the `/admin` posts list with the label "Draft".
- Given a draft exists, when I open it from the posts list, then `post-title-input` and `post-body-input` contain exactly the saved title and body.
- Given a draft exists, when I change the body and click `save-draft-button` again, then reopening the post shows the new body and the posts list still shows one entry for it.
- Given I click `save-draft-button` with an empty title, then a validation message is shown and nothing is saved.

**Priority:** Must-have
**Effort:** Medium

### Story 7 — Publish a draft

**Story:** As a writer, I want to publish a draft so that it appears on my public site immediately.

**Acceptance criteria:**

- Given I have a saved draft open in the editor, when I click `publish-button`, then `post-status-label` reads "Published", a published date is shown in the editor, and the posts list labels the post "Published".
- Given the post is published, when a visitor opens the site's public home page, then a card with the post's title is in the feed, showing its excerpt, author name, published date and a reading time such as "1 min read".
- Given the post is published, when a visitor opens the post's public address (the site's public path plus the post's slug, generated from the title, for example `.../on-mulch`), then the page's `<h1>` is the post title and the full body text is visible.
- Given a post has no explicit excerpt, when it is published, then the feed card shows the first sentences of the body as the excerpt.
- Given the post was never published before, when I publish it, then its published date is within a minute of now.

**Priority:** Must-have
**Effort:** Medium

### Story 8 — Drafts stay private

**Story:** As a writer, I want my drafts to stay private so that no reader, and no Ask me question, can reach unfinished writing.

**Acceptance criteria:**

- Given a draft titled "Compost secrets" whose body contains the phrase "zebrafish quantum marmalade", when a visitor opens the site's public home page, then no card contains "Compost secrets".
- Given that draft, when a visitor requests the draft's public address (the site's public path plus its slug), then the page shows a not-found message and no body text, and the underlying request returns 404.
- Given that draft, when the public posts endpoint for the site is requested (per `docs/api-contract.md`), then the response contains no post with that title or slug.
- Given that draft and a member with a feed, when the member opens the member feed, then "Compost secrets" is not listed.
- Given that draft, when a reader types "zebrafish quantum marmalade" into `ask-input` and clicks `ask-button`, then `ask-result` shows the "no matches" message and no passage text, in both no-key and key-present modes.
- Given a published post is unpublished back to draft (should-have Story 16), when the same checks run, then the post is absent from all five surfaces above.

**Priority:** Must-have
**Effort:** Medium

### Story 9 — Read without an account

**Story:** As a reader, I want to visit a public site and read its published posts without an account so that there is nothing between me and the writing.

**Acceptance criteria:**

- Given a fresh browser context with no cookies or storage, when I open the seeded Traversaal.ai site's public home page, then the URL does not redirect to `/login`, the cover heading reads "Traversaal.ai", the description reads "Technical insights and updates from the forefront of AI orchestration", and the cover's computed background colour is `rgb(252, 101, 74)` (`#fc654a`).
- Given the home page, when it loads, then the feed shows one large lead card and further cards below it, ten cards in total for the seeded site, newest first: the first card is "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)" and the last is "LLM Caching Strategies Explained: KV, Prefix, Prompt, and Semantic, and Why Most Teams Only Use One".
- Given I click the card for "Why MLOps Observability Breaks for Tool-Calling Agents -and What Agent Observability Tools Do Instead", when the post page loads, then the `<h1>` is that title, the byline shows "Hamza Farooq", a date of 9 Sep 2026 and a reading time, the body is in a single reading column, and no sign-in prompt appears.
- Given a post page, when it loads, then the "Sign up for more like this." box with `member-email-input` and `join-button` is visible below the body.

**Priority:** Must-have
**Effort:** Medium

### Story 10 — Become a free member by email

**Story:** As a reader, I want to become a free member by entering my email so that I am connected to the site without creating a password.

**Acceptance criteria:**

- Given I am reading a post on the Traversaal.ai site with no account, when I fill `member-email-input` with `dev@example.com` and click `join-button`, then `member-confirmation` appears with text containing "member", no password field is ever shown, and a member row exists for (this site, `dev@example.com`) with status `free`.
- Given `dev@example.com` is already a member of this site, when I submit it again, then `member-confirmation` says I am already a member and the site still has exactly one member with that email.
- Given `dev@example.com` is a member of the Traversaal.ai site, when I submit the same email on a different site's post page, then it succeeds and a second member row exists for (that site, `dev@example.com`); the first site still has one.
- Given I fill `member-email-input` with `not-an-email`, when I click `join-button`, then a validation message asking for a valid email is shown and no member is recorded.
- Membership never requires a password or a writer account; the email alone is enough.

**Priority:** Must-have
**Effort:** Small

### Story 11 — Ask me without an answer key

**Story:** As a reader, I want to ask the site a question in the Ask me box and, when no answer key is configured, get the matching passages from published posts labelled as search results so that I can find what the site has said about my topic.

**Acceptance criteria:**

- Given the server started with no `ANTHROPIC_API_KEY` in its environment and no other configuration, when I open the seeded Traversaal.ai site's home page, then `ask-input` and `ask-button` are visible and usable (Ask me works in this mode by default).
- Given no key, when I type "what is progressive disclosure in context engineering?" into `ask-input` and click `ask-button`, then `ask-result` appears, its mode label `ask-mode-label` reads "Search results" (not "Answer"), and the first result's title is "Context Engineering Techniques: How Progressive Disclosure Outperforms Always-In-Context RAG for Tool and Skill Library Design".
- Given that result, when I inspect it, then each result is a passage of text with the highlighted matching words, shows its post title, and contains an `ask-citation` link whose href is that post's public address; clicking it opens the post page.
- Given no key, when I ask "why does MLOps observability break for agents?", then the first result is "Why MLOps Observability Breaks for Tool-Calling Agents -and What Agent Observability Tools Do Instead".
- Given no key, when I ask "how do I bake sourdough?", then `ask-result` shows a message containing "No matches" and contains zero `ask-citation` links.
- Given only the Traversaal.ai site's posts are published, when I ask from a different site's page, then no Traversaal.ai passage appears (results are scoped to the site being viewed).

**Priority:** Must-have
**Effort:** Medium

### Story 12 — Ask me with an answer key

**Story:** As a reader, I want to ask the site a question and, when an answer key is configured, get a written answer with citations to the published posts it came from, and no answer at all when nothing matched, so that I can trust what I am told.

**Acceptance criteria:**

- Given the server started with a valid `ANTHROPIC_API_KEY`, when I type "when does self-hosting an LLM pay off?" into `ask-input` and click `ask-button`, then within 15 seconds `ask-result` shows `ask-mode-label` reading "Answer", a written paragraph (not a list of passages) that mentions tokens per day, and at least one `ask-citation` link whose text is "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)" and whose href is that post's public address.
- Given a key, when I ask "what is a trajectory trace?", then the answer cites "Why MLOps Observability Breaks for Tool-Calling Agents -and What Agent Observability Tools Do Instead" and every `ask-citation` names a post that is currently published on this site.
- Given a key, when I ask "how do I bake sourdough?", then `ask-result` shows the same "No matches" message as Story 11, contains no answer paragraph and no `ask-citation`, and the server log shows no model call was made.
- Given a key but the answer service fails, is refused or times out (QA may simulate this with an invalid key value), when I ask "when does self-hosting an LLM pay off?", then `ask-result` falls back to `ask-mode-label` "Search results" with the matching passages and `ask-citation` links, plus a note containing "could not be written"; no error page or empty result is shown.
- Given a key, when the answer is written, then the model only received the retrieved passages: asking "zebrafish quantum marmalade" (a phrase that exists only in a draft) still returns "No matches".

**Priority:** Must-have
**Effort:** Medium

### Story 13 — Seeded demo site

**Story:** As a person evaluating the product, I want a fresh install to come with a demo writer whose site is the Traversaal.ai blog, loaded from the seed file, so that the demo answers from real writing rather than placeholder text.

**Acceptance criteria:**

- Given a fresh clone with no database file, when the seed script runs, then it prints the demo writer's email and password to the terminal, and reads `.sprint-zero/seed/traversaal-posts.json` at run time (deleting the file and re-running fails with a clear message rather than seeding embedded text).
- Given the seed has run, when I open `/login` and enter the printed credentials into `email-input` and `password-input` and click `login-button`, then the URL becomes `/admin`, the sidebar shows "Traversaal.ai", and the posts list has exactly ten rows, all labelled "Published".
- Given the seed has run, when I open the Traversaal.ai public home page, then ten cards are shown, newest first, with "Self-Hosting LLMs: The Real Cost-Benefit Framework (API vs. On-Premise, Honestly)" dated 10 Sep 2026 first and "LLM Caching Strategies Explained: KV, Prefix, Prompt, and Semantic, and Why Most Teams Only Use One" dated 7 Sep 2026 last (RFC 2822 `published_at` values were parsed, not stored as text).
- Given the seed has run, when I open the post at slug `llm-router-cost-optimization-route-requests-cheapest-model`, then the title, author "Hamza Farooq", excerpt and body match the seed entry, and the site's accent colour is `#fc654a`.
- Given the seed has run, when I ask "what is progressive disclosure in context engineering?" in Ask me, then a cited result naming the context-engineering article is returned (in whichever mode the server is in).
- Given the seed has already run, when it runs a second time (or the server restarts and re-seeds on start), then there is still exactly one demo writer, one Traversaal.ai site, ten posts and no duplicate slugs.
- The seed ignores the `source_url` and `word_count` fields without error.

**Priority:** Must-have
**Effort:** Medium

## Should-have

### Story 14 — Posts list with status labels

**Story:** As a writer, I want to see all my posts in one list, each labelled Draft or Published, so that I know what is live.

**Acceptance criteria:**

- Given I am signed in with two drafts and one published post, when I open `/admin`, then the list shows three rows, each with its title and a status label reading either "Draft" or "Published", newest first.
- Given the list, when I click a row, then the editor opens for that post at `/admin/posts/<id>`.
- Given a second writer has posts on their own site, when I open `/admin`, then none of their titles appear in my list.

**Priority:** Should-have
**Effort:** Small

### Story 15 — Edit a published post

**Story:** As a writer, I want to edit a post after it is published so that I can fix mistakes.

**Acceptance criteria:**

- Given a published post is open in the editor, when I change `post-body-input` and click the save button (labelled "Update", still `save-draft-button`), then `post-status-label` still reads "Published" and the public post page shows the new body after reload.
- Given I edit a published post, when I save, then its published date does not change.
- Given I edit the title of a published post, when I save, then the post's slug and public address stay the same.

**Priority:** Should-have
**Effort:** Small

### Story 16 — Unpublish back to draft

**Story:** As a writer, I want to unpublish a post back to draft so that I can take something down without deleting it.

**Acceptance criteria:**

- Given a published post is open in the editor, when I click `unpublish-button`, then `post-status-label` reads "Draft" and the posts list labels it "Draft".
- Given the post is unpublished, when a visitor opens the home page or the post's public address, then the post is absent from the feed and the address returns not-found.
- Given the post is unpublished, when a reader asks a phrase found only in that post, then Ask me returns "No matches" in both modes.
- Given the post is republished, when I click `publish-button`, then it reappears on the public site and in Ask me results.

**Priority:** Should-have
**Effort:** Small

### Story 17 — Member feed

**Story:** As a member, I want an in-app feed of the site's published posts so that I can catch up on what I have missed (this replaces email delivery, which is excluded).

**Acceptance criteria:**

- Given `dev@example.com` is a member of the site, when I open the site's member feed page and enter `dev@example.com` into `member-email-input` and submit, then a list of the site's published posts is shown, newest first, each linking to its public address.
- Given an email that is not a member of this site, when I submit it on the feed page, then a message says the email is not a member and no posts are listed.
- Given a draft exists, when the member feed loads, then the draft is not listed.
- Given the writer publishes a new post, when the member reloads the feed, then the new post is at the top.

**Priority:** Should-have
**Effort:** Medium

### Story 18 — Markdown rendering

**Story:** As a reader, I want post bodies written in markdown to render as formatted text so that headings, links and lists read properly.

**Acceptance criteria:**

- Given the seeded post "Context Engineering Techniques: How Progressive Disclosure Outperforms Always-In-Context RAG for Tool and Skill Library Design", when I open its public page, then the body contains an `<h2>` reading "What is context engineering?" and an `<a>` element for at least one inline link, and no literal `##` or `**` characters are visible.
- Given a post body with a bulleted list, when the page renders, then the items are `<li>` elements.
- Given a body containing raw HTML such as `<script>`, when the page renders, then the script tag is not executed or present in the DOM.

**Priority:** Should-have
**Effort:** Small

## Nice-to-have

- As a writer, I want to schedule a post for a future date so that it publishes while I am away.
- As a writer, I want to mark a post as members-only so that only free members can read it.
- As a writer, I want to add a feature image to a post so that the home feed has visual variety.
- As a writer, I want to preview a post as a reader would see it before publishing.
- As a member, I want to sign back in by email link so that I can manage my membership from any device.

## Edge cases to discuss

- Two posts with the same title on one site produce the same generated slug. Either append a suffix (`on-mulch-2`) or reject the second save; the public address and Ask me citations depend on the slug being unique per site.
- Ask me on a site with zero published posts (a new writer's site before their first publish). The PRD leaves this open: show the box and return "No matches", or hide the box until the first post is live.
- Full-text search is literal. A question with none of the article's words ("cost of running my own model") returns "No matches" on the seeded site even though the self-hosting article answers it. QA criteria above use wording that appears in the articles; the team should agree that an honest empty result is the intended behaviour, not a bug.
- Key present but the model's answer says the passages do not cover the question. Show the model's "not covered" sentence with the citations it did receive, or treat it as "No matches"? The decisions file only rules that the model is never called on empty retrieval.
- A reader submits `Dev@Example.com` after `dev@example.com` is already a member. Decide whether the (site, email) uniqueness check lowercases emails; the criteria above assume it does.

## Questions for the team

1. How is a site addressed publicly: by a path segment such as `/s/<slug>`, `/<site-slug>`, or a single-site default on the root? Every public URL and `ask-citation` href in these stories depends on it. `[NEEDS CLARIFICATION]`
2. Should the writer's admin show a member count or a list of member emails at MVP? The stories above assume neither; if a count is wanted it needs a testid and an endpoint in the contract.
3. On unpublish, is `published_at` kept (so republishing keeps the original date) or cleared (so republishing sets it to now)? Story 16 and the feed ordering behave differently under each rule.
