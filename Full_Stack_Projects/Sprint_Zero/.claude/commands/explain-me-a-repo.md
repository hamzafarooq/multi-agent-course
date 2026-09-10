# /explain-me-a-repo

Produce a reference brief for the URL(s) in `docs/scope.md`. This brief is what the PRD generator reads next, so it needs to be structured enough to build from — not just a summary.

## Step 1 — Read scope

Read `docs/scope.md`. You need:

- **Company URL** — always present
- **Repo URL** — may be "not provided"
- **Core loop** — shapes which parts of the reference to emphasise

If `docs/scope.md` does not exist, stop and tell the user to run `/sprint-zero-scope` first.

## Step 2 — Research

Investigate the reference with whatever web research tools you have: Brave Search MCP if it is registered, otherwise the built-in `WebSearch` and `WebFetch` tools, and a browser MCP (`playwright` or `brave-devtools`) for pages that only render client-side. Start with the company URL, then the repo if provided.

Run these searches in sequence. Adapt if the reference isn't on GitHub.

1. Search for: `[company name] what it does product overview`
2. Search for: `[company name] how it works features`
3. If repo URL provided: navigate to it, read the README, browse the top-level folder structure
4. Search for: `[company name] pricing OR plans OR tiers` (helps surface the feature matrix)
5. Search for: `[company name] [core loop phrase from scope]` (targeted pull on the loop that matters)

If the repo is private, a 404, or the company site is unreachable, stop and tell the user clearly. Don't fabricate.

## Step 3 — Write `docs/reference-brief.md`

Use this structure exactly. The PRD generator parses it, so stick to the headings.

```markdown
# Reference brief — [Company name]

**Company URL:** [URL]
**Repo URL:** [URL or "not provided"]
**Language(s):** [if repo provided; otherwise "n/a"]

---

## What it does

One paragraph. Plain English. The problem it solves and who uses it.

## Core user flow

Walk through the primary user journey end-to-end. 3-6 steps. This is what Sprint Zero's build will rebuild in simplified form, so it needs to be concrete.

## How it works (high level)

2-4 bullets on architecture. No code. Concepts only.

## Feature inventory

A table of every significant feature the reference has. The decisions-writer reads this to identify scope cuts, so be thorough — include features you suspect we'll cut.

| Feature | What it does |
|---------|--------------|
| ... | ... |

## Data model (if repo provided)

The main entities and their relationships. Bullet list is fine.

## Key files and folders (if repo provided)

| Path | What it does |
|------|--------------|
| ... | ... |

## Who it's for

Two sentences. First: the person setting it up. Second: the end user.

## Things worth flagging

3-5 observations. Unusual design choices, heavy dependencies, anything a PM building a simplified version should know. Always include any AI / LLM integration if present.
```

## Rules

- Plain English throughout. No code unless quoted directly from the repo.
- If the README is thin or missing, say so and work from the file tree.
- Feature inventory is the most important section for the downstream chain — err on the side of including features we might cut, because the decisions document needs them to exist here.
- After writing, print a one-line summary: `Reference brief written. [N] features inventoried. Ready for /prd-generator.`
- Do not ask the user to save the file — write it directly to `docs/reference-brief.md`.

$ARGUMENTS
