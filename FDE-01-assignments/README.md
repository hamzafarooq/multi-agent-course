# Forward Deployed Engineer (FDE) Track

> **Previous cohort's assignments (2026-02).** These four projects and the bonus lab were the
> FDE track before it merged with Agent Engineering. In the 2026-03 course, Assignment 2 (Voice
> Agent) is the spec for **VOXA**, Assignment 3 (Moment Search at Scale) for **ARGUS**, and
> Assignment 4 (EPYHIA) for **Demo Day**. Assignment 1 (Live Translate) is superseded by
> **LUMINA**, whose PRD lives in
> [`modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/`](../modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/PRD.md).
> New-cohort assignments ship inside their module folders.
> Smaller, ungraded apps to practice on live in [`Starter_Projects/`](../Starter_Projects/README.md).

> **"Full stack" here means full-stack SWE *and* AI engineering.** You build the
> whole product — the frontend, the agent logic, the model serving, the caching,
> and the deployment. One product, fully under your control.

**"Forward Deployed Engineer" is the new moat in AI.** Plenty of engineers can call
an LLM API; plenty can build a React frontend or a Node.js backend. Far fewer can take
an AI idea all the way to a shipped product — from the code in the browser down to the
model running on their own servers. That's the gap this track closes.

A Forward Deployed Engineer takes a capability and stands it up end to end where it's
needed: shipping into a live environment, owning the service behind it, respecting the
interfaces around it, and deploying it so it keeps running. You won't wrap an API in a
chat box and call it a product — you'll merge the three layers most courses keep apart
(a React frontend, a Node.js backend, and an AI backend), with the caching,
observability, and deployment that keep it fast and up. Every layer, built by you,
debugged by you, shipped by you.

## What makes this track different

Most exercises hand you a clean sandbox. FDE work rarely is one. Across the track you'll
repeatedly:

- **Ship into environments you didn't build** — a browser, a customer's page, a third-party API.
- **Own a real service** — an LLM, a cache, logs, traces, health checks, and a deploy.
- **Conform to a contract** you don't get to change.
- **Separate concerns** — app/gateway layers vs. AI layers — and make them talk.
- **Prove it works** with observability and a measurable rubric, not vibes.

That control is the point: it's how you cut latency and cost, keep data in-house, and
build what an API never will.

## What you'll learn

Build and ship complete AI products yourself — both the software engineering and the AI:

- **Full-stack AI products, end to end** — frontend, backend, and AI backend as one
  seamless product; own the full request path so you can debug any layer.
- **Run your own model** — serve a model with vLLM on RunPod, or route through OpenRouter,
  and swap providers without rewriting your app.
- **Multimodal Agentic RAG that scales** — retrieve across text, images, audio, and video;
  semantic caching and knowledge graphs for hybrid memory; scale toward millions of items.
- **Safe, evaluated agents** — Llama Guard guardrails; trajectory-vs-outcome evaluation;
  catch regressions before they ship.
- **Observability across the stack** — tracing, dashboards, and per-request latency, cost,
  and quality.
- **Distributed systems that stay up** — independent services (app, inference, retrieval,
  workers) that scale and fail on their own; multi-agent coordination with MCP and A2A.

## Who it's for

- **Senior frontend / full-stack engineers going AI-native** — strong in React, Node, and
  Python, who learn by building, not watching.
- **ML engineers who get stuck shipping** — can build a model, but want the frontend,
  caching, and deployment skills to actually get it out the door.
- **Founding and early-stage engineers** — own everything, and need to ship a real AI
  product on infrastructure they control.

## Assignments

Real-world products, all built end to end — from efficiency to action.

| # | Name | You build | Core skills |
|---|------|-----------|-------------|
| 1 | [Live Translate](Assignment_1_Live_Translate/) | A two-service backend (Node gateway + Python AI service) behind a provided browser widget that live-translates any page EN → Mexican Spanish | LLM calls, caching, structured logging + tracing, service separation, API contracts, deploy on Fly.io |
| 2 | [Voice Agent](Assignment_2_voice_agent/) | A production voice agent (STT → LLM → TTS) with a knowledge router, evals, and telemetry | Real-time pipelines, turn-taking, latency budgeting, retrieval, evaluation |
| 3 | [Moment Search at Scale](Assignment_3_Moment_Search_Scaled/) | Extend the working [Moment Search](https://github.com/traversaal-ai/momentsearch) video-RAG app to ingest **research papers and slide decks** through an **async work queue**, and answer one question with cited moments across video + page + slide | Async ingestion & work queues (Prefect), multi-format parsing, crash-safe pipelines, one shared vector index, cross-source cited retrieval, deploy on Fly.io |
| 4 | [EPYHIA (Capstone)](Assignment_4_Final_Epyhia/) | An end-to-end agent that **acts** for one real customer — pick one of four builds (Support Copilot, Outbound SDR, Content Studio, Repo Guardian) or bring your own — running unattended on a heartbeat, every side effect through one Action Gateway | A few scoped agents + an orchestrator, an autonomous heartbeat (crash-safe, idempotent), an approval inbox, auth, tracing, guardrails, evals, deploy on Fly.io |

**Bonus (optional, on your own time):**

| # | Name | You explore | Core skills |
|---|------|-------------|-------------|
| ★ | [AI Infra on Kubernetes](Bonus_AI_Infra_K8s/) | Serve an open-source vision model yourself with vLLM, then run it as a real fleet on GKE — and break it three ways to see what separates a demo from a deploy | Self-hosted inference (vLLM), Kubernetes (kubectl, node pools, probes, rollouts, autoscaling), cost hygiene |

> **This week:** Assignment 3 (Moment Search at Scale). The **AI Infra on
> Kubernetes** lab is now an optional **bonus** — do it on your own time; it pairs
> with the guest-speaker session on AI infra.

Each assignment folder is self-contained with its own `README.md`, provided scaffolding,
an `AGENTS.md` of non-negotiables, and a grading rubric.

## How every FDE project is graded

Consistent across the track: a **measurable rubric** plus a **video demo**.

- Each assignment ships an `eval/` folder with a `rubric.json` and an `eval.py`, and a
  bundled eval **skill** in `.claude/skills/`.
- `python eval/eval.py --student "…" --video "…"` scores the automated criteria against
  the running project and captures evidence, writing an intermediate scorecard
  (`eval/REPORT.md`). The eval skill runs that plus a live real-world test and folds it
  into a **`PRODUCT_EVAL.md`** — the polished Product Evaluation.
- Submission = **a Vercel link to your deployed app**, and nothing else. No repo, no code. Its
  `/evals` sub page renders the Product Evaluation (scored rubric, benchmark numbers, quality
  gates, design, both trajectories, video). The eval skill generates it; you never hand-write it. Course-wide rules: [`SUBMISSION.md`](../SUBMISSION.md).
  An `AGENTS.md` in each assignment states the non-negotiables so a coding agent (Claude Code)
  inherits them automatically.

## How to work through an assignment

1. Read the assignment's `README.md` top to bottom before writing code.
2. Run the provided pieces first so you can see what "done" looks like.
3. Build the parts marked as yours; the provided frontend/tests are your acceptance check.
4. Prove it with logs, traces, and stats; deploy it for real; then tackle the stretch goals.

## Prerequisites

- Comfort with a terminal, `git`, and HTTP/JSON.
- **Node 18+** and **Python 3.10+** installed.
- An API key for one LLM provider (Anthropic, Google, or OpenAI).
- A free **[Fly.io](https://fly.io)** account for the deploy step.
