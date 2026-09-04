# Competitor Research Agent

A Claude Code harness for **competitor research**. One user-invocable skill
does the bulk of the work itself, plus two specialist subagents for the tasks
that genuinely benefit from their own context window.

## How it works

```
User: "Run competitor research on Notion"
        │
        ▼
Claude reads available skills → matches "competitor-research"
        │
        ▼
┌──────────────────────────────────────────────────┐
│  SKILL: competitor-research                      │
│  (instructions Claude follows directly)          │
│                                                  │
│  Step 1: Ask scoping question                    │
│  Step 2: WebSearch → pick 3–5 competitors        │
│          (Brave only for date-strict queries)    │
│  Step 3: For each competitor (in parallel)       │
│          ├── WebFetch homepage  ← skill does     │
│          ├── pricing-fetcher subagent ────────┐  │
│          └── review-miner subagent ──────────┐│  │
│  Step 4: Synthesize 6-bullet cards          ││  │
│  Step 5: Write Gap Analysis                 ││  │
│  Step 6: Ask the closing question           ││  │
└─────────────────────────────────────────────┼┼──┘
                                              ││
            ┌─────────────────────────────────┘│
            ▼ (one per competitor, parallel)   │
   ┌────────────────────────────────────┐      │
   │ pricing-fetcher (subagent)         │      │
   │ Tries WebFetch first (cheap).      │      │
   │ Falls back to Playwright only if   │      │
   │ pricing is JS-rendered (~114K tok).│      │
   │ Returns structured tier table.     │      │
   └────────────────────────────────────┘      │
                                               │
            ┌──────────────────────────────────┘
            ▼ (one per competitor, parallel)
   ┌────────────────────────────────────┐
   │ review-miner (subagent)            │
   │ Reads 10+ pages: G2, Reddit, HN,   │
   │ ProductHunt, Trustpilot.           │
   │ Uses Brave only for news +         │
   │ summarizing long pages.            │
   │ Returns recurring strengths +      │
   │ weaknesses (≥3 voices, ≥2 plats).  │
   └────────────────────────────────────┘
```

## Setup

Prerequisites: [Claude Code](https://claude.com/claude-code), Node.js (for the
MCP servers).

```bash
git clone https://github.com/hamzafarooq/claude-code-starter.git
cd claude-code-starter/ai-agent-workshop
bash scripts/setup.sh
```

> **Why `cd ai-agent-workshop`?** Claude Code reads `.claude/skills/` and
> `.mcp.json` from its working directory. The skill, subagents, and MCP wiring
> all live inside this folder, so you need to start `claude` from here for
> them to load.

The setup script does two things, both idempotent (safe to re-run any time):

1. **Creates `.env`** from `.env.example` if it doesn't exist — so you can
   add your Brave API key.
2. **Installs Playwright Chromium** (~165 MB) if not already present —
   used as a fallback for JavaScript-rendered pricing pages.

After running it:

- **Add your Brave API key** (optional). Open `.env` in any editor and
  replace `your_brave_api_key_here` with a real key from
  [brave.com/search/api](https://brave.com/search/api/) (free tier ~2,000
  queries/month). Without a key, the skill falls back to `WebSearch` for
  everything.

### What's required vs. optional

| Component | Required? | Failure mode if missing |
| --- | --- | --- |
| Built-in `WebSearch` + `WebFetch` | **Required** (ships with Claude Code) | — |
| Brave Search MCP (API key in `.env`) | Optional | Skill falls back to `WebSearch` for news/summaries |
| Playwright MCP (Chromium browser) | Optional | `pricing-fetcher` falls back to WebFetch-only and flags the limitation in *Gaps & Uncertainties* |

The skill works on built-ins alone — both MCPs add capability but neither is required.

> **If the Playwright install fails** (corporate firewall, locked-down machine),
> just move on — the skill still works without it, falling back to WebFetch-only
> for pricing pages. `pricing-fetcher` notes this in its *Gaps & Uncertainties*
> section so the limitation is visible rather than silent.

The `.mcp.json` declares both MCP servers; Claude Code picks them up
automatically on session start.

## Quickstart

Once setup is done, open Claude Code in this repo:

```bash
claude
```

Then trigger the skill:

- Type `/competitor-research`, or
- Ask naturally: *"Who are our competitors for X?"* / *"Run a competitive
  analysis on Y"* / *"What's the market landscape for Z?"*

The skill returns:

1. One **6-bullet card** per competitor (positioning, target customer, pricing,
   differentiators, weaknesses, source date)
2. A **Gap Analysis** section with three falsifiable gaps
3. One sharp closing question

## Example output

See [examples/wispr-flow-competitive-landscape.md](examples/wispr-flow-competitive-landscape.md)
for the actual report this skill produced when run on Wispr Flow in May 2026 —
4 competitors, gap analysis, sources cited inline. It's the canonical reference
for what a "good" run looks like.

## Evaluating the skill

Ground truth dataset and eval workflow live in [docs/eval-ground-truth.md](docs/eval-ground-truth.md)
and [runs/](runs/). The flow:

1. Run the skill on the 10 inputs in the ground truth file. Save each output to
   `runs/<date>/case-NN-*.md`.
2. Run `/skill-evaluator` against the ground truth + your run directory.
3. Use the *Fix to make* output to patch [SKILL.md](.claude/skills/competitor-research/SKILL.md).
4. Don't ship below 8/10.

See [runs/README.md](runs/README.md) for the full workflow.

## The skill / subagent split — and why it matters

This is the central design choice, and it's the workshop's main lesson.

| Task | Where it runs | Why |
| --- | --- | --- |
| Scoping & competitor selection | **Skill** | Light reasoning + one search. Fast. |
| Homepage research | **Skill** (parallel WebFetch) | Server-rendered for ~95% of sites. Fast and light. |
| Pricing research | **Subagent** (`pricing-fetcher`) | WebFetch first; Playwright as fallback can hit ~114K tokens — isolate it. |
| Review mining | **Subagent** (`review-miner`) | 10+ pages across G2/Reddit/HN/PH/Trustpilot per competitor. Heavy reading + judgment. |
| Synthesis & Gap Analysis | **Skill** | Needs the full picture in one place. |

**Rule of thumb for delegating:** push down work that is (a) heavy enough to
warrant its own context window, (b) parallelizable across N items, and (c)
returns clean structured output. Anything else stays in the skill.

## Skill vs. subagent — the mental model

- **Skill** = a *playbook* the main Claude reads and follows. It's not a separate
  process; it's instructions loaded into the current conversation. It can call
  tools (WebSearch, WebFetch, etc.) directly.
- **Subagent** = an *actual separate Claude instance* with its own context window,
  tool access, and remit. The skill spawns it via the `Agent` tool when it has a
  heavy, parallelizable task to offload.

The user only ever talks to the **skill**. The subagents are invisible — they
return structured reports that the skill folds into the final answer.

## Does the skill ask questions?

Yes, but bounded:

| Scenario                          | Behavior                                              |
| --------------------------------- | ----------------------------------------------------- |
| User gives no context             | Asks one scoping question: product + audience         |
| User already provided both        | Skips the question, confirms in one line              |
| Scope still ambiguous             | Up to **2** clarifying questions (hard cap)           |
| End of report                     | Always asks one closing question about the gap to own |

Never an interview. The cap is intentional.

## File layout

```
.
├── .mcp.json                                  # MCP server config
├── .env.example                               # template for BRAVE_API_KEY
├── CLAUDE.md                                  # project-level instructions
├── README.md                                  # this file
├── docs/
│   └── eval-ground-truth.md                   # 10 eval cases
├── examples/
│   └── wispr-flow-competitive-landscape.md    # sample skill output
├── runs/
│   ├── README.md                              # eval workflow
│   └── _template/                             # case stubs for each eval pass
└── .claude/
    ├── skills/
    │   ├── competitor-research/SKILL.md       # the skill
    │   └── skill-evaluator/SKILL.md           # the eval scorer
    └── agents/
        ├── pricing-fetcher.md                 # subagent: pricing
        └── review-miner.md                    # subagent: reviews
```

## Design conventions (enforced by the skill + subagents)

- **Recency bias** — prioritize sources from the last 12 months; flag older
- **Cross-referencing** — every non-trivial claim needs ≥2 independent sources
- **Hard 6-bullet cap** per competitor, with `—` placeholders rather than padding
- **Falsifiable gaps** — *"no per-seat pricing under $10/mo for teams <5"* beats
  *"better UX"*
- **Patterns, not anecdotes** — one G2 complaint is noise; ≥3 across ≥2 platforms
  is signal
- **Unknown is valid** — *"Pricing not public"* beats an invented number
- **Default to built-in tools** — reach for MCPs only when they offer something
  built-ins can't
