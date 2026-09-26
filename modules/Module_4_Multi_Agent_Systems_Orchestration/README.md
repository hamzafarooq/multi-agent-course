# Module 4 — Multi-Agent Systems & Orchestration

This module is about what happens when a single agent is no longer enough. Real systems are
built from **many specialized agents** that have to discover each other, exchange messages, and
call shared tools — without collapsing into a tangle of point-to-point glue code. The answer is a
**protocol layer**: a small set of standards that let agents and tools talk to each other the same
way regardless of who built them.

You'll learn the three protocols that matter most in practice, and how they fit together:

- **MCP (Model Context Protocol)** — the standard way to expose *tools and data sources* to an
  agent. Instead of hard-coding database calls into your agent, you run an MCP server and the agent
  discovers the tools at runtime.
- **A2A (Agent-to-Agent)** — the standard way for *agents to call other agents* as independent
  services. Each agent publishes an "agent card" describing what it can do, and others invoke it
  over JSON-RPC 2.0 / HTTP — including streaming responses.
- **ADK (Agent Development Kit)** — Google's framework for *defining* the agents themselves:
  single LLM agents, sequential pipelines, and the runner that drives their execution.

The throughline of the course is **"from efficiency to action"** — this is the *action* end, where
agents stop being standalone chatbots and start coordinating as a system.

---

## What You'll Learn

- Why a **protocol layer** beats bespoke integration glue once you have more than one agent or tool
- How to expose database operations as **MCP tools** instead of baking them into agent code
- How to run agents as **independent A2A microservices** that discover and call each other
- How to build agents with **Google ADK** — `LlmAgent`, `SequentialAgent` pipelines, and the `Runner`
- How these three layers compose into one working system: ADK *defines* the agents, A2A *connects*
  them, MCP *feeds* them tools
- How to put a **multi-layer security pipeline** in front of a multi-agent system (input
  sanitization, an LLM security judge, and PII masking on the way out)
- What a **ReAct loop** buys you over one-shot RAG, measured against golden answers, and why the loop
  alone isn't enough to keep an agent grounded

---

## Module Structure

```
Module_4_Multi_Agent_Systems_Orchestration/
│
├── how_skills_work_under_the_hood.ipynb               # Notebook: skills, demystified, on the Anthropic SDK
├── agent_subagent_orchestrator_starter.ipynb          # Notebook: agent → sub-agents → orchestrator on the Anthropic SDK
│
├── Rag_react/                                         # ReAct vs one-shot RAG: notebook, eval, Streamlit demo
│   ├── ReAct_Agent.ipynb      # The ReAct loop on top of Module 3's agentic RAG, run side by side
│   ├── react_agent.py         # The loop, tools and prompt (shared by the notebook and the app)
│   ├── rag_helpers.py         # Module 3's agentic RAG pipeline (router, Qdrant, SerpApi)
│   ├── golden_answers.json    # Expected answers, key facts and 10-K quotes for the six questions
│   ├── demo_runs/             # Six saved, hand-audited runs replayed by Demo mode
│   ├── main.py                # Streamlit app: Overview · Compare · Results
│   └── Agentic_RAG/qdrant_data/  # Uber FY2021 + Lyft FY2020–22 10-Ks, OpenAI Agents SDK docs
│
└── advance-customer-support-agent-feature-A2A-MCP-ADK/   # Hands-on capstone project
    ├── cs_agent/          # The agent package — ADK agents, A2A infra, security pipeline
    │   ├── agents/        # ADK agent definitions (Judge, Mask, Sequential pipeline)
    │   ├── a2a/           # A2A protocol layer (JSON-RPC server, client, task managers)
    │   ├── security/      # SecurityBlocker, sanitizer, and DLP-based PII masker
    │   └── evaluation/    # Security evaluation suite (95 test scenarios)
    ├── mcp_toolbox/       # MCP Toolbox config — exposes PostgreSQL as MCP tools
    ├── diagram.png        # System architecture diagram
    └── README.md          # Full setup + walkthrough for the project
```

> **Note:** This module is taught primarily through the hands-on project below, with supporting
> notebooks and the ReAct vs RAG demo (see the next sections). The conceptual companion lives in
> [`study-material/`](study-material/) — `lesson.md`, `key-concepts.md`, `exercises.md`, `quiz.md`,
> and `recap-and-preview.md` — but here the system *is* the lesson: read the concepts, then go run it.

---

## Companion Notebook: How Skills Work Under the Hood

**[`how_skills_work_under_the_hood.ipynb`](how_skills_work_under_the_hood.ipynb)**
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/rkarmaka/multi-agent-course/blob/main/modules/Module_4_Multi_Agent_Systems_Orchestration/how_skills_work_under_the_hood.ipynb)

A short, runnable peek behind the curtain of **Agent Skills**. It takes the `market-sizing` skill and
shows that a skill is — at its core — **just a markdown file of instructions**, then rebuilds its
behavior from scratch on the raw **Anthropic Python SDK**, one step at a time:

- A skill is a `SKILL.md` file: **frontmatter** (routing metadata) + **body** (the instructions).
- Stripping the frontmatter and passing the body as the **`system`** prompt is the whole trick.
- What an Anthropic API call actually looks like — `system` vs `messages`, and the response's
  **content blocks**.
- Why the model is **stateless**, and how a `history` list gives a conversation memory.
- An **ablation** (same question, no system prompt) that makes visible exactly what the skill buys you.
- How running a skill *in Claude Code* differs from running it *via the SDK* (triggering, tools, memory).

It's **Colab-ready**: hit the badge above (or *Runtime → Run all*) — it installs the SDK, pulls the
skill file from GitHub, and reads your `ANTHROPIC_API_KEY` from Colab **Secrets**. Running locally
works too; the setup cells fall back to a `.env` file or a hidden prompt.

> **Why it's here:** Module 4 is about coordinating *many* agents, but every agent in the capstone is
> still driven by instructions fed to a model. This notebook grounds that intuition at the smallest
> possible scale — one instruction file, one API call — before you scale up to ADK agents talking over
> A2A and MCP.

---

## ReAct vs One-Shot RAG

**[`Rag_react/`](Rag_react/)**

Module 3's agentic RAG router makes **one** decision: pick a source, retrieve once, answer. That breaks
on questions that need several lookups, more than one source, or arithmetic. This folder wraps the
same pipeline in a ~40-line **ReAct loop** (Thought → Action → Observation, repeated) and measures the
difference on six such questions about Uber's and Lyft's 10-Ks.

| | One-shot RAG | ReAct |
|---|---|---|
| Key facts correct (6 questions, 16 facts) | 7/16 (44%) | 16/16 (100%) |
| Avg time per question | 12.6s | 19.6s |
| Cost, all six | $0.0099 | $0.0163 (1.6×) |

*Saved runs on `gpt-5.6-luna`, recorded and audited 2026-09-25.*

**The lesson is in the failures.** When retrieval misses, one-shot RAG doesn't say *I don't know*: it
answers from memory and still cites the documents. For example, it put Lyft's long-term debt at
$1.73B where the balance sheet says $803.2M, and reported 218M MAPCs while citing a page that says 208M.
ReAct fixes this with one focused search per fact, a calculator, and later steps that build on
earlier results. The loop alone isn't enough, though. Three tool and prompt choices matter just as much:

- Tools return **raw chunks**, not an LLM summary (a summarising step slipped memorised figures in).
- `search_10k` **filters to one filing** and says when a filing isn't in the collection.
- The prompt allows **only figures that appear in an Observation**.

**How correctness is checked.** Each answer is scored against `golden_answers.json`: every 10-K figure
there is quoted from the filing, and the key facts are matched with regexes. Because regexes only
check key figures, every saved answer was also **audited by hand** against the filing text, including
side claims (the notes are stored in each `demo_runs/Q*.json` and shown in the app).

### Run it

```bash
cd Rag_react
python3.11 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# .env with openai_api_key=... and serp_api_key=...
streamlit run main.py        # the app
jupyter notebook ReAct_Agent.ipynb
pytest tests                 # 18 headless tests for the app and the grader
```

The app has three pages:

- **Overview:** the problem, both architectures, and the six questions with the expected answer, both
  agents' outputs, a correct/wrong verdict and the audit note.
- **Compare:** ask one question and watch both agents answer side by side. Turn on
  **🎬 Demo mode** to replay a saved run with no API calls (use this in class).
- **Results:** the scoreboard: facts matched, tool path, time and cost per question.

A live run of one of the six questions replaces its saved recording only if ReAct gets every golden fact
right, and a replaced recording loses its audit note until someone re-checks it.

**Known limits:** web figures (market cap, latest MAPCs) change over time; the web tool doesn't judge
source quality; and Q4's price-to-sales ratio divides today's market cap by 2021 revenue, which tests
combining sources but isn't a ratio an analyst would use.

---

## The Project: Advanced Customer Support Agent

**[`advance-customer-support-agent-feature-A2A-MCP-ADK/`](advance-customer-support-agent-feature-A2A-MCP-ADK/)**

A customer-support agent, with both a CLI and a live web UI, that ties all three protocols together in one running system. It's a
deliberately small but realistic example: a support agent that can look up orders, modify them under
business rules, and remember past conversations — wrapped in a security pipeline that runs as its own
set of agents.

How the pieces map to the module's concepts:

| Concept | Where it shows up in the project |
|---|---|
| **ADK** | The support agent, the Security Judge, and the Data Masker are all ADK `LlmAgent`s (Gemini 2.5 Flash); the Judge → Mask pipeline is a `SequentialAgent`. |
| **A2A** | The Judge (port `10002`) and Masker (port `10003`) run as standalone A2A servers; the CLI calls them over JSON-RPC for every request and refuses to start if they're unreachable. |
| **MCP** | Database operations (`get-order-status`, `find-customer-orders`, `update-order-status`) are exposed through the **MCP Toolbox** server, not hard-coded into the agent. |
| **Security pipeline** | Input sanitization → an A2A Security Judge (100+ regex patterns) → a Guardrail agent (safe and on-topic?) → the agent → A2A PII masking via Google Cloud DLP on the way out. |
| **Shared memory** | Mem0: recalled before every agent call and shown with relevance scores; the user's message is saved after every turn. |
| **Observability** | Arize Phoenix: one trace per message, with a span for every layer, Gemini call and MCP tool call. The web UI links each answer to its trace. |

Run `./run.sh web` inside the project for the chat (`:8000`), the live architecture view (`/architecture`) and Phoenix (`:6006`). **[`docs/build-log/index.html`](advance-customer-support-agent-feature-A2A-MCP-ADK/docs/build-log/index.html)** walks through how each piece was built, which bugs are left in on purpose, and a class demo script.

The project's own [`README.md`](advance-customer-support-agent-feature-A2A-MCP-ADK/README.md) has the
full prerequisites, step-by-step setup (PostgreSQL, MCP Toolbox, A2A servers, the CLI), the request
flow, and a troubleshooting guide. Start there once you've got the conceptual picture above.

---

## Assignment 3: Customer Support

**[`Assignment_3_Customer_Support/`](Assignment_3_Customer_Support/README.md)** — build the project above **from an
empty folder**: first as a CLI, then as a streaming web UI over the same pipeline. No starter code, only Markdown:
a plain-language [`README`](Assignment_3_Customer_Support/README.md), the [`PRD`](Assignment_3_Customer_Support/PRD.md),
an exhaustive [`SPEC`](Assignment_3_Customer_Support/SPEC.md) for coding agents, a ten-stage
[build guide](Assignment_3_Customer_Support/TECHNICAL.md) where the student makes a decision, runs a check and logs
what happened at every stage, and seven [gold sets](Assignment_3_Customer_Support/EVALS.md) that grade every guard
on both sides: attacks blocked **and** real customers not blocked.

---

## Environment Setup

The capstone targets **Python 3.12+**. Create an isolated conda environment before installing:

```bash
conda create -y -n customer-support python=3.12   # creates Python 3.12.x
conda activate customer-support
cd advance-customer-support-agent-feature-A2A-MCP-ADK
pip install -r requirements.txt
```

See the project [`README.md`](advance-customer-support-agent-feature-A2A-MCP-ADK/README.md#3--python-dependencies)
for the full dependency setup (Phoenix observability + OTel pinning).

---

## Tech Stack

| Category | Library / Tool |
|---|---|
| Agent framework | `google-adk` (ADK — `LlmAgent`, `SequentialAgent`, `Runner`) |
| Model | `gemini-2.5-flash` via Vertex AI |
| Tool protocol | MCP Toolbox (`toolbox-core`) over PostgreSQL |
| Agent-to-agent | A2A protocol — JSON-RPC 2.0 / HTTP with agent cards + SSE streaming (FastAPI) |
| Memory | `mem0ai` (persistent, cross-session memory) |
| Security | SecurityBlocker (regex), Google Model Armor, Google Cloud DLP (PII masking) |
| Database | PostgreSQL (via Docker) + `psycopg2-binary` |
