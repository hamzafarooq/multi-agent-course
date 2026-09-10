# Sprint Zero — CLAUDE.md

> This file is Claude Code's briefing document for the Sprint Zero repo.
> Read this before touching any file. It is the single source of truth for
> what this project is, how it's wired, and what the rules are.

---

## What is Sprint Zero?

Sprint Zero is a cloneable Claude Code kit that turns a reference URL plus three scoping answers into a complete spec set and a working product. The user points Sprint Zero at something similar to what they want to build, answers one multi-part scoping question, and a team of sub-agents produces:

- A full spec set in `docs/` (scope, reference brief, PRD, decisions, user stories, API contract)
- A working build whose stack is chosen at scoping time (see "Build configuration" below) — by default a local SQLite-backed Express + React app that runs with no external account
- QA calibrated to the build — browser-driven for web apps, API-level for services, command runs for CLIs

The audience is PMs, founders, and non-developers who can follow terminal output but don't write code. Every decision in this repo prioritises:

- Clarity over cleverness
- Demo-readiness over production hardening
- Visible outputs over elegant internals
- The user's judgement over inferred defaults

---

## Scope levels

The user picks one of three levels up front. The scope level drives every downstream agent's behaviour.

| Level       | What it produces                                                                                                  |
| ----------- | ----------------------------------------------------------------------------------------------------------------- |
| `clickable` | Mock backend, fake data, no auth. Useful for pitching and flow reviews.                                           |
| `MVP`       | Real data + real auth via the chosen data layer, one core loop works end-to-end. The main v1 target.              |
| `Prod`      | MVP plus error boundaries, loading states, input validation, and a happy path + one error path test per loop.     |

`docs/scope.md` is the lever that carries this choice — and the build configuration above — through the pipeline. The scope level is independent of the data layer: `clickable` is mock-only regardless, while `MVP`/`Prod` use whichever data layer was chosen.

---

## Build configuration

The build is configured by three orthogonal choices captured during scoping, on top of the scope level. The full catalog — concrete dirs, ports, run commands, and test strategy for every combination — lives in `.claude/stacks.md`, which every agent reads. Do not hardcode a stack assumption anywhere else.

- **Project type** — `web-app` (UI + API), `api-service` (API only, no frontend), or `cli-tool` (a command-line program).
- **Stack profile** — `node-react` (Express + React/Vite), `nextjs` (one Next.js app, UI + API together), or `python-react` (FastAPI + React/Vite).
- **Data layer** — `local` (SQLite + a self-issued JWT, **zero external setup**) or `supabase` (hosted Postgres + Supabase Auth, needs a `.env`).

**Default: `web-app` + `node-react` + `local`.** That default clones and runs with no account, no keys, and no `.env`. Supabase is opt-in. `docs/scope.md` records all three choices and carries them through the pipeline alongside the scope level.

Testing is Playwright (via Playwright MCP) for web apps, HTTP integration tests for API services, and command-output assertions for CLIs.

---

## Architecture, one line

URL → scoping conversation → spec set (PRD, decisions, stories, contract) → parallel build (backend + frontend) → QA with browser-driven tests → working product.

---

## Repo structure

```
sprint-zero/
├── CLAUDE.md                 ← you are here
├── README.md                 ← public-facing description
├── plan.md                   ← phased build plan for this repo itself
├── LICENSE                   ← MIT, Yousuf Alvi
├── .env.example              ← only needed for the supabase data layer (local needs none)
├── .gitignore
├── .claude/
│   ├── stacks.md             ← the build-configuration catalog (read by every agent)
│   ├── commands/             ← slash commands (Phase 2)
│   └── agents/               ← sub-agents (Phase 3)
├── docs/                     ← generated spec files live here per run
└── examples/
    └── mini-twenty/          ← worked example (Phase 5, committed build)
```

Files generated at runtime (per user run):

- `docs/scope.md` — scoping answers, structured
- `docs/reference-brief.md` — extracted brief of the reference URL
- `docs/prd.md` — product requirements
- `docs/decisions.md` — scope cuts and tradeoffs, tied to the chosen level
- `docs/user-stories.md` — user stories
- `docs/api-contract.md` — the contract all agents build to
- `server/` / `client/` (node-react, python-react) or one `app/` (nextjs) or `cli/` (cli-tool) — the build, per the resolved stack profile
- `*.db` — the SQLite file for the `local` data layer (gitignored)
- `.claude/settings.local.json` — demo-time permissive settings, gitignored

---

## Agent topology

Sprint Zero's build layer has one briefing sub-agent (tech-lead) and three worker sub-agents (two engineers, one QA). **The main Claude Code session is the orchestrator — it is the only thing that spawns sub-agents.** tech-lead does not spawn anyone; it reads specs and hands a build brief back to the main session, which then spawns the workers. This is a hard Claude Code constraint, not a stylistic choice: a sub-agent cannot spawn another sub-agent (the `Task` tool is stripped from nested contexts), and tech-lead is declared with `tools: Read` only. See "Build orchestration pattern" below for the full rationale.

```
You
  │
  └─ main session  (the orchestrator — the only thing that spawns)
        │
        ├─ 1. invoke tech-lead ........ reads specs → returns a build brief
        │                               (tools: Read only — no code, no spawning)
        │
        ├─ 2. spawn IN PARALLEL ......  backend-engineer   (API or CLI, per stack profile + data layer)
        │                              frontend-engineer  (web-app only; React/Vite or Next.js pages)
        │
        └─ 3. after both finish ......  qa-engineer        (browser / API / CLI, per project type)
```

Which engineers run depends on the project type — `frontend-engineer` is spawned only for `web-app`.

### tech-lead (briefing only — does not spawn)

- Reads `docs/scope.md` (scope level + build config), `docs/prd.md`, `docs/api-contract.md`, `docs/decisions.md`, and resolves the config against `.claude/stacks.md`
- Returns a build brief: what it understood, the resolved dirs/ports, and a **recommended** execution order (which engineers the main session should spawn, and in what order)
- Does **not** spawn engineers or QA, and does not write application code — `tools: Read` only. The main session acts on the recommendation.

### backend-engineer

- Builds the API (Express / FastAPI / Next.js route handlers) or, for `cli-tool`, a command-line program — per the resolved stack profile
- Data access + auth per the data layer: `local` → SQLite + a self-issued JWT (`/auth/*` endpoints), `supabase` → `@supabase/supabase-js` + JWKS verification
- Seed script creates the schema (SQLite or via migration) and a demo user with realistic data
- Builds strictly to `docs/api-contract.md`

### frontend-engineer (web-app only)

- Builds the UI — React + Vite in `client/`, or pages inside the Next.js `app/`
- Auth per the data layer: `local` → calls the backend `/auth/*`; `supabase` → Supabase Auth SDK. Login, signup, session context, protected route wrapper
- Product screens come from `docs/user-stories.md` and the contract
- Form patterns standardised so QA can drive them

### qa-engineer

- `web-app`: the full auth dance (signup, session, logout, login, protected route, 401) + core loop in a real browser via Playwright
- `api-service`: contract + HTTP integration tests, auth verified at the API level (no browser)
- `cli-tool`: runs the CLI with sample args and asserts on stdout/exit codes
- At `Prod` scope, adds one error-path test per loop. Reports pass/fail back to the main session, which writes the delivery summary

---

## Key files Claude Code should read first

When starting a session on this repo, read in this order:

1. `CLAUDE.md` (this file) — project context and rules
2. `plan.md` — what's built, what's next, what's out of scope
3. `README.md` — the public-facing story, to stay consistent with it

When a user invokes `/sprint-zero <url>`, the orchestrator adds:

4. `docs/scope.md` (once scoping is complete)
5. `docs/prd.md`
6. `docs/api-contract.md`
7. `docs/decisions.md`

---

## Rules for all agents

1. **The API contract is law.** `docs/api-contract.md` is the shared interface. Backend implements it. Frontend consumes it. QA validates against it. If it's wrong or missing, stop and flag it — do not work around it silently.
2. **Read the scope file.** `docs/scope.md` tells you which of the three levels you're building for. Calibrate your output to that level. Do not add polish above the chosen level.
3. **Keep files small and readable.** Non-developers will read this. Someone may record a Loom over it.
4. **No TypeScript unless the scope file says so.** Plain JavaScript by default.
5. **No exotic dependencies.** If it needs its own README to install, pick something simpler.
6. **Seed data must be realistic.** Real-sounding names, companies, and records. Not "Test User 1".
7. **Every endpoint returns consistent JSON.** Structure defined in `docs/api-contract.md`.
8. **Log decisions.** If you make a tradeoff, add a line to `docs/decisions.md`.
9. **Narrate handoffs.** Orchestrator and engineers: never go silent for long stretches. The user is watching.
10. **Do less when in doubt.** A working 80% at the chosen scope beats a broken 100%.

---

## Conventions

- Sentence case for headings in markdown, not Title Case.
- No emoji in technical output.
- Prose over bullet lists unless structure genuinely helps.
- Numbered steps when sequence matters; otherwise prose.
- One idea per paragraph.

---

## Context for Claude Code

- Builder: Yousuf Alvi (co-facilitator on Hamza Farooq's Claude Code for PMs cohort)
- Audience for this repo: developers, founders, and PMs using Claude Code
- This repo's own build is tracked in `plan.md`, phase by phase. Each phase is a single chat session. Do not skip ahead.
- Mini Twenty is Sprint Zero's worked example (Phase 5). Until then, `examples/` is intentionally empty.

---

## Build orchestration pattern

Sprint Zero uses a two-tier pattern that respects Claude Code's sub-agent limitations:

- `tech-lead` is a **briefing sub-agent** — reads specs, returns a build brief, does NOT spawn engineers
- The **main Claude Code session** is the orchestrator — spawns backend-engineer and frontend-engineer in parallel, then qa-engineer after both complete
- `backend-engineer`, `frontend-engineer`, `qa-engineer` are **worker sub-agents** — isolated context, no sub-agent spawning themselves

When running a build, invoke tech-lead first for the brief, then follow the recommended execution order it returns.
