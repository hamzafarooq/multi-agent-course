# Next Session — Agent Architecture Demo

> Resumable handoff. Read this file first if returning to this project.

---

## Current state

**Live on Vercel.** Production URL: `https://skill-sub-multi-agent.vercel.app`

This is a Next.js 16 demo app that teaches 3 levels of Claude agent architecture through animated, simulated visualizations. The example domain is building a full-stack task manager (React + FastAPI + PostgreSQL). No real API calls — all outputs are pre-scripted.

---

## What's built

### Stack
- Next.js 16.2.6 (App Router, Turbopack)
- React 19, TypeScript, Tailwind v4
- All styling via inline styles + CSS variables (no Tailwind classes for layout)
- Inter font via `next/font/google`

### Key files

| File | Purpose |
|------|---------|
| `lib/demo-data.ts` | All 3 levels — agents, coordinates, connections, scripted steps, code snippets, click-to-expand detail markdown. AgentDef role union includes `'human'`. |
| `components/SimulationView.tsx` | Canvas (720×440), S-curve SVG connections, hover tooltips, click-to-open node detail modal, simulation engine |
| `components/AgentNode.tsx` | Individual agent card (170×78px, fixed) with pulse animation. Supports `onClick` for detail modal. |
| `components/LevelSelector.tsx` | Left sidebar: level buttons + collapsible file tree + use case footer |
| `components/FileTree.tsx` | Collapsible `.claude/` file tree — CLAUDE.md, 4 skill files, 2 agent files. Click any `.md` to open a white-background file viewer modal. |
| `components/ConceptCallout.tsx` | Two-tab callout: "What's happening" + "How to write it" |
| `app/page.tsx` | Shell: topbar, 1180px grid layout, 3-step stepper, subtle course CTA in bottom-right corner |
| `app/globals.css` | CSS variables (warm paper theme) + keyframe animations |
| `PROMPT.md` | One-shot prompt to recreate this app from scratch in Claude Design |

### Design source
Fetched from a Claude Design handoff bundle (`Agent Architectures.html`). Warm off-white paper (`#F6F3EC`), terracotta accent (`oklch(0.58 0.16 38)`), muted moss for done state, Inter throughout.

---

## The 3 levels

| Level | Name | Tagline | Agents | Layout |
|-------|------|---------|--------|--------|
| 1 | Single Skill | A skill is a reusable prompt | 1 node (Full-Stack Dev) | Centered |
| 2 | Sub-Agent | Skill vs Sub-Agent — side by side | 4 nodes (You + Planner Agent + Formatter Skill + Research Agent) | Human → Main → [Skill, Sub-Agent] |
| 3 | Orchestrator | The agent decides the team | 6 nodes (Project Lead + 4 specialists + Tech Lead synthesiser) | Tree hierarchy |

### Key conceptual distinctions baked in
- **Skill** = a `.md` file. No tools, no memory, no external access.
- **Sub-agent** = skill + tools + memory + isolated context.
- **Level 2 now shows both side by side** — Formatter Skill (no tools, fast) and Research Agent (has tools, slower) fan out from the same Planner Agent. Students see the contrast without switching levels.
- **Human node** — Level 2 has a `role: 'human'` node ("You") at the top. Styled with `#F4F1EC` background to visually distinguish from agent nodes.
- **Level 2 vs Level 3:** Level 2 main agent delegates and still assembles the final output itself. Level 3 orchestrator delegates everything and does no work itself.
- **Hardcoded vs dynamic topology:** writing `asyncio.gather(a, b, c)` is static. The orchestrator reads the goal and picks the team at runtime.

---

## Features added (2026-05-22 session)

- **Click-to-expand node detail** — click any agent node to open a modal with rendered markdown explaining that node's role (skill vs sub-agent vs orchestrator), including code examples
- **File tree in left sidebar** — collapsible `.claude/` folder with full-length realistic `.md` files for CLAUDE.md, 4 skill files (`full-stack-developer`, `ui-designer`, `frontend-developer`, `backend-developer`), and 2 agent files (`tech-lead`, `project-lead` with `tools:` and `memory:` frontmatter)
- **File viewer modal** — white/paper background, monospace content, dismisses on backdrop click
- **Body scroll lock** — background freezes when any modal is open
- **Course CTA** — subtle pill in bottom-right corner linking to `maven.com/boring-bot/advanced-llm`
- **Domain retheme** — all levels now use full-stack website building as the example (was content marketing)
- **Python code** — all code snippets use the Anthropic Python SDK (`anthropic` package, `asyncio.gather` for parallel)
- **Level 3 removed** (was Parallel Agents) — site went from 4 levels to 3. Old Level 4 (Orchestrator) is now Level 3.

---

## How to run

```bash
cd skill-sub-multi-agent

# Dev (HMR can cause Chrome DevTools crashes — use production instead)
npm run dev

# Production (stable for demos)
npm run build && npm run start -- --port 3002

# Open
open http://localhost:3002
```

> **Note:** The dev server HMR conflicts with Chrome DevTools MCP. Always use the production build (`npm start`) when demoing or screenshotting via DevTools.

---

## Known issues / quirks

- **Dev server HMR crashes Chrome DevTools context** — use `npm start` for any browser automation or screenshotting.
- **Canvas is fixed 720×440px** — not responsive. Clips on screens narrower than ~800px. Acceptable for desktop demos.
- **Tooltip overflow** — tooltips are positioned outside the canvas bounds intentionally (outer canvas div has no `overflow: hidden`).
- **Course image** — loaded from Maven's CDN (`d2426xcxuh3ht5.cloudfront.net`). If it fails to load, the `onError` handler hides it gracefully.

---

## Possible next moves

- **Responsive canvas** — scale with `transform: scale()` wrapper on smaller screens
- **Level transitions** — fade/slide animation when switching between levels
- **Live API toggle** — wire Level 1 to a real Claude API call with a "simulated / live" toggle
- **Narration mode** — auto-advance through all 3 levels with timed pauses, for hands-free classroom demo
- **Export as standalone HTML** — bundle into a single `.html` file for sharing without a server
- **Add a tools demo** — show a sub-agent with an active tool call (web search result appearing mid-simulation)

---

## Session history

| Date | What happened |
|------|--------------|
| 2026-05-21 | Built initial version (white theme, percentage-based layout) |
| 2026-05-21 | Renamed `agent-demo/` → `skill-sub-multi-agent/` |
| 2026-05-21 | Fetched Claude Design file, warm paper aesthetic, fixed 720×440 canvas, S-curve connections, hover tooltips, step counter |
| 2026-05-22 | Rethemed to full-stack website building; Python SDK code; click-to-expand node modals; file tree with realistic .md files; body scroll lock; level 3 (Parallel Agents) removed; course CTA added; all Level 4 refs updated to Level 3 |
| 2026-05-22 | Deployed to Vercel (`skill-sub-multi-agent.vercel.app`); rewrote Level 2 copy for clarity (fixed code order, removed "skill that delegates" language, cleaner tagline); redesigned Level 2 from 2-node to 4-node layout — added Human node (role: 'human'), Planner Agent (main), Formatter Skill, Research Agent — showing skill vs sub-agent side by side |
