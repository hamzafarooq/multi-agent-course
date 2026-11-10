# Glossary

Every term on the pre-work path. `/prework-explain` uses this file. It mirrors the pre-work site, so the words here match the videos and the reading.

## The model

| Term | Meaning | Module | Book |
|---|---|---|---|
| **LLM** | A model that predicts the next token of text. Text in, text out. It doesn't read files, run commands or remember anything by itself. | M02 How LLMs work | §3.1 |
| **Token** | The unit a model reads and writes, roughly ¾ of an English word. Price, speed and limits are all counted in tokens. | M02 How LLMs work | §3.1 |
| **Context window** | The maximum number of tokens the model can consider in one call, including its own answer. Outside the window, nothing exists. | M02 How LLMs work | §3.1 |
| **Statelessness** | Each API call is independent. Apparent memory is the application resending earlier text. | M02 How LLMs work | §3.1 |
| **Temperature** | How random the next-token choice is. Low for extraction and code, higher for ideas. Never fully deterministic, which is why evals matter. | M02 How LLMs work | §3.1 |
| **Token cost** | You pay per input and output token on every call. Resent history and stuffed documents add up fast. | M02 How LLMs work | §3.1 |
| **Open vs. closed models** | Closed models (Claude, GPT) are API-only. Open-weight models (Llama, Qwen) can run on your own infrastructure for control, residency and cost. | M02 How LLMs work | §3.1 |

## Agent · CTL

| Term | Meaning | Module | Book |
|---|---|---|---|
| **Agent** | An LLM given tools and run in a loop that feeds results back, so it can act, observe and adjust instead of only replying. | M03 LLM → Agent | §3.1–3.2 |
| **Context (C)** | Everything the model sees on a turn: system prompt, history, tool descriptions and tool results. The agent's entire world. | M03 LLM → Agent | §3.1–3.2 |
| **Tools (T)** | Functions you define and describe. The model requests a call; your code decides whether to run it and returns the result. | M03 LLM → Agent | §3.1–3.2 |
| **Loop (L)** | Read → Plan → Act → Observe → Repeat, until the model answers without a tool call or a step limit is hit. | M03 LLM → Agent | §3.1–3.2 |
| **ReAct** | The reason-then-act-then-observe pattern most agent loops follow. | M03 LLM → Agent | §3.1–3.2 |
| **Trace** | The log of every step an agent took: what it saw, what it decided, what came back. The first thing you open when an agent misbehaves. | M03 LLM → Agent | §3.1–3.2 |

## The harness

| Term | Meaning | Module | Book |
|---|---|---|---|
| **Harness** | The runtime scaffolding around a model that manages the loop, tools, permissions and context. The model is the brain; the harness is the body. | M04 Harness & Claude Code | §3.3–3.4 |
| **Permissions** | Gates between the model and risky actions (running commands, deleting files, pushing). The harness asks; you decide. | M04 Harness & Claude Code | §3.3–3.4 |
| **Memory** | What survives between sessions. The model has none; the harness provides it via CLAUDE.md, skills and commands. | M04 Harness & Claude Code | §3.3–3.4 |
| **Claude Code** | Anthropic's agentic coding harness: the agent loop with tools for files, commands and search, plus permissions and memory, in a chat panel in your editor. | M04 Harness & Claude Code | §3.3–3.4 |
| **Plan mode** | Claude Code proposes a plan without changing anything until you approve it. Use it for anything bigger than one file. | M04 Harness & Claude Code | §3.3–3.4 |

## Extending it

| Term | Meaning | Module | Book |
|---|---|---|---|
| **CLAUDE.md** | A project file the harness loads into context at the start of every session: what this is, how it's built, how to run it, what to avoid. | M05 Extending the harness | Ch 2 |
| **Skills** | A named, packaged workflow (SKILL.md plus optional files) Claude runs on request. One word, infinite reuse. | M05 Extending the harness | Ch 4 |
| **MCP** | Model Context Protocol: a standard way to plug new tools into any harness, such as a browser, a database or Slack. | M05 Extending the harness | §3.12 |
| **Subagents** | Specialists with their own context window, tools and model. They keep big or separable tasks out of your main context. | M05 Extending the harness | Ch 5 |
| **Pipelines & agent teams** | Several agents chained or collaborating: research → write → review. The bridge into multi-agent systems in the bootcamp's Module 2. | M05 Extending the harness | Ch 6 |

## The product

| Term | Meaning | Module | Book |
|---|---|---|---|
| **Frontend** | What users touch: React in the browser. Never holds secrets. | M06 Full-stack architecture | §3.5–3.10 |
| **Backend** | The API behind the click: auth, data, business logic, and the place your API keys live. | M06 Full-stack architecture | §3.5–3.10 |
| **AI backend** | Where the intelligence runs: LLM calls, agents, retrieval. Often its own service so it can scale and be swapped. | M06 Full-stack architecture | §3.5–3.10 |
| **Streaming** | Sending the model's answer token by token as it's generated, so users see progress instead of a spinner. | M06 Full-stack architecture | §3.5–3.10 |
| **Docker** | Packages an app and everything it needs into an image that runs the same everywhere as a container. | M06 Full-stack architecture | §3.5–3.10 |
| **Deploy** | Putting your app on a server with a public URL so the client can use it. | M06 Full-stack architecture | §3.5–3.10 |

## In the bootcamp

| Term | Meaning | Module | Book |
|---|---|---|---|
| **RAG** | Retrieval-augmented generation: fetch only the relevant documents and put them in context, instead of everything. | Bootcamp |  |
| **Evals** | Systematic tests of an agent's outcomes and trajectories, so you catch regressions before your client does. | Bootcamp |  |
| **Guardrails** | Checks on inputs and outputs (e.g. Llama Guard) that block unsafe or off-policy behaviour. | Bootcamp |  |
| **Observability** | Tracing, dashboards, latency, cost and quality per request, for agents in production. | Bootcamp |  |
| **A2A** | Agent-to-agent protocol for coordinating independent agent services. | Bootcamp |  |
