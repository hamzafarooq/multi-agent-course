---
name: competitor-research
description: Research 3–5 competitors for any product or feature. Returns positioning, pricing, key differentiators, gaps, and an unclaimed angle. Use when the user asks about competitors, market landscape, or competitive analysis.
---

# Competitor Research

You research competitors yourself for the light, fast tasks (search and
homepage fetches), and you delegate the heavy work to specialist subagents:

- `pricing-fetcher` — pricing extraction with WebFetch-first, Playwright-fallback
- `review-miner` — distilling user sentiment from 10+ review pages

> **Workshop note:** the split between "skill does it" and "subagent does it"
> follows one rule: **delegate work that is heavy, parallelizable, and returns
> clean structured output**. Light fetches stay in the skill. Heavy or
> potentially-heavy work (Playwright at ~114K tokens, review-mining across
> dozens of pages) gets its own context window.

---

## Step 1 — Scope

Ask the user **once**:

> "What product or feature are you researching? Who is it for?"

Skip if they already gave both. Cap at **2** clarifying questions max
(geography, segment, direct vs. adjacent). Don't run an interview.

## Step 2 — Identify competitors

Use **`WebSearch`** by default. Look for:

- "best [category] tools 2025/2026"
- G2 / Capterra / Gartner category pages
- Reddit "alternatives to [known leader]" threads

**Use `mcp__brave-search__brave_web_search` instead only when** you need
strictly the last 12 months of results (e.g., a fast-moving category where
2-year-old listicles would be misleading). Brave's `freshness` parameter is
deterministic; `WebSearch`'s recency is a soft preference. For most categories
the soft preference is fine.

Pick **direct** competitors (same buyer, same job-to-be-done). List them back
to the user briefly so they can correct the set before you go deep.

## Step 3 — Per competitor (parallel work)

For each competitor, dispatch the following **in a single message with multiple
tool calls** so they run concurrently:

### 3a. Homepage — you do this yourself (`WebFetch`)

Fetch the homepage and extract:

- Hero headline (verbatim)
- Subhead (verbatim)
- Top 3 features in homepage order
- Stated differentiators (translated to plain English, not paraphrased into
  marketing-speak)

This stays inline because homepage HTML is server-rendered for ~95% of
competitor sites — fast, light, and pollutes nothing.

### 3b. Pricing — delegate to `pricing-fetcher` subagent

Spawn one `pricing-fetcher` per competitor. It tries `WebFetch` first; falls
back to Playwright browser automation only if the page is JS-rendered.

**Why this is delegated:** Playwright sessions cost ~114K tokens each. Even
when only 1 in 3 competitors needs it, isolating that work in subagents keeps
the orchestrator's context lean and lets fetches run in parallel.

The subagent returns a structured pricing table plus a `Method used` field
(WebFetch / Playwright) — audit this field. If 4 of 5 competitors all used
Playwright, something's wrong with WebFetch and you should investigate before
trusting the data.

### 3c. Reviews — delegate to `review-miner` subagent

Spawn one `review-miner` per competitor. It searches across G2/Capterra/Reddit/
HN/ProductHunt/Trustpilot, distills patterns (≥3 confirming voices across ≥2
platforms = signal), and returns recurring strengths + weaknesses.

**Why this is delegated:** review pages are dense user-voice text — 10+ pages
per competitor. Doing it inline pollutes the orchestrator's context with raw
review snippets.

If a subagent returns "insufficient data," don't retry with the same prompt —
either accept the gap (and surface it in the final report) or hand the next
attempt a sharper, narrower question.

## Step 4 — Synthesize per-competitor cards

Combine your homepage research with the two subagents' findings into **exactly
6 bullets** per competitor:

```
### [Competitor Name]
- **Positioning**: one sentence (their words, plain English)
- **Target customer**: who they're built for
- **Pricing**: tiers and price points, or "Not public"
- **Differentiators**: 2–3 things they do well
- **Weaknesses**: 1–2 recurring complaints from reviews/forums
- **Source date**: most recent source pulled (YYYY-MM)
```

Hard rules:
- 6 bullets exactly. If a bullet is empty, write "—" but keep the line.
- Pricing must cite a source URL inline if public.
- No marketing language in your translation.

## Step 5 — Gap Analysis

Add this section verbatim:

```
### Gap Analysis
- **What no competitor does well**: [specific capability gap]
- **Where pricing is underserved**: [a tier or model nobody offers]
- **Unclaimed positioning angle**: [a frame nobody owns]
```

Each gap must be **falsifiable** — grounded in something a reader can verify.
"Better UX" is not a gap. "No competitor offers per-seat pricing under $10/mo
for teams under 5" is.

## Step 6 — Close

End the report with exactly one line:

> **Based on this, which gap are you trying to own?**

No summary. No "let me know if you want more." Just the question.

---

## Tool selection cheat sheet

| Task | Default tool | Reach for MCP when... |
| --- | --- | --- |
| Identify competitors | `WebSearch` | You need strict 12-month recency → `brave_web_search` |
| Fetch a homepage | `WebFetch` | (never — homepage is light) |
| Fetch a pricing page | `pricing-fetcher` subagent | (subagent decides internally whether Playwright is needed) |
| Mine reviews | `review-miner` subagent | (subagent decides internally — uses Brave's news/summarizer for specific cases) |

**Default principle:** built-in tools first, MCPs only when they offer
something built-ins can't.

---

## Anti-patterns (do not do)

- ❌ Doing your own deep web searches once you've identified competitors —
  delegate pricing and review work to the subagents
- ❌ Calling subagents sequentially per competitor instead of in parallel
- ❌ Reaching for `brave_web_search` when `WebSearch` would have been fine
  (this wastes Brave's free-tier budget)
- ❌ Invoking Playwright tools directly from the orchestrator — those calls
  belong in the `pricing-fetcher` subagent so the heavy context is isolated
- ❌ Accepting a `pricing-fetcher` report where 4 of 5 competitors used
  Playwright — investigate WebFetch first
- ❌ Adding a 7th bullet "for completeness"
- ❌ Inventing pricing because the public site is vague
- ❌ Listing every G2 complaint — only recurring patterns
- ❌ Writing a closing paragraph after the sharp question
