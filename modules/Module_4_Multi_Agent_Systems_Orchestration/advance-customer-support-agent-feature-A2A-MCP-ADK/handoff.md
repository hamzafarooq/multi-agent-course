# Handoff — Module 4 Customer-Support Capstone

**Date:** 2026-06-26
**Scope:** Getting the Module 4 multi-agent capstone (MCP + A2A + ADK) runnable end-to-end,
documented, and demoable for a live class.

---

## Current state — it works

The full stack runs **live** on this machine and was verified end-to-end (real Gemini calls,
real mem0 memory, MCP tools hitting a seeded Postgres, both A2A security servers, Phoenix
tracing). A scripted CLI session successfully: logged in as Alice, looked up order 3
(`get-order-status`), listed all orders (`find-customer-orders`), saved a contact preference
(Mem0), and confirmed a cancel intent (`action-log`). Output came back lowercased — the A2A
Data Masker processing the response.

Conda env: **`customer-support`** (Python 3.12.13). All deps installed.

---

## What was built this session

- **`run.sh`** — one-command orchestrator (`setup | start | stop | status | seed | logs`).
  Self-contained: regenerates the gitignored `mcp_toolbox/tools.yaml` + `seed.sql` from
  embedded heredocs. Committed in **PR #45** (merged to `main`, commit `27ede2b`).
- **Study-material set** for the module (`study-material/lesson.md`, `key-concepts.md`,
  `exercises.md`, `quiz.md`, `recap-and-preview.md`). Committed in **PR #44** (merged).
- **README + `run.sh` updates** (this session, see *Uncommitted* below).
- **`handoff.md`** — this file.

See the diffs/commits for content; not duplicated here.

---

## Key facts the next agent needs

- **Two API keys** live in the **project** `.env` (`advance-…-ADK/.env`), NOT the repo-root
  `.env`. `agent_cli.py` does `load_dotenv()` from `cs_agent/` and picks up the project one.
  Both `GOOGLE_API_KEY` (39 chars, valid) and `MEM0_API_KEY` (43-char `m0-…`, valid) are set.
- **`.env` footgun (root cause of a long detour):** dotenv treats `KEY=value # comment` as part
  of the value. The old template had inline `# app.mem0.ai` comments, which got read as the key.
  Fixed in `run.sh` (comments now on their own lines) — see *Uncommitted*.
- **Phoenix auto-launches** in-process via `telemetry.py:init_telemetry()` →
  `px.launch_app()`. It serves at **http://localhost:6006** only while the CLI is alive. The
  README's old "Terminal 3" standalone Phoenix step is obsolete.
- **OpenTelemetry pin:** must be **1.42.1** (not the README's old 1.33.1) to satisfy the
  installed `google-adk 2.3.0` (`>=1.39,<=1.42.1`). Already corrected in `run.sh` and README §3.
- **Toolbox flag** is `--config` (not the README's old `--tools-file`); pkg
  `@toolbox-sdk/server@1.5.0`.
- **macOS:** no `setsid` — `run.sh` uses PID + `pkill -P` + `lsof`-by-port cleanup.
- **User passwords** = first name lowercase (alice/bob/hannah/julia/…). DB creds:
  `toolbox_db` / `toolbox_user` / `mysecretpassword` @ `127.0.0.1:5432` (hardcoded in
  `cs_agent/greet.py` and `mcp_toolbox/tools.yaml`).
- **`mcp_toolbox/` and `.env` are gitignored** — that's why `tools.yaml` was never committed
  and had to be reconstructed. `run.sh` regenerates both, so only `run.sh` needs committing.
- **DLP masking** degrades to a no-op without `GOOGLE_CLOUD_PROJECT` (see
  `security/masker.py`) — fine for local/class demo.

---

## Uncommitted changes (need a commit/PR)

In the working tree on `main`:
- `run.sh` — `.env` template fixed (inline-comment footgun removed).
- `README.md` — added: `./run.sh` quick-start (Option A), fixed manual commands (Option B),
  full 10-user credential table, "Using the agent (CLI walkthrough)", "Observability — Arize
  Phoenix" section, corrected OTel pin in §3, `run.sh`/`seed.sql` in project structure.
- `handoff.md` — this file.

**Next step:** branch, commit these, open a PR, merge (the established workflow this repo uses —
see PRs #44/#45). The user has been directing each push/merge explicitly.

---

## How to run (for the demo)

```bash
cd modules/Module_4_Multi_Agent_Systems_Orchestration/advance-customer-support-agent-feature-A2A-MCP-ADK
./run.sh                       # starts everything, drops into the CLI
# open http://localhost:6006 in a browser for live Phoenix traces
```
Demo queries and DB-inspection commands are in the README's *Using the agent* section.

Background services from this session (Toolbox :5000, A2A :10002/:10003, Postgres :5432) may
still be running; `./run.sh` auto-clears stale ones before starting.

---

## Open / possible follow-ups

- Commit the uncommitted changes above (primary).
- Optional: `.env.example` still has `GOOGLE_GENAI_USE_VERTEXAI=1`, which contradicts the
  AI-Studio-key path — worth aligning with the generated `.env`.
- Optional: the module README one level up references study-material; verify cross-links.

## Suggested skills for the next session
- **`review`** or **`verify-work`** before committing the README/`run.sh` changes.
- The repo's own teaching skills (`teach-module`, `quiz-me`) now have Module 4 content to use.
