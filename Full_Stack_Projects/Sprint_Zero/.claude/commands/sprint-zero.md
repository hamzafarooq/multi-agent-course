# /sprint-zero

You are the Sprint Zero orchestrator. Your job: take a company URL (and optional repo URL) and run the full flow — scoping, discovery, spec generation, build briefing, parallel engineering, and QA — producing a working product from a single command.

## Arguments

`$ARGUMENTS` may contain URLs, flags, or nothing:

- First URL (optional if running interactively): the company or product being referenced
- Second URL (optional): a specific repo to reverse-engineer
- `--fresh` (optional flag): delete `docs/` before starting so all spec steps run fresh
- `--rebuild` (optional flag): delete `server/` and `client/` before the build phase, forcing a clean rebuild
- `--no-launch` (optional flag): skip the auto-launch step at the end. The user will start the servers manually.
- `--present` (optional flag): boot the Sprint Zero presenter UI in the browser, collect scoping via the form instead of the terminal Q&A, and write a status file at every phase transition so the UI updates live. Used for demoing Sprint Zero to non-developers. See "Step 0 — Presenter mode" below.

If `$ARGUMENTS` is empty, trigger the guided intake (see Step 1). If URLs are present, run non-interactively as described.

## Resumability

Before each spec-writing step, check whether its expected output file already exists in `docs/`. If it does, print a skip message and move to the next step. This makes `/sprint-zero` safe to re-run after a partial failure — it picks up from where the previous run stopped.

The build and QA phases resume from `.sprint-zero/status.json`, which this command writes at every phase transition whether or not `--present` was passed (see Step 0c). At the start of a run, if that file exists, read it and print `Resuming from phase: <phase>.` Then:

- `build.backend` is `"done"` and the backend dir exists → do not re-spawn backend-engineer.
- `build.frontend` is `"done"` and the frontend dir exists → do not re-spawn frontend-engineer.
- `phase` is `"launch"` or `"done"` and the code dirs exist → skip straight to Step 11.
- `phase` is `"failed"` → read `failure.state`, print its recovery instruction, and resume at the step that state names.

Anything marked `"running"` when the previous session broke is treated as not done: re-spawn it. Engineers write their dir from scratch when it is missing and build on what exists when it is present, so a re-spawn after a partial build is safe. `--fresh` and `--rebuild` also delete `.sprint-zero/status.json`.

If `--fresh` was passed, delete `docs/` and `.sprint-zero/status.json` before step 2 so all spec steps run from scratch.

If `--rebuild` was passed, delete `server/` and `client/` (or `app/`, `cli/`) and reset `build` in `.sprint-zero/status.json` before step 9 so the full build runs from scratch.

## Named failure states

If any step fails unrecoverably, print the named state and a recovery instruction, then stop. Do not continue past a failure — a broken spec will produce a broken build.

```
STATE: SCOPE_NEEDED       — re-run /sprint-zero <url> with a reachable URL, or run /sprint-zero-scope <url> directly then re-run /sprint-zero <url>
STATE: DISCOVERY_NEEDED   — fix connectivity or web-research tool access (Brave Search MCP, WebSearch/WebFetch, or a browser MCP), then re-run /sprint-zero <url> to resume
STATE: SPEC_INCOMPLETE    — run the failing command directly (/prd-generator, /decisions-writer, etc.), then re-run /sprint-zero <url> to resume from the build step
STATE: BUILD_BRIEF_NEEDED — fix the flagged doc issue reported by tech-lead, then re-invoke the tech-lead sub-agent manually
STATE: BUILD_NEEDED       — re-spawn the failing engineer sub-agent directly, then spawn qa-engineer once both engineers complete
STATE: QA_NEEDED          — fix the contract mismatches or test failures reported by qa-engineer, then re-spawn qa-engineer
```

---

## Step 0 — Presenter mode (only if `--present` was passed)

Skip this whole step unless `$ARGUMENTS` contains `--present`.

**0a. Boot the presenter server.**

Run, in this exact order:

```bash
cd presenter && npm install --silent
cd presenter && npm run build
mkdir -p .sprint-zero
nohup node presenter/server/index.mjs > .sprint-zero/presenter.log 2>&1 &
```

`npm install` is idempotent — npm skips it instantly if `presenter/node_modules` is already populated. The build is also idempotent at Vite's level. The server backgrounds itself; do not block the chat on it.

Wait two seconds, then read `.sprint-zero/presenter.json` to learn the port the server bound to (it auto-picks 4000+ if 4000 is taken). The file looks like `{"url":"http://localhost:4000","port":4000}`.

**0b. Open the browser.**

Run `open <url>` (macOS) or `xdg-open <url>` (linux), where `<url>` is the URL from `presenter.json`. If `open` fails, do not abort — just print the URL so the user can click it.

Print:

> Presenter UI is up at <url>. Walk through the About section to teach the flow, then click "Start a run" to enter the scoping form.

**0c. Status helper for the rest of this run. This sub-step runs on every invocation, with or without `--present`.**

Whenever a "presenter status update" is mentioned in steps 1–11 below, write a JSON file at `.sprint-zero/status.json` with this shape (keys are optional unless required by the specific step). The file is the run's checkpoint: the presenter UI reads it when present, and the Resumability rules above read it after a break.

```json
{
  "phase": "<one of: idle | waiting-for-scope | scoping | research | prd | decisions | stories | contract | brief | building | qa | launch | done | failed>",
  "step": "<short slug, e.g. 'reference-brief'>",
  "stepNumber": <1-10>,
  "message": "<one short sentence the UI shows in the header>",
  "timestamp": "<ISO 8601>",
  "docs": ["scope.md", "reference-brief.md", ...],
  "build": { "backend": "idle|running|done|failed", "frontend": "idle|running|done|failed" },
  "qa": { "contractBackend": "pending|pass|fail", "contractFrontend": "pending|pass|fail", "integration": {"passed": 0, "total": 0}, "authDance": "pending|pass|fail|n/a", "coreLoop": "pending|pass|fail" },
  "appUrl": null,
  "credentials": null,
  "projectName": null,
  "failure": null
}
```

Use `bash` with `cat <<EOF > .sprint-zero/status.json … EOF` to overwrite atomically. Always include `phase`, `message`, and `docs` (the list of files currently in `docs/`). Other keys are additive.

If `--present` was NOT passed, still write every status update (it is one small file and it is what makes a broken run resumable); only skip booting the UI in 0a and 0b.

**0d. Project name.**

If the presenter UI submitted scoping, `.sprint-zero/meta.json` will exist and contain `projectName`. Read it and use that as the project name for the delivery summary in step 10. If the file is missing or empty, fall back to the company URL.

---

## Step 1 — Validate and prepare

**If `$ARGUMENTS` contains URLs**, extract the first URL as the company URL and the second (if present) as the repo URL. If either URL does not start with `http://` or `https://`, prepend `https://` before proceeding. Skip to the `--fresh` / `--rebuild` handling below.

**If `$ARGUMENTS` is empty**, ask the user exactly this, in one message:

> Before we kick off, three things — answer in a paragraph, no need to format:
>
> 1. **Project name** — a short slug for this build (e.g. `linear-clone`, `mini-crm`). Used to label the delivery summary.
> 2. **Company or product URL** — the reference you want Sprint Zero to study.
> 3. **Repo URL** — a specific repo to reverse-engineer alongside the product site, or "none".

Wait for the reply. Parse it for the three fields. If a URL is given without a scheme, prepend `https://`. Store the project name for use in the delivery summary. Use the company URL and optional repo URL as inputs to all downstream steps, exactly as if they had been passed as `$ARGUMENTS`.

If `--fresh` was passed, delete the `docs/` directory and confirm deletion before continuing.

If `--rebuild` was passed, delete `server/` and `client/` and confirm deletion before continuing.

Print:

> Sprint Zero starting. Project: [project name or URL if no name given]. Scope level will be set in step 2.

---

## Step 1b — Data-layer preflight (conditional)

Sprint Zero supports two data layers, chosen during scoping (Step 2) and recorded in `docs/scope.md`: `local` (SQLite, zero setup) and `supabase` (hosted Postgres + auth). See `.claude/stacks.md` for the full description.

**This preflight only applies to the `supabase` data layer, and the data layer is not known until scoping completes.** So:

- If `docs/scope.md` already exists, read its **Data layer** now and run the Supabase check below only if it says `supabase`.
- If `docs/scope.md` does not exist yet, **defer this entire step** — run it immediately after Step 2 writes `docs/scope.md`, and only if the chosen data layer is `supabase`.
- If the data layer is `local`, **skip this step entirely** and print: `Data layer: local (SQLite). No external setup needed.`

### Supabase check (only when data layer is `supabase`)

Check whether a `.env` file exists at the project root and contains non-empty values for `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_SECRET_KEY`, and `DATABASE_URL`.

If the file is missing or any key is empty, print this block exactly and wait for the user to confirm before continuing:

> **Supabase setup required before we build.**
>
> Sprint Zero needs a live Supabase project. Here's what to do — takes about 3 minutes:
>
> 1. Go to [supabase.com](https://supabase.com) → New project. Choose any name and region.
> 2. Once created, go to **Settings → API**. Copy:
>    - **Project URL** → `SUPABASE_URL`
>    - **anon / public** key → `SUPABASE_PUBLISHABLE_KEY`
>    - **service_role** key → `SUPABASE_SECRET_KEY`
> 3. Go to **Settings → Database → Connection string → URI** (choose Session mode, port 5432). Copy the full URL → `DATABASE_URL`. It looks like: `postgresql://postgres.[ref]:[password]@aws-0-[region].pooler.supabase.com:5432/postgres`
> 4. Go to **Authentication → Providers → Email** and make sure it is enabled.
> 5. Create a `.env` file at the project root (copy `.env.example` and fill in all four values).
>
> Reply "ready" when done and Sprint Zero will continue.

After the user replies "ready", re-check `.env`. If it still looks empty, print the same block again and wait. Do not proceed to scoping until all four keys are present.

If the file exists and all four keys are non-empty, print:

> `.env` found with Supabase credentials. Continuing.

Note: database tables are created automatically when `node seed.js` runs — no manual SQL pasting required.

---

## Step 2 — Scoping

Check whether `docs/scope.md` exists. If it does, print:

> `docs/scope.md` already exists — skipping step 2. Delete it or use --fresh to regenerate.

If it does not exist:

**If `--present` was passed** — do NOT run the terminal scoping conversation. Instead:

1. Write a presenter status update with `phase: "waiting-for-scope"`, `step: "scope"`, `stepNumber: 1`, `message: "Waiting for scope via the presenter UI."`. The UI will land on its scoping form.
2. Print to the terminal: `Waiting for scope via <presenter-url>. The form will write docs/scope.md when submitted.`
3. Poll for `docs/scope.md` to exist, checking once every 2 seconds, for up to 15 minutes. Use `bash`: `for i in $(seq 1 450); do [ -f docs/scope.md ] && break; sleep 2; done`.
4. When the file appears, print `Scope received via presenter UI.` and continue. (The UI's `/api/scope` endpoint already wrote the file in the same format `/sprint-zero-scope` produces, including the Build configuration block. Then run Step 1b's data-layer preflight if the scope says `supabase`.)
5. If the loop times out without the file appearing, print `STATE: SCOPE_NEEDED — submit the scoping form in the presenter, or run /sprint-zero again without --present.` and stop.

**Otherwise (no `--present`)** — Read `.claude/commands/sprint-zero-scope.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says. Pass the URLs from `$ARGUMENTS` as the arguments that command expects.

If `docs/scope.md` is not written by the end of this step, print `STATE: SCOPE_NEEDED` with recovery instructions and stop.

**Presenter status update** (only when `--present`): write `phase: "research"`, `step: "reference-brief"`, `stepNumber: 2`, `message: "Researching the reference."`, and refresh the `docs` array.

---

## Step 3 — Reference brief

Check whether `docs/reference-brief.md` exists. If it does, print:

> `docs/reference-brief.md` already exists — skipping step 3. Delete it or use --fresh to regenerate.

If it does not exist:

Read `.claude/commands/explain-me-a-repo.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says. Pass the URLs from `$ARGUMENTS` as the arguments that command expects.

If `docs/reference-brief.md` is not written by the end of this step, print `STATE: DISCOVERY_NEEDED` with recovery instructions and stop.

---

## Step 4 — PRD

Check whether `docs/prd.md` exists. If it does, print:

> `docs/prd.md` already exists — skipping step 4. Delete it or use --fresh to regenerate.

If it does not exist:

Read `.claude/commands/prd-generator.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says.

If `docs/prd.md` is not written by the end of this step, print `STATE: SPEC_INCOMPLETE` with recovery instructions and stop.

---

## Step 5 — Decisions

Check whether `docs/decisions.md` exists. If it does, print:

> `docs/decisions.md` already exists — skipping step 5. Delete it or use --fresh to regenerate.

If it does not exist:

Read `.claude/commands/decisions-writer.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says.

If `docs/decisions.md` is not written by the end of this step, print `STATE: SPEC_INCOMPLETE` with recovery instructions and stop.

---

## Step 6 — User stories

Check whether `docs/user-stories.md` exists. If it does, print:

> `docs/user-stories.md` already exists — skipping step 6. Delete it or use --fresh to regenerate.

If it does not exist:

Read `.claude/commands/user-story-writer.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says.

If `docs/user-stories.md` is not written by the end of this step, print `STATE: SPEC_INCOMPLETE` with recovery instructions and stop.

---

## Step 7 — API contract

Check whether `docs/api-contract.md` exists. If it does, print:

> `docs/api-contract.md` already exists — skipping step 7. Delete it or use --fresh to regenerate.

If it does not exist:

Read `.claude/commands/api-contract-writer.md` and follow its instructions exactly. Do not summarise or simulate — read the actual file and do what it says.

If `docs/api-contract.md` is not written by the end of this step, print `STATE: SPEC_INCOMPLETE` with recovery instructions and stop.

---

## Step 8 — Build brief

Print:

> Spec set complete. Invoking tech-lead for the build brief.

Invoke the `tech-lead` sub-agent. The one load-bearing instruction in the prompt is that the contract is law and deviations are not allowed. Tech-lead reads `docs/` itself to get the scope level, core loop, build configuration (project type / stack profile / data layer), and the full spec set, and resolves the concrete dirs, ports, and run commands against `.claude/stacks.md`. Its brief states which engineers to spawn and the resolved ports — use those, do not assume the node-react defaults.

If tech-lead reports a missing or malformed doc, print `STATE: BUILD_BRIEF_NEEDED` with recovery instructions and stop.

Once tech-lead returns its build brief, print it so the user can read it before the build starts.

---

## Step 9 — Parallel build and QA

**Which engineers to spawn depends on the project type** (from `docs/scope.md`, resolved against `.claude/stacks.md`):

- `web-app` — spawn `backend-engineer` **and** `frontend-engineer` in parallel.
- `api-service` or `cli-tool` — spawn `backend-engineer` **only** (it owns the API or the CLI source). There is no frontend; skip `frontend-engineer`.
- `nextjs` profile — backend-engineer scaffolds the single Next.js app and its `app/api` routes, then frontend-engineer builds the pages on top of the same project. They still run in the same turn for `web-app`; both write into one app, so the brief from tech-lead will note the sequencing.

Print (adjust wording to the engineers you're actually spawning):

> Build brief received. Spawning the build team in parallel.

Spawn the engineer(s) in the same turn. Pass the scope level, core loop, **and the build configuration (project type / stack profile / data layer)** in each prompt. The one load-bearing instruction: the contract is law and deviations are not allowed. The workers read `docs/` and `.claude/stacks.md` themselves via relative paths.

Wait for each spawned engineer to return its exact completion message:
- Backend: "Backend complete. All endpoints match docs/api-contract.md." (for `cli-tool`, "CLI complete. All commands match docs/api-contract.md.")
- Frontend (web-app only): "Frontend complete. All API calls match docs/api-contract.md."

If any returns anything other than its completion message, print `STATE: BUILD_NEEDED` with recovery instructions and stop.

Once the spawned engineers complete, print:

> Build complete. Spawning qa-engineer.

Spawn `qa-engineer`. Pass the scope level, core loop, and build configuration in the prompt. Tell QA the **resolved ports** from the stack profile (e.g. node-react: backend 3001 / frontend 5173; python-react: backend 8000 / frontend 5173; nextjs: app on 3000, same-origin API). For `clickable` scope, instruct QA to skip the auth dance and API integration tests. For `api-service`, QA runs API/integration checks only (no browser). For `cli-tool`, QA runs the CLI with sample args and asserts on output.

---

## Step 10 — Delivery

Once QA returns its report, print the delivery summary using this template:

```
SPRINT ZERO — DELIVERY SUMMARY
==============================
Project: <name from step 1, or URL if no name was collected>
Scope level: <level>
Core loop: <from docs/scope.md>
Backend: PASS / FAIL
Frontend: PASS / FAIL
Auth dance (signup → session → logout → login → protected → 401): PASS / FAIL / N/A
QA integration tests: X/X passed
QA browser tests: X/X passed
Known issues: <list any, or "none">
Ready to demo: YES / NO
```

If QA reports failures, print `STATE: QA_NEEDED` with recovery instructions after the summary.

If the QA report mentions that database tables are missing or the seed script failed **and the data layer is `local`**, the fix is just to re-run the seed (it creates the SQLite schema): print `Run the seed command for this build to (re)create the SQLite tables, then re-run QA.`

If the QA report mentions database/seed failures **and the data layer is `supabase`**, print this reminder:

> **Database setup needed — likely a missing `DATABASE_URL`:**
> 1. Go to Supabase Dashboard → Settings → Database → Connection string → URI (Session mode, port 5432).
> 2. Copy the full URL and add it to `server/.env` as `DATABASE_URL=...`
> 3. Run `cd server && node seed.js` — this creates the tables automatically and populates demo data.
> 4. Restart the server and re-run QA.

---

## Step 11 — Auto-launch the app

If `--no-launch` was passed, or if QA reported `Ready to demo: NO`, skip this step and print:

> Skipping auto-launch. Start the servers manually — see the "Start the app manually" section in the README.

Otherwise, hand the user a working app without making them wire it up themselves. **Resolve the dirs, run commands, and ports from `docs/scope.md` + `.claude/stacks.md` first** — the steps below use the node-react web-app names as the worked example, but substitute the resolved values for other profiles/types.

**Resolved values you need (look them up, do not assume):**

- node-react web-app: backend `cd server && node index.js` on 3001; frontend `cd client && npm run dev` on 5173.
- python-react web-app: backend `cd server && uvicorn main:app --port 8000` (after `pip install -r requirements.txt` in a venv) on 8000; frontend on 5173.
- nextjs web-app: a single app, `npm run dev` on 3000 — there is no separate frontend to start, and no `client/.env` to wire.
- api-service: backend only — start it, skip every frontend sub-step, and the "open in browser" line points at the API root or `/docs` (FastAPI) instead of a UI.
- cli-tool: nothing to start — skip 11d–11f and instead print the example invocation (e.g. `node cli/index.js --help` or `python cli/main.py --help`) and the seed/demo data note.

**11a. Install dependencies if needed.** For each code dir the build produced, install if its dependency folder is missing. Node dirs: `npm install` if `node_modules/` is absent. Python backend: create `.venv` and `pip install -r requirements.txt` if `.venv` is absent. Print one line per install. QA may have already done this — don't re-run if already present.

**11b. Wire frontend env — only for `supabase` web-apps with a separate frontend.** Skip entirely when data layer is `local` (the local frontend talks to our own backend `/auth/*` and needs no keys) and for `nextjs`/`api-service`/`cli-tool`. When it does apply: if `client/.env` does not exist, create it from `client/.env.example`, copying `SUPABASE_URL` → `VITE_SUPABASE_URL` and `SUPABASE_PUBLISHABLE_KEY` → `VITE_SUPABASE_PUBLISHABLE_KEY`.

**11c. Seed the data.** Run the seed command for the build (node-react/api: `cd server && node seed.js`; python: `cd server && .venv/bin/python seed.py`; nextjs: `node seed.js` at the app root). For `local`, this creates the SQLite schema and demo rows with no external dependency. Idempotent. Capture the demo user's email and password from stdout for the launch summary (omit for `clickable`, which has no real auth).

**11d. Start the backend/app in the background** using the resolved run command. Wait two seconds, then verify with `curl -s -o /dev/null -w "%{http_code}" http://localhost:<backend-port>/` (any HTTP response means it's up; a connection error means it failed to start).

**11e. Start the frontend in the background — web-app with a separate frontend only.** Skip for `nextjs` (already started in 11d), `api-service`, and `cli-tool`. Use the resolved command/port. Verify with `curl` against the frontend port.

**11f. Open the app cross-platform.** Pick the URL the user should open (frontend port for a UI; backend root or `/docs` for an api-service). Open it with the right command for the OS, and never abort if it fails — just print the URL:

```bash
URL="http://localhost:<open-port>"
if command -v open >/dev/null 2>&1; then open "$URL"          # macOS
elif command -v xdg-open >/dev/null 2>&1; then xdg-open "$URL" # Linux
elif command -v wslview >/dev/null 2>&1; then wslview "$URL"   # WSL
elif command -v cmd.exe >/dev/null 2>&1; then cmd.exe /c start "" "$URL"  # Windows
else echo "Open this in your browser: $URL"; fi
```

**11g. Print the launch summary** in this format (substitute resolved ports/commands; drop the frontend line for api-service; drop login for clickable):

```
SPRINT ZERO — APP IS RUNNING
============================
Backend:  http://localhost:<backend-port>  (background)
Frontend: http://localhost:<frontend-port>  (background)   ← omit for api-service / nextjs

Demo login:
  email:    <from seed output>
  password: <from seed output>

Open http://localhost:<open-port> in your browser.

To stop the servers later (cross-platform):
  - macOS / Linux: pkill -f "<backend run cmd>"  and  pkill -f "vite" (or "next dev")
  - Windows: close the terminal windows running them, or use Task Manager.
```

If any sub-step in 11 fails, print `STATE: LAUNCH_FAILED — start the servers manually per the README.` and stop. Do not retry. The build succeeded — only the launch did not.

---

## Status updates per step (always; the presenter reads them when `--present` was passed)

Write `.sprint-zero/status.json` once at the start of each step below, after the existing print statements but before invoking the sub-command. Always re-list the `docs/` directory contents into the `docs` array. Always set `timestamp` to the current ISO 8601 string. Never block on the write — it's atomic and trivially fast.

| Step | `phase`     | `stepNumber` | `step`             | `message`                                            |
| ---- | ----------- | ------------ | ------------------ | ---------------------------------------------------- |
| 3    | `research`  | 2            | `reference-brief`  | Researching the reference product.                   |
| 4    | `prd`       | 3            | `prd`              | Drafting the PRD.                                    |
| 5    | `decisions` | 4            | `decisions`        | Logging scope cuts and tradeoffs.                    |
| 6    | `stories`   | 5            | `user-stories`     | Expanding stories with acceptance criteria.          |
| 7    | `contract`  | 6            | `api-contract`     | Writing the API contract.                            |
| 8    | `brief`     | 7            | `tech-lead-brief`  | Tech-lead is reading the spec set.                   |
| 9    | `building`  | 8            | `parallel-build`   | Backend and frontend building in parallel.           |
| 9    | `qa`        | 9            | `qa`               | QA: contract checks, auth dance, core loop.          |
| 11   | `launch`    | 10           | `launch`           | Installing, seeding, and starting the servers.       |

For step 9 (parallel build), set `build.backend` and `build.frontend` to `"running"` when spawning the engineers, and to `"done"` (or `"failed"`) when each returns. Write the status file again after each engineer reports.

For step 9 (QA), populate the `qa` block as the engineer's report comes back: `contractBackend`, `contractFrontend`, `integration` (`{passed, total}`), `authDance`, and `coreLoop`. Use `"pending"` while a check is in flight, `"pass"`/`"fail"` once it lands, and `"n/a"` for `authDance` when scope is `clickable`.

**On step 11f (launch summary)**, write a final status with:

- `phase: "done"`
- `appUrl: "http://localhost:<open-port>"` (the resolved UI port from 11f, not a hardcoded 5173)
- `credentials: { "email": "<from seed stdout>", "password": "<from seed stdout>" }`
- `projectName: "<the project name from .sprint-zero/meta.json or step 1>"`
- `message: "Sprint Zero finished. Open the app."`

**On any named-failure exit**, before stopping, write:

```json
{
  "phase": "failed",
  "failure": {
    "state": "<the named state, e.g. SCOPE_NEEDED>",
    "message": "<one short sentence on what went wrong>",
    "recovery": "<the same recovery instructions you printed>"
  }
}
```

This lets the presenter UI show the failure card instead of spinning indefinitely.

<!-- $ARGUMENTS is the interpolation token Claude Code replaces with everything the user typed after /sprint-zero. It must appear in the file for URL and flag values to be accessible throughout these instructions. -->
$ARGUMENTS
