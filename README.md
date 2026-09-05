<div align="center">

# 🤖 FDE Agent Engineering Bootcamp
### Agent Engineering + Forward Deployed Engineering, merged

**From a 50-line agent loop to a production-ready AI agency in seven weeks: four shipped products, built by you.**

[![Agent Engineering Bootcamp](https://img.shields.io/badge/Maven-Agent%20Engineering%20Bootcamp%20★%204.8-6E40C9?style=for-the-badge)](https://maven.com/boring-bot/advanced-llm)
&nbsp;
[![FDE Bootcamp](https://img.shields.io/badge/Maven-Forward%20Deployed%20Engineering%20Bootcamp%20★%204.9-FF6F61?style=for-the-badge)](https://maven.com/boring-bot/ai-system-design)
&nbsp;
![Weeks](https://img.shields.io/badge/7%20Weeks-6%20modules%20%2B%20Demo%20Day-2EA043?style=for-the-badge)
&nbsp;
[![Built with Claude](https://img.shields.io/badge/Built%20with-Claude%20Code-D97757?style=for-the-badge&logo=anthropic&logoColor=white)](https://claude.com/claude-code)

[**Agent Engineering Bootcamp**](https://maven.com/boring-bot/advanced-llm) · [**FDE Bootcamp**](https://maven.com/boring-bot/ai-system-design) · [**Curriculum**](#course-curriculum) · [**The four projects**](#the-four-projects) · [**What you'll build**](#what-youll-build) · [**Learn with Claude**](#learn-with-claude-ai-tutor)

<img width="1000" alt="FDE Agent Engineering Bootcamp, 2026-03 course outline: seven weeks and four projects" src="assets/course-outline-2026-03.png" />

**Cohort 2026-03 · Aug 31 – Oct 11, 2026 · 6 live sessions · 6 office hours · 1 demo day · 20+ hours**

</div>

---

Welcome to the official course repository for the **FDE Agent Engineering Bootcamp**: all the code, notebooks, exercises, and project specs used throughout the course. This cohort merges two Maven courses that used to run separately:

- [**Agent Engineering Bootcamp: Developers Edition**](https://maven.com/boring-bot/advanced-llm) (★ 4.8, 132 reviews): the loop, the harness, agentic RAG, multi-agent coordination, voice; *"master the full agent stack from first principles to production."*
- [**Forward Deployed Engineering Bootcamp**](https://maven.com/boring-bot/ai-system-design) (★ 4.9, 54 reviews): *"build full-stack AI products, from MVP to deployment"*: React frontend, Node backend, hosted models, four real deployments.

Six modules teach the concepts; four projects make you ship them.

> **Looking for a previous cohort?** The prior version of this course is preserved on the [`2026-02`](https://github.com/hamzafarooq/multi-agent-course/tree/2026-02) branch (and `2026-01` before it).

## Why merge Agent Engineering and FDE?

Modern AI builders need more than model skills.

- **Roles are converging.** AI work now requires system design and production skills, not just prompts.
- **FDEs need AI depth.** Agents, RAG, voice, and orchestration are becoming the core of the job.
- **The model is only one piece.** Reliability, latency, cost, security, and scale decide whether it ships.
- **Industry needs end-to-end builders** who can understand the problem, design, build, and ship.

## By the end of this bootcamp you will be able to

- Master **loop engineering** for reliable AI agents.
- Build **agent harnesses** with tools, state, memory, and observability.
- Apply **system and product design** across frontend, backend, APIs, data, and deployment.
- Engineer **production Agentic RAG** with retrieval, knowledge graphs, and caching.
- Design **multi-agent systems** with sub-agents, orchestration, MCP, and A2A.
- Build **scalable AI systems** for performance, reliability, and cost.
- Create **real-time voice agents** optimized for streaming and low latency.
- Make **architecture trade-offs** across performance, cost, security, reliability, and scale.

## Who this course is for

- **AI / ML engineers** ready to move from prototypes to production.
- **Software / full-stack engineers** building AI-native products and agents.
- **Forward deployed / solutions engineers** solving customer problems with AI.
- **Engineering & product leaders** making better architecture and scaling decisions.
- **Builders** who want to understand the complete system around AI.

## Quick Links

**Course modules** (in teaching order):

1. [Week 1: Agent Foundations, Agent Harness & System Design](#week-1-agent-foundations-agent-harness--system-design)
2. [Week 2: Skills & Subagents: Product Architecture & Coordination](#week-2-skills--subagents-product-architecture--coordination)
3. [Week 3: Production Agentic RAG & AI Systems](#week-3-production-agentic-rag--ai-systems)
4. [Week 4: Multi-Agent Systems & Orchestration](#week-4-multi-agent-systems--orchestration)
5. [Week 5: Real-Time Voice Agents & Conversational Systems](#week-5-real-time-voice-agents--conversational-systems)
6. [Week 6: Leading AI Systems Across Teams](#week-6-leading-ai-systems-across-teams)
7. [Week 7: Demo Day, Production-Ready AI Systems](#week-7-demo-day-production-ready-ai-systems)

**Also on this page:** [The four projects](#the-four-projects) · [How to use this repo](#how-to-use-this-repo) · [What you'll build](#what-youll-build) · [Sprint Zero](#full-stack-projects) · [Starter Projects](#starter-projects) · [The quality bar](#the-quality-bar-how-work-is-judged-and-how-to-give-feedback) · [How to submit](SUBMISSION.md)

### 🗺️ Course at a glance

| Week | Module | The big idea | You ship |
|---|--------|--------------|----------|
| 1️⃣ | **Agent Foundations, Agent Harness & System Design** | What an agent *actually* is, and what a system around it looks like | A ReAct agent from scratch · **LUMINA** kicks off |
| 2️⃣ | **Skills & Subagents: Product Architecture & Coordination** | One agent → a coordinated product built by specialized subagents | **Sprint Zero**: a multi-agent app builder |
| 3️⃣ | **Production Agentic RAG & AI Systems** | Retrieval as a decision the agent makes, evaluated and guarded | A cited video-moment RAG + eval harness · **ARGUS** kicks off |
| 4️⃣ | **Multi-Agent Systems & Orchestration** | When many agents beat one, and the protocols (MCP · A2A · ADK) that make it work | A coordinated multi-agent support system |
| 5️⃣ | **Real-Time Voice Agents & Conversational Systems** | STT → LLM → TTS under a latency budget, two architectures head-to-head | A benchmarked voice agent · **VOXA** kicks off |
| 6️⃣ | **Leading AI Systems Across Teams** | From building the system to leading the people and decisions around it | An AI roadmap + measurement plan for a real team |
| 7️⃣ | **Demo Day** | Show it, measure it, defend it | **EPYHIA**: an end-to-end AI agency, live |

---

## The Four Projects

Concepts are taught in the modules; the projects are where you ship. Each is a real product built end to end (frontend, agent logic, model serving, caching, deployment) and graded against a **measurable rubric plus a short video demo, not vibes**. LUMINA's PRD ships inside Module 1; the other three specs, rubrics, and evaluators live in the [previous cohort's FDE assignments](FDE-01-assignments/README.md) until their 2026-03 versions land in their module folders.

| Starts | Project | You build | Spec |
|---|---|---|---|
| Week 1 | 🔍 **LUMINA**: Perplexity-style AI search | An AI search experience with retrieval, citations, and structured answers | [PRD](modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/PRD.md) |
| Week 3 | 📄 **ARGUS**: Multimodal RAG pipeline | A RAG pipeline that understands and retrieves across text, images, documents, and more, with cited moments | [Assignment 3: Moment Search at Scale](FDE-01-assignments/Assignment_3_Moment_Search_Scaled/) |
| Week 5 | 🎙️ **VOXA**: Open-source voice agent | A streaming STT → LLM → TTS voice agent that holds a real-time conversation | [Assignment 2: Voice Agent](FDE-01-assignments/Assignment_2_voice_agent/) |
| Week 7 | 🏆 **EPYHIA**: End-to-end AI agency (Demo Day) | A production-ready autonomous agency that plans, builds, executes, and delivers value | [Assignment 4: EPYHIA](FDE-01-assignments/Assignment_4_Final_Epyhia/) |

Every project ships an `eval/` folder with a `rubric.json` and an `eval.py` that scores your running deployment, captures evidence, and produces a **Product Evaluation** report you submit with a 60–90s demo. [See a sample scorecard →](FDE-01-assignments/Assignment_1_Live_Translate/README.md#sample-scorecard)

---

## How to Use This Repo

### Start here: understand the course in 15 minutes

1. **Read the outline above**, then the [course at a glance](#quick-links) table: seven weeks, six modules, four shipped projects.
2. **Open one module folder.** Every module lives at `modules/Module_N_Name/` and follows the same shape: a `README.md` that says what the week covers and what's inside, a `study-material/` folder with `lesson.md`, `key-concepts.md`, `exercises.md`, `quiz.md`, and `recap-and-preview.md`, and the notebooks, apps, and specs next to them. Module 1 is the best first stop: it holds the [LUMINA PRD](modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/PRD.md) and [Alex](modules/Module_1_Agent_Foundations_Harness_System_Design/Alex_Perplexity_Clone/README.md), the reference app you'll clone before you build.
3. **Let an agent walk you through it.** Open the repo in Claude Code and type `/start`, or point any other coding agent at [`AGENTS.md`](AGENTS.md). Either way you get a tutor that teaches one concept at a time and tracks you in `progress/learner-progress.md`. See [Learn with Claude](#learn-with-claude-ai-tutor).
4. **Read one project spec end to end** before touching code. The LUMINA PRD shows the shape every project follows: a fixed API contract, a provided UI that is the acceptance test, an SLA you prove with a benchmark, and a rubric. This is a *reading* course first.
5. **Know how work gets judged** and how to give feedback that helps: [The quality bar](#the-quality-bar-how-work-is-judged-and-how-to-give-feedback). And how you submit: a Vercel link to your deployed app with an `/evals` sub page that proves itself. See [`SUBMISSION.md`](SUBMISSION.md).

### Layout

- Content is organized **module by module** under `modules/`, aligned with the live sessions and project milestones. The Week 1 project spec (LUMINA) lives inside Module 1; the previous cohort's specs, still used for VOXA, ARGUS, and EPYHIA, live under `FDE-01-assignments/`. Ungraded practice apps live in `Starter_Projects/`.
- **Google Colab Pro** is the preferred environment for the notebooks. You can also **clone locally** and run them in Jupyter or your IDE.
- Most notebooks include their own dependencies via `!pip install`; where a module needs more, a `requirements.txt` sits alongside it.

### Learn with Claude (AI tutor)

This repo is also set up to be **read and used with [Claude](https://claude.com/claude-code)** as a personal tutor. Drop the folder into Claude Code (or upload it to Claude.ai) and Claude reads `CLAUDE.md` to act as a patient, interactive guide through the course, teaching one concept at a time, checking your understanding, and tracking your progress in `progress/learner-progress.md`.

**Get started:** open the folder in Claude Code and type `/start`, or paste *"Read CLAUDE.md and run the `/start` onboarding"* into Claude.ai. Claude will greet you, ask how you like to learn, and begin Module 1. Using Codex, Cursor, or another coding agent? [`AGENTS.md`](AGENTS.md) at the repo root carries the same tutor instructions.

**Slash commands**

- `/start`: onboard, pick a learning style and begin Module 1 (or the next one)
- `/progress`: see where you are, what's next, and any flagged weak spots

**Skills Claude auto-invokes** (in `.claude/skills/`): just ask in plain language:

| Skill | What it does | Try saying |
|-------|--------------|------------|
| `teach-module` | Runs an interactive lesson for a module, one concept at a time | *"Teach me module 3"* |
| `quiz-me` | Quizzes you and tracks weak spots (never reveals answers first) | *"Quiz me on RAG"* |
| `explain-eli5` | Re-explains a concept as simply as possible, with analogies | *"Explain isolated context like I'm five"* |
| `build-along` | Guides you through a hands-on exercise step by step | *"Let's do the build-along for module 1"* |
| `warmup` | A ~15-min pre-class refresher: recaps the last module, previews the next | *"I have class soon, warm me up for module 2"* |

### Clone locally (optional)

```bash
git clone https://github.com/hamzafarooq/multi-agent-course.git
cd multi-agent-course
python3 -m venv .venv
source .venv/bin/activate
```

### Clone via Claude Code chat

You can clone this repo directly from the Claude Code chat interface without leaving your conversation:

1. Open [Claude Code](https://claude.ai/code) in your browser (or launch `claude` in your terminal)
2. In the chat, type:
   ```
   Clone https://github.com/hamzafarooq/multi-agent-course.git and open it
   ```
3. Claude will clone the repo into a directory of your choice, set up the project, and open it, ready for you to start learning.

From there, type `/start` to begin the AI-guided onboarding.

### Recommended resource

To go deeper on building LLM applications, see the book
[**Build LLM Applications from Scratch**](https://www.manning.com/books/build-llm-applications-from-scratch).

---

## Course Curriculum

> Six modules across six weeks, one 2-hour live session and one office hour each, then Demo Day in week seven. Every week ends with a working artifact you built yourself, and four of those weeks kick off a shipped product.

### Week 1: Agent Foundations, Agent Harness & System Design

Demystify what an agent actually is: the perceive → reason → act loop and the **ReAct** pattern. Then zoom out to the *system* around it: the harness, the components, where state lives, and how the whole thing scales. Build a ReAct agent from scratch, no framework.

**What this module covers:** agent & system foundations (software → ML → AI) · the agentic loop & the agent harness · components & responsibilities · state, communication & trade-offs · scale up vs. scale out

**Key topics:** the agent loop · ReAct (Reasoning + Acting) · agent vs. workflow vs. chatbot · debugging via the trace · agent frameworks (smolagents) · vertical vs. horizontal scaling for AI systems

**🚀 Project kickoff: LUMINA.** A Perplexity-style AI search experience. Week 1 gives you the loop; the project makes you wrap it in retrieval, citations, and a real frontend.
[Read the PRD →](modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/PRD.md)

**🔎 Reference app: Alex.** A finished Perplexity-style assistant you can clone and take apart before you build LUMINA. Four levels (LLM → chatbot → tool-using agent → RAG assistant), a debug panel that shows the exact API request behind every answer, and a keyword-vs-semantic Search Lab. Hosted at https://lumina-perplexity-clone.vercel.app (password shared in class).
[Open Alex →](modules/Module_1_Agent_Foundations_Harness_System_Design/Alex_Perplexity_Clone/README.md)

[Open Module 1 →](modules/Module_1_Agent_Foundations_Harness_System_Design/README.md)

---

### Week 2: Skills & Subagents: Product Architecture & Coordination

Go from *one* agent doing one thing well to a *coordinated product* built by specialized subagents. Learn why isolated context windows are the whole point, the orchestrator + subagents pattern, how to define your own subagents and skills, then watch the pattern run end to end in **Sprint Zero**.

**What this module covers:** multi-agent architectures (Supervisor, Plan-and-Execute, …) · sub-agents & coordination · tools, skills & MCP · memory in multi-agent systems · governance, security & guardrails

**Key topics:** agents vs. subagents · isolated context windows · the orchestrator pattern (sequential vs. parallel) · defining subagents in `.claude/agents/` · specialization & the shared-spec coordination layer · multi-agent failure modes

**📦 Featured project: [Sprint Zero](#sprint-zero-a-multi-agent-product-team-in-your-terminal).** The module's capstone: a multi-agent system that turns a product URL and three answers into six spec docs and a working full-stack app.

[Open Module 2 →](modules/Module_2_Skills_Subagents_Product_Architecture/README.md)

---

### Week 3: Production Agentic RAG & AI Systems

Treat retrieval as a tool the agent *decides* to use, not a static bolt-on. Add a semantic cache for real latency/cost wins, contrast vector RAG with Knowledge Graphs, push retrieval down to the exact *moment* in a video, then **prove it works** with the right metrics and guard it for production.

**What this module covers:** production agentic RAG · advanced RAG techniques (re-ranking, query transformation, hybrid search) · RAG evaluation & optimization · security, safety & guardrails · productionization & scaling

**Key topics:** naive vs. agentic RAG · query routing & multi-hop retrieval · query decomposition + HyDE · hybrid retrieval & RRF fusion · cross-encoder re-ranking · semantic caching · Knowledge Graphs & text-to-Cypher · moment-level video RAG · the eval pyramid (LLM → RAG → agent metrics) · guardrails (Llama Guard)

> 🗺️ **New here?** [Module 3 at a glance](modules/Module_3_Production_Agentic_RAG_AI_Systems/README.md#module-3-at-a-glance): a one-screen map of the five folders below.

![Module 3 mind map, Agentic RAG, Semantic Cache, Knowledge Graphs, and Moment RAG](modules/Module_3_Production_Agentic_RAG_AI_Systems/module-3-mindmap.png)

**🎬 Featured project: Moment RAG.** Agentic RAG on *video*. Ask a complex question and get a streamed, **cited** answer where every citation pops up the source YouTube episode at the **exact moment**, with a synced transcript. Pipeline: self-query → decompose → hybrid retrieve (dense + BM25 + HyDE questions, RRF) → cross-encoder re-rank → cited synthesis.
[View documentation →](modules/Module_3_Production_Agentic_RAG_AI_Systems/Moment_RAG/README.md)

```bash
cd modules/Module_3_Production_Agentic_RAG_AI_Systems/Moment_RAG
pip install -r requirements.txt
cp .env.example .env      # add OPENAI_API_KEY
uvicorn app:app --reload  # open http://localhost:8000
```

**📊 Featured project: RAG vs. Knowledge Graph comparison framework.** A Streamlit app that objectively compares RAG and KG approaches with LLM-based evaluation and interactive graph visualizations.
[View documentation →](modules/Module_3_Production_Agentic_RAG_AI_Systems/Knowledge_Graphs/README.md)

```bash
cd modules/Module_3_Production_Agentic_RAG_AI_Systems/Knowledge_Graphs
python setup.py      # one-time setup
streamlit run app.py
```

**📏 Featured notebook: AI Evaluation Metrics.** A plain-English tour of the metrics used across every layer of an AI system: LLM quality & reasoning, RAG retrieval & generation, and full agent/multi-agent evaluation. No API keys, no model downloads, just the standard library doing the arithmetic so you can watch the numbers move.
[View documentation →](modules/Module_3_Production_Agentic_RAG_AI_Systems/Evaluation_and_Guardrails/README.md) · [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/modules/Module_3_Production_Agentic_RAG_AI_Systems/Evaluation_and_Guardrails/AI_Eval_Metrics.ipynb)

**🚀 Project kickoff: ARGUS.** A multimodal RAG pipeline. Take Moment RAG's cited-moment retrieval and scale it across text, images, documents, and slides through an async ingestion queue.

[Open Module 3 →](modules/Module_3_Production_Agentic_RAG_AI_Systems/README.md)

---

### Week 4: Multi-Agent Systems & Orchestration

When many agents beat one, and the more common case where they don't. Build a coordinated multi-agent system, learn the protocol layer underneath the marketing, and instrument it so you can debug it.

**What this module covers:** sub-agent & multi-agent foundations · coordination strategies & orchestration · agent-to-agent (A2A) communication & protocols · shared state, memory & context management · observability, evaluation & debugging

**Key topics:** one agent vs. many · topologies (orchestrator-worker, hierarchical, swarm, handoff) · **MCP** (tools), **A2A** (agent-to-agent), **ADK** (Google's framework) · shared memory & message passing · tracing multi-agent runs

> 🗺️ **New here?** [Module 4 overview](modules/Module_4_Multi_Agent_Systems_Orchestration/README.md): how MCP, A2A, and ADK compose into one running system.

**🛎️ Featured project: Advanced Customer Support Agent.** A CLI support agent that ties all three protocols together: **ADK** defines the agents (Gemini 2.5 Flash), **A2A** runs the Security Judge and PII Masker as independent microservices, and **MCP Toolbox** exposes a PostgreSQL backend as tools. Wrapped in a multi-layer security pipeline (input sanitization → A2A security judge → DLP-based PII masking).
[View documentation →](modules/Module_4_Multi_Agent_Systems_Orchestration/advance-customer-support-agent-feature-A2A-MCP-ADK/README.md)

```bash
cd modules/Module_4_Multi_Agent_Systems_Orchestration/advance-customer-support-agent-feature-A2A-MCP-ADK
pip install -r requirements.txt
cp .env.example .env      # add Google Cloud + Mem0 keys
python -m cs_agent.a2a.run_servers   # start the A2A servers, then run the CLI
```

[Open Module 4 →](modules/Module_4_Multi_Agent_Systems_Orchestration/README.md)

---

### Week 5: Real-Time Voice Agents & Conversational Systems

Ship an agent that talks and survives real conversation, then benchmark two different architectures for doing it head-to-head.

**What this module covers:** real-time voice agents & conversational systems · voice, STT, LLM & TTS foundations · system design, guardrails & performance optimization · evaluation, monitoring & quality assurance · deployment, integration & best practices

**Key topics:** the voice stack (STT → LLM → TTS) · turn-taking & end-of-turn detection · latency budgeting, streaming & barge-in · tool calling inside a voice loop · provider landscape (Deepgram, ElevenLabs, OpenAI Realtime, Vapi, Retell) · cascade vs. speech-to-speech architectures · benchmarking voice agents on cost, latency, and capability

**🚀 Project kickoff: VOXA.** An open-source voice agent. Streaming STT → LLM → TTS with a knowledge router, evals, and telemetry, holding a real-time conversation.

[Open Module 5 →](modules/Module_5_Voice_Agents_Conversational_Systems/README.md)

---

### Week 6: Leading AI Systems Across Teams

You can build the system. Now lead the people and decisions around it: set the strategy, drive adoption, govern responsibly, and measure whether any of it moved the business.

**What this module covers:** leadership & team alignment · AI strategy & roadmapping · organizational change & adoption · AI ethics, governance & compliance · measuring impact & ROI

**Key topics:** aligning teams on shared goals · prioritizing use cases into a roadmap · the adoption curve inside an org · policies, compliance, and responsible use · tracking ROI and communicating impact to stakeholders

[Open Module 6 →](modules/Module_6_Leading_AI_Systems_Across_Teams/README.md)

---

### Week 7: Demo Day, Production-Ready AI Systems

**Showcase · Evaluate · Feedback · Next steps.** You demo **EPYHIA**, your end-to-end AI agency, live: it plans, builds, executes, and delivers value for one real customer, unattended, with every side effect going through one action gateway. It is graded on the rubric, not the pitch.

[Demo Day brief →](modules/Module_7_Demo_Day/README.md) · [EPYHIA spec →](FDE-01-assignments/Assignment_4_Final_Epyhia/)

---

## What You'll Build

This course goes beyond theory. Across seven weeks you'll ship real, portfolio-ready artifacts:

| 🛠️ Artifact | What it proves |
|------------|----------------|
| 🔁 **ReAct agent** built from scratch | You understand the loop, not just a framework |
| 🔍 **LUMINA**: Perplexity-style AI search | You can turn a loop into a product with retrieval, citations, and a UI |
| 🤝 **Sprint Zero**: multi-agent app builder | You can orchestrate specialized subagents to a shared spec |
| 🎬 **Moment RAG** + 📄 **ARGUS**: cited, multimodal retrieval at scale | Retrieval resolves to the exact moment you cite, across text, video, and documents |
| 🕸️ **Knowledge Graph app** + RAG-vs-KG eval | You can pick the right memory for the job and measure it |
| ✅ **Evaluation + guardrail harness** | You ship with measurable quality and safety |
| 🛎️ **Multi-agent support system** (MCP · A2A · ADK) | You can coordinate many agents over real protocols |
| 🎙️ **VOXA**: real-time voice agent, benchmarked | You can budget latency and survive barge-in |
| 🏆 **EPYHIA**: an autonomous AI agency | You can ship an agent that *acts*, safely, unattended |

---

## Full Stack Projects

End-to-end, build-along projects that tie the course concepts together.

### 🚀 Sprint Zero: a multi-agent product team in your terminal

> **Point it at a product. Answer three questions. Get back a complete spec set and a working app.**

A Claude Code kit that runs a full sub-agent product team on your laptop: scoping, research, six spec docs, parallel engineering, and QA, all driven from one command. The Module 2 capstone, and a working reference for the orchestrator + subagents pattern.

```
/sprint-zero https://twenty.com  →  📋 specs  →  🤝 parallel build  →  ✅ QA  →  🟢 running app
```

- ⚙️ **Configurable**: `web-app` / `api-service` / `cli-tool` · `node-react` / `nextjs` / `python-react`
- 🔌 **Zero-setup default**: SQLite + local auth, runs straight after clone (no account, no keys)
- ⏱️ **~10–20 min** end-to-end for an MVP

[![Open Sprint Zero](https://img.shields.io/badge/▶%20Open-Sprint%20Zero-6E40C9?style=for-the-badge)](Full_Stack_Projects/Sprint_Zero)

Built by [Yousuf Alvi](https://github.com/yousuf-alvi) and [Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/).

---

## Starter Projects

Nine small, complete apps you can clone, run, break, and rebuild. Imported from
[claude-code-starter](https://github.com/hamzafarooq/claude-code-starter) (MIT). Ungraded. They exist so you
have working code to read alongside the modules and something real to point Claude Code at. Each folder is
self-contained: read its README, copy `.env.example` to `.env`, run it. None ship secrets.

| Project | What it does | Pairs with |
|---------|-------------|------------|
| [skill-sub-multi-agent](Starter_Projects/skill-sub-multi-agent/) | Interactive 4-level visualization of how skills, sub-agents, and multi-agent pipelines work (Next.js) | Module 2 |
| [research-frontend](Starter_Projects/research-frontend/) | Chat UI that teaches LLM modes one switch at a time: tools, memory, RAG, long-term storage | Modules 1, 3 |
| [full-stack-demo](Starter_Projects/full-stack-demo/) | Visual explainer of how a frontend, a backend, and an AI backend talk to each other | Module 1 |
| [competitor-research-agent](Starter_Projects/competitor-research-agent/) | End-to-end competitor research using sub-agents (pricing-fetcher + review-miner) | Module 2 |
| [research-agent](Starter_Projects/research-agent/) | Claude Code agent for deep competitive-landscape research with MCP | Module 2 |
| [meetingmemo](Starter_Projects/meetingmemo/) | Turns raw meeting notes into a structured standup update (Next.js + Anthropic API) | Module 1 |
| [meeting-notes-summarizer](Starter_Projects/meeting-notes-summarizer/) | Summarizes meeting notes into action items (Node.js + Express) | Module 1 |
| [prd-generator](Starter_Projects/prd-generator/) | Single-page PRD generator | Module 2 |
| [royal-pop-website](Starter_Projects/royal-pop-website/) | Scroll-driven product landing page built from a 15-second video (GSAP, Lenis, canvas frame playback) | Module 2 / EPYHIA |

Also worth a look, hosted elsewhere: [word-humanizer](https://github.com/hamzafarooq/word-humanizer/) ·
[seo-writer](https://github.com/hamzafarooq/seo-writer) · [linkedin-growth](https://github.com/hamzafarooq/linkedin-growth).
The previous cohort's graded FDE projects live in [`FDE-01-assignments/`](FDE-01-assignments/README.md).

---

## The Quality Bar: how work is judged, and how to give feedback

Everything in this repo, a module, a project submission, a pull request, is held to one standard, and it is the same standard your agents will be held to in production. If you review someone's work here, or file feedback on the repo itself, use it.

### The four laws

1. **A thing that ran is not a thing that worked.** A notebook that finished, an eval that passed, a demo that streamed an answer: each proves the process did not crash. Correctness is proven separately, against numbers.
2. **Assert from declared numbers, never from detection.** Every gating threshold is written down *before* the run (latency, cost, recall, grounding) and checked by arithmetic against a run log. Asking a model whether the output was good is detection. An LLM judge may *report* on tone or helpfulness; it may never *block*.
3. **Every rule cites the failure that created it.** A rule with no incident behind it is an opinion. Rules in this course carry IDs (`A1` tool errors surface, `A2` the loop finished rather than hit a cap, `R2` forbidden tools were not called, `E2` declared eval thresholds met, `B1`–`B3` token, latency, and cost budgets, `P1` a human read the trajectory) and each cites the real incident that made it a rule.
4. **Gates run in order, and each one blocks.** Static checks, then the declared contract, then a smoke run, then the trajectory, then the eval, then a human. Cheap and deterministic first; expensive and human last. Nothing downstream runs on upstream garbage.

The [LUMINA PRD, section 13](modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/PRD.md#13--quality-bar-how-done-is-proven) is the worked example: the declared `expectations.json`, the run-log shape, the six gates, and the rubric rows mapped to rule IDs.

### How to give feedback that helps

Whether you are reviewing a classmate's capstone or opening an issue on this repo:

- **Read the trajectory, not the answer.** Before you say a project works, read one complete *successful* run and one complete *failing* run, every step. If you cannot produce a failing run, you do not understand the failure surface yet. Say which two runs you read.
- **Cite a rule ID, then the evidence.** "`A1`: the fetch on step 3 failed and returned an empty string the model read as a normal result" is a better review than a paragraph. It points at the precedent and tells the author exactly what to fix.
- **Bring the number, not the adjective.** "Slow" is a vibe. "p95 6.4 s against a declared 12 s budget, but 3 of 30 runs hit the 90 s cap" is feedback.
- **When you hit a failure the rules do not cover, write the rule.** One executable sentence, the real incident as its precedent (date, what broke, what it cost), and a self-check question a reviewer can answer out loud. That is the highest-value contribution you can make to this repo, because it is the actual job. Never invent a precedent to make a rule look grounded; a lessons file full of fiction is worse than an empty one.
- **For the repo itself:** file issues the same way. Which module, which file, what you expected, what happened, and which of the four laws it violates. A broken link or a stale path is a `T` (teaching quality) finding; say so.

### Before you claim anything is done

- [ ] Every gate passes, or each failure is waived in writing with a reason.
- [ ] You read one full successful trajectory and one full failing trajectory.
- [ ] Budget numbers were checked against what was declared, not eyeballed.
- [ ] Nothing that must not break is verified by a model's opinion.
- [ ] Any new failure found is now a rule, with its precedent.
- [ ] The precedents you wrote are true.

That last box is the whole system.

---

## About the Course

**FDE Agent Engineering Bootcamp**: the merger of two Maven courses:

| Course | Rating | What it brought |
|---|---|---|
| [Agent Engineering Bootcamp: Developers Edition](https://maven.com/boring-bot/advanced-llm) | ⭐ 4.8/5 (132 reviews) | Agentic RAG, voice, and multi-agent systems from first principles to production |
| [Forward Deployed Engineering Bootcamp](https://maven.com/boring-bot/ai-system-design) | ⭐ 4.9/5 (54 reviews) | Full-stack AI products (frontend, backend, hosted models) shipped through four real deployments |

**Instructor:** [Hamza Farooq](https://www.linkedin.com/in/hamzafarooq/): Founder @ [traversaal.ai](https://traversaal.ai) · Ex-Google, Walmart Labs · 15+ years in machine learning · Adjunct Professor at Stanford & UCLA

A hands-on, build-every-week bootcamp for engineers who already write Python and have touched LLM APIs. Six live 2-hour sessions, six office hours, and a Demo Day; you leave with four shipped products and the **judgment** that separates engineers who ship agents from engineers who follow tutorials.

---

*Created by [boring-bot](https://maven.com/boring-bot). Building the future of AI, one agent at a time.*
