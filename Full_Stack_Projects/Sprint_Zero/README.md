<div align="center">

# 🚀 Sprint Zero

### Point it at a product. Answer three questions. Get back a complete spec set and a working app.

[![Built with Claude](https://img.shields.io/badge/Built%20with-Claude%20Code-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.com/claude-code)
&nbsp;
![Zero setup](https://img.shields.io/badge/Default-Zero%20setup-2EA043?style=for-the-badge)
&nbsp;
![Time](https://img.shields.io/badge/MVP-~10–20%20min-6E40C9?style=for-the-badge)
&nbsp;
![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)

**Capstone of [Module 2 — Skills, Subagents & Orchestration](../../README.md)** in the Agent Engineering Bootcamp.
Built by **[Yousuf Alvi](https://github.com/yousuf-alvi)** · **[Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/)**

[**Quick start**](#-quick-start) · [**How it flows**](#how-it-flows) · [**The agent team**](#the-agent-team) · [**Build options**](#build-configuration) · [**Demo mode**](#sprint-zero----present-mode)

</div>

---

```
        ┌─ 📋 spec set ─┐        ┌─ ⚙️ backend ─┐
/sprint-zero <url>  ──▶  scoping ──▶  research ──▶  PRD/contract  ──▶  ┤             ├──▶  ✅ QA  ──▶  🟢 running app
                                                                       └─ 🎨 frontend ┘
```

Sprint Zero is a Claude Code kit that gives a developer, founder, or PM a full sub-agent product team on their laptop. You bring the idea and a reference URL. Sprint Zero handles scoping, research, specs, parallel engineering, and QA — and hands back a running product. The default build runs **straight after clone with no account, no keys, and no `.env`.**

---

## 🧩 The problem

Validating a product idea today looks something like this:

- Write a rough PRD, argue about it in Notion
- Hand-wave an API contract, hope the engineers read it the same way
- Wait a week or three for a prototype
- Find out on demo day that the core loop doesn't actually work
- Go back to the PRD

Every step loses signal. By the time a PM sees something clickable, the idea has passed through three games of telephone. Nothing is built to one shared interface. Nothing is testable against the original intent.

Sprint Zero collapses that cycle into one terminal session. The PM stays in the loop the whole way through because the loop is now minutes long, not weeks.

---

## The promise

One command. One reference URL. Three scoping answers. You get:

| | What lands |
|---|---|
| 📋 **A full spec set** | `docs/` — scope, research brief, PRD, decisions, user stories, API contract |
| 🛠️ **A working build** | In the stack you pick — default is a React UI on an Express API with data + auth in local SQLite, so it runs immediately with no account or keys |
| ✅ **QA that matches the build** | Playwright auth dance + core loop for web apps · API tests for services · command runs for CLIs |

⏱️ For an `MVP` scope, expect **ten to twenty minutes** end-to-end.

---

## How it flows

```mermaid
flowchart LR
    A[You]
    B[Scoping]
    C[Spec set]
    D[Parallel build]
    E[QA]
    F[Running product]

    A -->|URL + 3 answers| B
    B --> C
    C --> D
    D --> E
    E --> F
```

One command drives the whole flow. You watch it happen in the Claude Code terminal and can read every spec file before code gets written.

---

## 🎚️ The three scope levels

You pick one when you answer the scoping question. The level is stored in `docs/scope.md` and calibrates every agent downstream.

| Level       | What it produces                                   | Good for                        |
| ----------- | -------------------------------------------------- | ------------------------------- |
| `clickable` | Mock backend, fake data, no auth                   | Pitching and flow reviews       |
| `MVP`       | Real data + real auth, one core loop end-to-end    | Showing the idea actually works |
| `Prod`      | MVP plus error states, validation, loading states  | Handing to 5–10 real users      |

`MVP` is the main demo path for v1. `clickable` is an escape hatch for very early ideation.

## Build configuration

Beyond the scope level, scoping captures three orthogonal choices (all with sensible defaults, so you can ignore them and still get a working app). They're recorded in `docs/scope.md` and the full catalog lives in [.claude/stacks.md](.claude/stacks.md).

| Choice            | Options                                                        | Default      |
| ----------------- | ------------------------------------------------------------- | ------------ |
| **Project type**  | `web-app` · `api-service` · `cli-tool`                        | `web-app`    |
| **Stack profile** | `node-react` (Express+React) · `nextjs` · `python-react` (FastAPI+React) | `node-react` |
| **Data layer**    | `local` (SQLite, zero setup) · `supabase` (hosted Postgres + auth) | `local`   |

The default — `web-app` + `node-react` + `local` — **clones and runs with no external account, no keys, and no `.env`.** Pick `supabase` when you want a real hosted Postgres and auth.

---

## The agent team

Sprint Zero has four sub-agents. You only ever talk to the main session — it orchestrates the rest.

```mermaid
flowchart TD
    User[You]
    Main[Main session]
    TL[tech-lead]
    BE[backend-engineer]
    FE[frontend-engineer]
    QA[qa-engineer]

    User -->|/sprint-zero url| Main
    Main -->|reads specs| TL
    TL -->|build brief| Main
    Main -->|parallel| BE
    Main -->|parallel| FE
    BE --> QA
    FE --> QA
    QA -->|report| Main
    Main -->|delivery summary| User
```

- **tech-lead** reads the spec set, resolves the build configuration, and returns a structured build brief. It does not write code.
- **backend-engineer** builds the API (Express / FastAPI / Next.js) — or a CLI — with data and auth per the chosen data layer.
- **frontend-engineer** builds the UI (React/Vite or Next.js pages) for web apps. Skipped for API services and CLIs.
- **qa-engineer** validates the live build — a Playwright auth dance + core loop for web apps, API tests for services, command runs for CLIs.

Backend and frontend never talk to each other. The API contract is the shared interface.

### Why orchestration lives in the main session

Claude Code does not permit sub-agents to spawn other sub-agents. `tech-lead` could not spawn the engineers even if we wanted it to. So tech-lead is a briefing layer, and the main session is the orchestrator. This also makes the demo clearer — the PM watching the session sees the parallel spawn happen in the main view, not buried inside a sub-agent's output.

---

## 📋 The spec pipeline

Before any code runs, Sprint Zero writes six documents to `docs/`. Each feeds the next.

```mermaid
flowchart LR
    S1[scope.md]
    S2[reference-brief.md]
    S3[prd.md]
    S4[decisions.md]
    S5[user-stories.md]
    S6[api-contract.md]

    S1 --> S2 --> S3 --> S4 --> S5 --> S6
```

| File                 | What's in it                                      |
| -------------------- | ------------------------------------------------- |
| `scope.md`           | Build level, core loop, excludes                  |
| `reference-brief.md` | What the reference product does and how           |
| `prd.md`             | What we're building and why                       |
| `decisions.md`       | Every scope cut, tied to the chosen level         |
| `user-stories.md`    | Acceptance criteria Playwright can drive          |
| `api-contract.md`    | The shared interface both engineers build against |

The pipeline is resumable. Each step checks whether its output file already exists and skips if so. If something fails, re-run `/sprint-zero` and it picks up where it stopped.

---

## 📜 The API contract is law

```mermaid
flowchart TD
    C[api-contract.md]
    C --> BE[backend-engineer<br/>implements]
    C --> FE[frontend-engineer<br/>consumes]
    C --> QA[qa-engineer<br/>validates]
```

Endpoint paths, request shapes, response shapes, status codes — all defined in one file. The engineers build in parallel without ever speaking to each other because they are both building to the same contract. If any agent needs to deviate, it stops and flags it rather than diverging silently.

---

## 🧰 The stack

Pick a stack profile at scoping time, or take the default. Each profile is a small, opinionated set of well-trodden technologies — the kit stays shippable by having a fixed catalog, not by locking you to one option. Full details in [.claude/stacks.md](.claude/stacks.md).

| Stack profile        | Frontend       | Backend            | Default ports        |
| -------------------- | -------------- | ------------------ | -------------------- |
| `node-react` *(default)* | React + Vite | Express (Node.js) | 5173 / 3001          |
| `nextjs`             | Next.js (App Router) — UI + API in one app | 3000          |
| `python-react`       | React + Vite   | FastAPI (Python)   | 5173 / 8000          |

Data and auth come from the **data layer**: `local` (SQLite + a self-issued JWT — nothing to set up) or `supabase` (hosted Postgres + Supabase Auth, free tier fine). Testing is Playwright via Playwright MCP for web apps, HTTP tests for API services, and command runs for CLIs.

---

## 🚀 Quick start

> **TL;DR (default, zero-setup):** `git clone https://github.com/yousuf-labs/sprint-zero && cd sprint-zero && claude` → then `/sprint-zero https://twenty.com`. No account, no keys.

### 1. Prerequisites

- [Node.js](https://nodejs.org) 18+ (and Python 3.11+ if you pick the `python-react` stack)
- [Claude Code](https://claude.com/claude-code) installed and authenticated
- Playwright MCP registered in Claude Code (so QA can drive the browser for web apps). If `claude mcp list` does not show `playwright`, install it and register it under that name.
- **Nothing else for the default `local` data layer** — no account, no keys. A free [Supabase](https://supabase.com) account is needed only if you choose the `supabase` data layer (see below).

### 2. Clone

```bash
git clone https://github.com/yousuf-labs/sprint-zero
cd sprint-zero
```

That's the whole setup for the default (`local`) data layer — no `.env` to fill in.

### 3. Run Sprint Zero

```bash
claude
```

Then in Claude Code:

```
/sprint-zero https://twenty.com/ https://github.com/twentyhq/twenty
```

Pass any product URL you want to reference (a landing page, an open-source tool, a competitor). Sprint Zero will ask you a few questions in one message — answer in a paragraph, no formatting needed, and skip anything you don't care about to take the default:

1. **Project name** — a short slug for this build
2. **What level?** — `clickable`, `MVP`, or `Prod`
3. **What's the core loop?** — the one user flow that must work
4. **What kind of project?** — `web-app`, `api-service`, or `cli-tool`
5. **Which stack?** — `node-react`, `nextjs`, or `python-react`
6. **Where does data live?** — `local` (zero setup) or `supabase`
7. **Anything to exclude?** — features you don't want

### Optional — using the `supabase` data layer

If you answer `supabase` for the data layer, create a free project first and provide four credentials in a `.env` (the default `local` layer skips all of this):

```bash
cp .env.example .env
# then paste the four values below
```

| Where                                                                   | Value                      | Goes into `.env` as        |
| ----------------------------------------------------------------------- | -------------------------- | -------------------------- |
| Settings → API → Project URL                                            | `https://xxxx.supabase.co` | `SUPABASE_URL`             |
| Settings → API Keys → Publishable key                                   | `sb_publishable_...`       | `SUPABASE_PUBLISHABLE_KEY` |
| Settings → API Keys → Secret key (click Reveal)                         | `sb_secret_...`            | `SUPABASE_SECRET_KEY`      |
| Settings → Database → Connection string → URI (Session mode, port 5432) | `postgresql://postgres...` | `DATABASE_URL`             |

Use the new **API Keys** tab, not **Legacy**. Enable **Authentication → Providers → Email**. `DATABASE_URL` lets Sprint Zero create tables automatically — no manual SQL.

#### Example answer — a mini CRM referenced from [twenty.com](https://twenty.com/)

> **What level are we building?**
> MVP
>
> **What's the core loop?**
> The core loop is: user creates a contact (name, email, company), creates a deal linked to that contact (name, value, stage), and moves the deal across pipeline stages (Lead → Qualified → Proposal → Closed Won / Closed Lost). That's what a MVP has to prove.
>
> **Anything to exclude?**
> Companies as a separate entity (roll company into the contact record as a text field), custom fields, activities and notes on records, email integration, import / export, filters and saved views, search, reporting and dashboards, tasks, calendar, and any admin / settings UI.

Notice how the excludes list is long and specific. That's the point — naming what you're cutting is how you keep a `MVP` to ten to twenty minutes and stop the agents from quietly building a full CRM.

Sprint Zero handles the rest.

### The app launches itself

Once QA passes, `/sprint-zero` automatically installs dependencies, seeds demo data, starts the build in the background, and opens it in your browser (cross-platform — `open`/`xdg-open`/`wslview`/`start`). The exact ports follow the stack profile (e.g. `node-react`: frontend 5173, backend 3001; `python-react`: backend 8000; `nextjs`: one app on 3000). For the `local` data layer there are no keys to wire — the seed creates a SQLite file and a demo user, and the launch summary prints the login. For `supabase`, it also wires the frontend's `VITE_` env from your root `.env`.

You'll land on a polished marketing page — click **Log in** and use the credentials from the launch summary to enter the product. The summary prints the exact commands to stop the servers for your build.

Pass `--no-launch` to `/sprint-zero` if you'd rather wire it up by hand.

---

## Start the app manually

You can skip auto-launch with `/sprint-zero <url> --no-launch`, or run these steps any time afterward. Commands follow your stack profile — the `node-react` + `local` default looks like this:

```bash
# Terminal 1 — backend
cd server
npm install       # first run only
node seed.js      # creates the SQLite tables + demo data (first run only)
node index.js     # API on http://localhost:3001

# Terminal 2 — frontend
cd client
npm install       # first run only
npm run dev       # app on http://localhost:5173
```

The seed script prints the demo user's email and password. Use those to log in.

> With the `local` data layer the frontend needs no env file — it talks to the backend's own `/auth` endpoints. For `supabase`, copy `client/.env.example` to `client/.env` and set `VITE_SUPABASE_URL` / `VITE_SUPABASE_PUBLISHABLE_KEY` (Vite only exposes `VITE_`-prefixed vars to the browser). For `python-react` the backend is `uvicorn main:app --port 8000`; for `nextjs` it's a single `npm run dev` on port 3000.

---

## What the seed script does

```mermaid
flowchart LR
    A[seed] --> B[Create tables<br/>SQLite, or migrate for Supabase]
    B --> C[Create demo user<br/>local hash, or Supabase admin]
    C --> D[Insert seed rows]
    D --> E[Print credentials]
```

It is idempotent. Running it twice is safe. Tables are created with `IF NOT EXISTS`. The demo user is checked before creation. Seed rows are cleared and re-inserted each run. For the `local` data layer this writes a SQLite file with no external calls; for `supabase` it migrates the schema and creates the user via the admin client.

---

## Repo layout

```
sprint-zero/
├── .claude/
│   ├── commands/                    ← slash commands (the pipeline)
│   │   ├── sprint-zero.md             main orchestrator
│   │   ├── sprint-zero-scope.md       scoping question → scope.md
│   │   ├── explain-me-a-repo.md       research → reference-brief.md
│   │   ├── prd-generator.md           → prd.md
│   │   ├── decisions-writer.md        → decisions.md
│   │   ├── user-story-writer.md       → user-stories.md
│   │   └── api-contract-writer.md     → api-contract.md
│   ├── stacks.md                   ← build-configuration catalog (read by every agent)
│   └── agents/                      ← sub-agents (the build layer)
│       ├── tech-lead.md
│       ├── backend-engineer.md
│       ├── frontend-engineer.md
│       └── qa-engineer.md
├── docs/                            ← generated specs (gitignored; filled at runtime)
├── examples/
│   └── ghost-lite/                  ← the worked example: a real run against ghost.org, committed as-is
├── server/ + client/  (or app/, or cli/)  ← the build, per stack profile (gitignored; created at runtime)
├── .env.example                     ← only for the supabase data layer (local needs none)
├── .gitignore
├── CLAUDE.md                        ← project instructions for Claude Code
├── LICENSE
├── plan.md                          ← phased build plan for this repo
└── README.md
```

On a fresh clone you'll only see the committed items. The spec docs and the build directories are populated when `/sprint-zero` runs.

---

## Re-running pieces individually

Every spec command works on its own. Delete the target file first if you want to regenerate it.

```
/sprint-zero-scope      re-run scoping
/explain-me-a-repo      re-research the reference
/prd-generator          regenerate the PRD
/decisions-writer       regenerate decisions
/user-story-writer      regenerate stories
/api-contract-writer    regenerate the contract
```

### Flags on `/sprint-zero`

| Flag          | Effect                                                                                     |
| ------------- | ------------------------------------------------------------------------------------------ |
| `--fresh`     | Delete `docs/` and regenerate all specs from scratch                                       |
| `--rebuild`   | Delete `server/` and `client/` and rebuild from existing specs                             |
| `--no-launch` | Skip auto-launch at the end. Start the servers manually afterwards.                        |
| `--present`   | Boot the presenter UI in the browser. Collects scoping via a form and shows live progress. |

Example: `/sprint-zero https://example.com --fresh`

### Named failure states

If anything goes wrong, `/sprint-zero` prints a named state and a recovery instruction.

| State                | Meaning                         | Recovery                                      |
| -------------------- | ------------------------------- | --------------------------------------------- |
| `SCOPE_NEEDED`       | `docs/scope.md` was not written | Re-run with a reachable URL                   |
| `DISCOVERY_NEEDED`   | Reference brief failed          | Fix connectivity, re-run                      |
| `SPEC_INCOMPLETE`    | A spec file is missing          | Run the failing command directly, then re-run |
| `BUILD_BRIEF_NEEDED` | tech-lead flagged a doc problem | Fix the doc, re-invoke tech-lead              |
| `BUILD_NEEDED`       | An engineer failed              | Re-spawn the failing engineer, then QA        |
| `QA_NEEDED`          | Tests failed                    | Fix the reported issues, re-spawn QA          |
| `LAUNCH_FAILED`      | Auto-launch at the end failed   | Start the servers manually (see above)        |

---

## Sprint Zero — `--present` mode

For walking PMs or non-developers through Sprint Zero, run it with `--present`:

```
/sprint-zero https://twenty.com https://github.com/twentyhq/twenty --present
```

A polished local UI boots at `http://localhost:4000` and opens in the browser. Use it for three phases of the demo:

1. **About** — explains scope levels, the agent topology, and the spec pipeline. Stay here while you talk through the concept.
2. **Start a run** — a form replaces the terminal scoping conversation: level, project type, stack, data layer, core loop, excludes. Submitting it writes `docs/scope.md` in the same format `/sprint-zero-scope` produces.
3. **Live** — a vertical pipeline timeline updates in real time as each spec doc lands. Click any completed step to view its rendered markdown. The build phase shows backend and frontend as side-by-side cards. When the run finishes, the screen reveals the running app's URL with a copyable demo login.

The presenter is a permanent committed part of the kit, not a one-off. The terminal narration is unchanged, so you can also screen-share the Claude Code window alongside the UI.

To boot the presenter on its own (without a Sprint Zero run):

```
cd presenter && npm install && npm run build && npm start
```

---

## Worked example: ghost-lite

[`examples/ghost-lite/`](examples/ghost-lite/) is one complete Sprint Zero run, copied from the pipeline's output without edits: the six spec docs, the Express + SQLite backend, the React client, and QA's integration test. The reference was [Ghost](https://ghost.org), the open-source publishing platform, at MVP / web-app / node-react / local, plus one feature Ghost does not have: an "Ask me" box that answers reader questions from the site's own posts with citations (SQLite full-text search; Claude writes the answer only when `ANTHROPIC_API_KEY` is set, otherwise the box returns the matching passages). The seeded site is the Traversaal.ai blog, ten real articles, so Ask me has something worth answering from on first launch.

Run it:

```
cd examples/ghost-lite/server && npm install && node index.js      # :3001, seeds on start
cd examples/ghost-lite/client && npm install && npm run dev        # :5173
```

Demo login `demo@traversaal.ai` / `inkwell-demo`. Public site at `http://localhost:5173/s/traversaal-ai`. See [`examples/ghost-lite/README.md`](examples/ghost-lite/README.md) for what QA verified and how.

The same run is committed under `presenter/sample/` so the presenter can play it back. Start the presenter with no run on disk and it shows the sample automatically; with a live run on disk, the **Run demo** button in the top bar switches to the sample and **Exit demo** switches back. `SPRINT_ZERO_DEMO=0` turns the automatic fallback off (the button still works).

---

## 🩺 Troubleshooting

**The page shows "Failed to load data" (or similar).** Tables aren't created yet. Re-run the seed command for your build (e.g. `cd server && node seed.js`).

**The server crashes on startup (supabase only).** `server/.env` is missing or incomplete. The error message names the missing key. On the `local` data layer there is no `.env` to misconfigure.

**Every API call returns 401 (supabase only).** New Supabase projects issue ES256 tokens, not RS256. `middleware/auth.js` must accept both, and the JWKS URI must be `{SUPABASE_URL}/auth/v1/.well-known/jwks.json` (not `/auth/v1/jwks`). On `local`, a 401 usually means the stored JWT is missing or the dev secret changed — log in again.

**QA didn't run the browser tests.** Either no browser MCP is registered (`claude mcp list` should show `playwright` or `brave-devtools`; register one and re-spawn `qa-engineer`, or let QA fall back to its Playwright script), or the project type is `api-service`/`cli-tool`, which have no browser tests by design.

**Seed says "relation/table does not exist".** On `local`, just re-run the seed — it creates the SQLite schema. On `supabase`, `DATABASE_URL` is wrong: get it from Settings → Database → Connection string → URI, Session mode, port 5432 (`postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`).

---

## What's not in v1

Deliberate cuts, tracked in [plan.md](plan.md) as v2 candidates:

- More stacks beyond the three profiles (e.g. Vue, Django, Go) — the catalog in [.claude/stacks.md](.claude/stacks.md) is where you'd add one
- Deployment automation — Sprint Zero produces code, you deploy it
- Multi-user collaboration in the generated product
- Design system integration — the generated UI is utilitarian
- Payment / Stripe integration
- File upload beyond what the chosen data layer gives you
- A hosted version of Sprint Zero itself

---

## Status

- Phase 1 — Foundation — complete
- Phase 2 — Scoping and discovery layer — complete
- Phase 3 — Build layer — complete
- Phase 4 — Kickoff orchestrator — complete
- Phase 5 — Worked example (ghost-lite, a real run against ghost.org) — complete
- Phase 6 — Polish for launch — not started

See [plan.md](plan.md) for the full roadmap.

---

## 👥 Authors

- **[Yousuf Alvi](https://github.com/yousuf-alvi)** · [LinkedIn](https://www.linkedin.com/in/yousufalvi/) — original author
- **[Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/)** — course integration ([Agent Engineering Bootcamp](https://maven.com/boring-bot/advanced-llm))

Originally published at [yousuf-labs/sprint-zero](https://github.com/yousuf-labs/sprint-zero). MIT licensed — see [LICENSE](LICENSE).

<div align="center"><sub>Part of the <a href="../../README.md">Agent Engineering Bootcamp</a> · Module 2 capstone</sub></div>
