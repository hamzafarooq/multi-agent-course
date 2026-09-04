# Competitor Research Workshop

This project is a small Claude Code harness for **competitor research**.
It exposes one user-invocable skill that does the bulk of the work itself,
plus two specialist subagents for tasks that genuinely benefit from their
own context window.

> **Workshop note:** this CLAUDE.md is intentionally read by both Claude (every
> session) and by learners reading the repo. The rules below explain *why* they
> exist, not just *what* they are — that's how you write a CLAUDE.md that ages well.

## How the pieces fit

```
User → /competitor-research
         │
         ▼
  competitor-research (skill)
   1. Asks scoping question
   2. WebSearch → identifies 3–5 direct competitors
        (brave_web_search only for date-strict queries)
   3. For each competitor (in parallel):
        ├── WebFetch homepage  ← skill does inline
        ├── pricing-fetcher subagent
        │     └── WebFetch first; Playwright fallback if JS-rendered
        └── review-miner subagent
              └── WebSearch + WebFetch (Brave for news + summarization)
   4. Synthesizes one 6-bullet card per competitor
   5. Writes Gap Analysis
   6. Ends with one sharp question
```

## The skill / subagent split (and why)

The skill **does its own research** for searches and homepage fetches —
those are fast, light tasks. The skill **delegates** two things:

- **`pricing-fetcher`** — pricing extraction. WebFetch first (cheap); falls
  back to Playwright (~114K tokens/session) only when the page is JS-rendered.
  Isolated in a subagent so the heavy context doesn't pollute the orchestrator.
- **`review-miner`** — review aggregation. Reads 10+ pages across G2/Reddit/HN/
  ProductHunt/Trustpilot per competitor. Distills patterns (≥3 confirming
  voices across ≥2 platforms = signal). Heavy reading + judgment.

This split is the workshop's central lesson: **delegate work that is
heavy, parallelizable, and returns clean structured output. Keep
lightweight orchestration in the skill.**

## Tool stack

| Tool | Where it's used | Owner |
| --- | --- | --- |
| `WebSearch` | Default search — competitors, reviews | Built-in |
| `WebFetch` | Default page fetch — homepages, pricing first attempt, individual review pages | Built-in |
| `mcp__brave-search__brave_web_search` | Only when strict 12-month recency matters | MCP (optional) |
| `mcp__brave-search__brave_news_search` | Recent-news lookups (fundraising, pivots) inside `review-miner` | MCP (optional) |
| `mcp__brave-search__brave_summarizer` | Digesting long aggregator pages inside `review-miner` | MCP (optional) |
| `mcp__playwright__browser_*` | JS-rendered pricing pages, fallback inside `pricing-fetcher` | MCP (optional) |

**Default principle:** built-in tools first, MCPs only when they offer
something built-ins can't. Never reach for Brave when WebSearch would have
been fine — that wastes the free-tier budget for no gain.

## MCP servers (declared in `.mcp.json`)

Two MCP servers are wired into this repo:

- **`brave-search`** — requires `BRAVE_API_KEY` (free tier at brave.com/search/api).
  If not configured, the Brave tools simply won't be available and the skill
  falls back to `WebSearch` for everything. **Optional but recommended.**
- **`playwright`** — auto-installs via `npx`. Browser binaries (~165 MB) are
  installed by running `bash scripts/setup.sh` once after cloning. The script
  is idempotent: first run downloads Chromium; subsequent runs exit in <1 sec.
  If the install fails (locked-down network), Playwright tools simply won't be
  available and `pricing-fetcher` falls back to WebFetch-only.

Both servers are declared so any contributor cloning the repo gets the wiring
for free. Manual setup steps a student takes after cloning:

1. **Run `bash scripts/setup.sh`** to install Chromium (only if they want
   Playwright fallback for JS-rendered pricing).
2. **Set `BRAVE_API_KEY`** via `cp .env.example .env` and editing the file
   (only if they want Brave's news/summarizer features).

Both are optional — the skill works on built-in `WebSearch` + `WebFetch` alone.

---

## ⚠️ CRITICAL — non-negotiables

These are the rules that, if violated, break the system's value entirely.

1. **Never invent pricing.** If a competitor's price isn't public, write
   *"Not public"* or *"Contact sales"*. A made-up number poisons the gap
   analysis and any downstream decision.
2. **Never claim a single review as a pattern.** A G2 1-star rant is anecdote.
   Patterns require ≥3 confirming voices across ≥2 platforms.
3. **Subagents fan out in parallel, not sequentially.** All `pricing-fetcher`
   and `review-miner` calls go in *one* message — sequential = N× wall-clock
   time for zero quality gain.
4. **Don't delegate light work.** Homepage fetches and basic searches are
   light; the skill does them. Delegating fast tasks adds latency and obscures
   what the skill is actually doing.
5. **Default to built-in tools.** Reach for an MCP only when it offers
   something built-ins can't. Brave's free tier is 2,000 queries/month —
   spending it on queries `WebSearch` could have handled is the workshop's
   anti-pattern.
6. **6 bullets per competitor card. Hard cap.** Empty bullets get an `—`.
   Don't add a 7th "for completeness" — the constraint is what forces clarity.

---

## ✅ DO

| Do | Why |
| --- | --- |
| Prioritize sources from the **last 12 months** | Pricing, positioning, and review sentiment all decay fast. Old data looks confident but lies. |
| **Cross-reference** every non-trivial claim against ≥2 independent sources | The company's own site is one source. You need at least one more. |
| **Cite source URLs inline** for any pricing or differentiator claim | Lets the reader verify and re-check when prices change. |
| **Quote hero copy verbatim** when you fetch a homepage | The exact words a company chooses are signal — paraphrasing destroys it. |
| **Translate marketing-speak into plain English** in differentiator bullets | "AI-powered next-gen platform" is noise. Reader needs to know what the product *does*. |
| **Surface contradictions** between sources rather than picking one | Two sources disagreeing is itself a finding. Hiding it is dishonest. |
| **Make Gap Analysis bullets falsifiable** | "No per-seat plan under $10/mo for teams <5" is testable. "Better UX" is hand-waving. |
| **End the report with exactly one sharp question** | Forces the user to decide. The whole research pass is in service of that decision. |
| **Audit `pricing-fetcher`'s `Method used` field** | If 4 of 5 competitors all used Playwright, something's wrong with WebFetch. Investigate before trusting. |

---

## ❌ DON'T

| Don't | Why it hurts |
| --- | --- |
| Don't add a closing summary paragraph after the question | Padding. The 6-bullet cards + gap section already are the summary. |
| Don't reach for Brave when WebSearch would have been fine | Burns the free-tier query budget for zero gain. |
| Don't invoke Playwright tools directly from the orchestrator | Heavy context (~114K tokens) belongs in the `pricing-fetcher` subagent, not the main thread. |
| Don't fabricate an enterprise tier price because the public site is vague | "Contact sales" is the answer. Inventing a number is the failure mode. |
| Don't list every weakness ever mentioned in a review | Only recurring patterns. Listing 8 one-off complaints buries the real signal. |
| Don't have subagents write to disk or run shell commands | They're read-only researchers. Their `tools:` lists are restricted on purpose. |
| Don't ask the user more than 2 clarifying questions up front | Research that begins with an interview kills momentum. Bound it. |
| Don't retry a subagent with the same prompt if it returned "insufficient data" | Either accept the gap or hand it a *narrower* question. Same prompt = same answer. |

---

## 🎓 Learning notes (for workshop participants)

These are the design choices worth understanding *why*:

**Why two subagents and not four (or one)?**
The earliest version had four (positioning, pricing, reviews, messaging) — too
many; three of the four were doing light fetches that didn't earn their own
context. We collapsed to one (review-miner). Adding Playwright re-introduces a
heavy task (pricing extraction when JS-rendered), so `pricing-fetcher` joins
the team. Each subagent now has a clear "why we delegate" story: heavy work +
parallelizable + clean structured output. **Picking the right thing to delegate
is more interesting than delegating everything.**

**Why are subagents read-only-ish (no `Bash`, no `Write`)?**
The `tools:` list is a security boundary, not a hint. A subagent literally
cannot call tools outside its list. Research workers have nothing legitimate
to write to disk; restricting them is defense in depth.

**Why default to built-in tools?**
MCPs add setup friction (API keys, npx installs, browser binaries). Every MCP
you require is a barrier students must clear before they can run anything.
Default to built-ins; reach for MCPs only when they unlock real capability.

**Why hard caps (6 bullets, 2 clarifying questions, 1 closing question)?**
Constraints force clarity. A skill with "give a thorough report" produces
sludge. A skill with "exactly 6 bullets" produces something the user can read
and act on.

**Why is "Unknown" a required valid answer?**
The default failure mode of LLMs is to fabricate confident-sounding numbers
when real data is missing. Making *"Not public"* / *"Contact sales"*
first-class outputs removes the incentive to invent.

**Why does the skill ask only 1–2 questions up front?**
Research with too many gates feels like a customer service script. The skill
makes a reasonable choice and proceeds; the user can correct mid-flight. The
closing question (*"Which gap are you trying to own?"*) is where the real
decision happens.

---

## File layout

```
.
├── .mcp.json                          # MCP server config (brave-search, playwright)
├── .env.example                       # template for BRAVE_API_KEY
├── CLAUDE.md                          # this file
├── README.md
├── docs/eval-ground-truth.md          # 10 eval cases
├── examples/                          # sample skill output
├── runs/                              # captured outputs for eval scoring
└── .claude/
    ├── skills/
    │   ├── competitor-research/SKILL.md   # the skill (does the work)
    │   └── skill-evaluator/SKILL.md       # the eval scorer
    └── agents/
        ├── pricing-fetcher.md         # subagent: pricing (WebFetch + Playwright)
        └── review-miner.md            # subagent: reviews (WebSearch + Brave)
```

## When to use this

Trigger the skill when the user asks any of:
- "Who are our competitors for X?"
- "Run a competitive analysis on Y"
- "What's the market landscape for Z?"
- "Where's the gap in [category]?"

Do **not** trigger for: customer research, user interviews, internal product
audits, head-to-head two-product comparisons. Those are different jobs with
different methods.
