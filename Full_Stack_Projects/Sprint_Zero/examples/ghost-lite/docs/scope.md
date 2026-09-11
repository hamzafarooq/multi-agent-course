# Sprint Zero — Scope

## Reference

- **Company URL:** https://ghost.org
- **Repo URL:** https://github.com/TryGhost/Ghost

## Build configuration

- **Project type:** web-app
- **Stack profile:** node-react
- **Data layer:** local

A React + Vite UI talking to an Express API, with data and auth stored locally in SQLite (no external account needed).

## Build level

**MVP**

Real auth and real data on one core loop, end to end.

## Core loop

A writer signs up, creates a site (title, description, accent color), writes a post with a title and body, and publishes it. A reader visits the public site without an account, reads the post, becomes a free member with their email, and asks the site a question in an "Ask me" box; the answer cites the posts it came from. Ask me runs on SQLite full-text search over published posts with no configuration, and when an ANTHROPIC_API_KEY environment variable is present it uses Claude to write the answer from the retrieved posts; without a key it returns the matching passages. Seed content is real: the seed script creates one demo writer whose site is the Traversaal.ai blog, loading the 10 articles in .sprint-zero/seed/traversaal-posts.json (title, slug, author, published date, excerpt, markdown body, plus the site title, description, and accent color) as published posts, so the demo's Ask me answers from real writing rather than invented filler.

## Excludes

- Paid tiers, Stripe, and any payments
- Static pages (only posts)
- Tags and collections
- Multiple newsletters
- Theme upload and theme marketplace (one built-in theme with the site's accent color)
- Integrations, webhooks, Zapier
- Comments
- Recommendations
- Multiple staff users and roles (one owner per site)
- Custom domains
- Real email sending (published posts appear in a member's in-app feed)
- Analytics and post stats
- SEO settings and code injection
- A rich text editor (plain textarea; markdown rendering optional)
- Embeddings or a vector database (keyword FTS only for retrieval)
