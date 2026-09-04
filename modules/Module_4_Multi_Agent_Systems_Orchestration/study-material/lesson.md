# Module 04 — Multi-Agent Systems & the Protocol Layer

<!-- INSTRUCTOR: This is the teaching content Claude walks the learner through.
     Each ## is roughly one "concept" Claude presents, then checks understanding on.
     Source: the capstone project advance-customer-support-agent-feature-A2A-MCP-ADK
     (the system IS the lesson) + the module README. Keep chunks short. -->

## Learning objectives

By the end of this module the learner can:
- [ ] Explain why a **protocol layer** beats bespoke glue code once you have >1 agent or tool
- [ ] Describe **MCP** and why exposing tools through an MCP server beats hard-coding them
- [ ] Describe **A2A** — agent cards, JSON-RPC over HTTP — and when to run an agent as a service
- [ ] Describe **ADK** primitives: `LlmAgent`, `SequentialAgent`, and the `Runner`
- [ ] Explain how the three layers compose: ADK *defines*, A2A *connects*, MCP *feeds*
- [ ] Trace the capstone's security pipeline (sanitize → A2A judge → agent → A2A mask) end to end

## Prerequisites
- Module 2 (orchestrator + subagents, isolated context, specialization). This module replaces
  in-process subagents with agents that talk **over the network** through shared protocols.

---

## Concept 1 — Why a protocol layer

[In Module 2 the orchestrator and its subagents lived in one process — the orchestrator
*spawned* them directly. That works until agents are built by different teams, written in
different frameworks, or need to run as separate services that scale independently. Then every
new connection is custom glue: agent A learns agent B's function signature, C learns D's API,
and you get an N² tangle of point-to-point integrations that breaks whenever anything moves.

A **protocol layer** is the fix: a small set of *standards* so any agent or tool talks to any
other the same way, regardless of who built it. Think USB — you don't rewire your laptop for
each device; you agree on a plug. Module 4 teaches the three plugs that matter: **MCP** (how
agents get tools), **A2A** (how agents call other agents), and **ADK** (how agents are
defined). The throughline: standards replace glue.]

**Check:** What goes wrong with point-to-point integration once you have several agents and
tools, and what does a protocol layer replace it with?

## Concept 2 — MCP: the standard way to give an agent tools

[**MCP (Model Context Protocol)** is the standard for exposing *tools and data sources* to an
agent. Instead of baking a database call into your agent's code, you run an **MCP server** that
publishes the operations as tools; the agent **discovers them at runtime** and calls them.

In the capstone, the **MCP Toolbox** server wraps PostgreSQL and publishes a toolset —
`get-order-status`, `find-customer-orders`, `action-log` — defined in a `tools.yaml` config, not
in Python. The agent loads the toolset on startup (`toolbox_client.load_toolset("cs_agent_tools")`)
and never sees raw SQL. Why this matters: the tools become swappable and reusable. Change the
database, fix a query, add a tool — you edit the MCP server's config, and *every* agent that
points at it gets the change. The agent code doesn't move.]

**Check:** In the capstone, where do the database operations live — in the agent's code or
somewhere else? What does the agent do to get them?

## Concept 3 — A2A: the standard way for agents to call agents

[**A2A (Agent-to-Agent)** is the standard for one agent to invoke *another agent* as an
independent service. Each agent publishes an **agent card** — a small JSON description of its
name, URL, capabilities (e.g. streaming), and skills — so callers can discover what it does.
Others invoke it over **JSON-RPC 2.0 / HTTP** (method `tasks/send`, or `tasks/sendSubscribe`
for SSE streaming).

In the capstone, the **Security Judge** runs as its own server on port `10002` and the **Data
Masker** on `10003`. The CLI doesn't import them — it POSTs a JSON-RPC request to their URLs for
every message, and *refuses to start* if they're unreachable. That's the A2A shift from Module
2: a subagent there was an in-process spawn; an A2A agent is a **network service** with a
published contract. It can be written in any language, deployed separately, and scaled on its
own — the caller only needs its agent card.]

**Check:** What's in an agent card, and how is calling an A2A agent different from spawning a
Module-2 subagent?

## Concept 4 — ADK: the standard way to define an agent

[**ADK (Agent Development Kit)** is Google's framework for *defining* the agents themselves.
Three primitives carry the module:
- **`LlmAgent`** — a single agent: a model (`gemini-2.5-flash`), an `instruction` (its system
  prompt), and a list of `tools`. The capstone's support agent, Judge, and Masker are each one.
- **`SequentialAgent`** — chains sub-agents so they run in order. The capstone's
  `security_pipeline` is `SequentialAgent(sub_agents=[judge_agent, mask_agent])` — Judge first,
  Masker second.
- **`Runner`** — the thing that actually *drives* an agent: it manages the session, feeds in the
  user message, and streams back events until `is_final_response()`. You don't call the model
  directly; the Runner runs the loop (that's the Module 1 agent loop, now framework-managed).

So ADK is the *definition* layer — it says what an agent is and how it executes.]

**Check:** Match each to its job: `LlmAgent`, `SequentialAgent`, `Runner`. Which one runs the
loop that drives the agent?

## Concept 5 — How the three layers compose

[The point of the capstone is that these aren't three separate topics — they're three layers of
one system:

    ADK   defines the agents      (LlmAgent: support, Judge, Masker; SequentialAgent pipeline)
    A2A   connects the agents     (Judge :10002 and Masker :10003 as JSON-RPC services)
    MCP   feeds the agents tools  (Toolbox server publishes the Postgres toolset)

Read it as one sentence: **ADK defines them, A2A connects them, MCP feeds them.** Each layer is
independent — you can swap the database behind MCP, rewrite the Judge in another language behind
A2A, or change the support agent's model in ADK — without touching the others. That
independence is exactly what the protocol layer buys you, and it's why this is the "action" end
of the course: agents stop being standalone chatbots and start coordinating as a system.]

**Check:** Say in one sentence what each layer does for the capstone, using the words define,
connect, feed.

## Concept 6 — Security as a pipeline of agents

[The capstone wraps the support agent in a **multi-layer security pipeline** — and the security
checks are *themselves agents*, reached over A2A. The flow around every user message:

    user input
      ↓  Layer 1: sanitize_input()      local — character whitelist, length cap, Model Armor
      ↓  Layer 2: A2A Security Judge     :10002 — LlmAgent + 100+ regex patterns → pass or "BLOCKED"
      ↓  the support agent               ADK LlmAgent + MCP tools + Mem0 memory
      ↓  Layer 3: A2A Data Masker        :10003 — Google Cloud DLP masks PII on the way out
    response to user

Note the shape: a cheap **local** check first (sanitize), then an **LLM-powered** check
(the Judge reasons *and* runs regex via a tool), then the agent, then masking on output. Defense
in depth — each layer catches what the previous can't, and the Judge being a separate A2A
service means you can harden or replace it without redeploying the support agent.]

**Check:** Why run a cheap local `sanitize_input()` before calling the LLM-powered Judge, rather
than just the Judge? And why is masking on the *output* side, not the input?

## Concept 7 — The capstone end to end

[Put it together. A user logs in (one of the seeded test users), and for each message:
1. **Sanitize** locally; reject garbage early.
2. **Judge** over A2A — block injection/XSS attempts before they reach the model.
3. The **support agent** (ADK `LlmAgent`) reasons, recalls history from **Mem0**, and calls
   **MCP** tools to read orders or log an action — note it *logs* write-intents to `actions_log`
   rather than mutating core tables directly.
4. **Mask** the response over A2A so no PII leaks out.

To run it you start five things *in order* — PostgreSQL → MCP Toolbox → A2A servers → (Phoenix
observability) → the agent — because each depends on the one before. That startup order is the
dependency graph of the protocol layer made visible: tools must exist before agents can load
them, and the A2A services must be up before the CLI that calls them will start.]

**Check:** Why does startup order matter — what breaks if you start the agent CLI before the
MCP Toolbox and the A2A servers?

---

## Summary
1. A **protocol layer** (MCP, A2A, ADK) replaces N² point-to-point glue with standards, so any
   agent or tool talks to any other the same way.
2. **ADK defines** agents (`LlmAgent`, `SequentialAgent`, `Runner`), **A2A connects** them as
   network services (agent cards + JSON-RPC), **MCP feeds** them discoverable tools — and the
   three layers are independently swappable.
3. The capstone proves it: a support agent wrapped in a sanitize → A2A-Judge → agent → A2A-Mask
   pipeline, with orders served through MCP and memory through Mem0.

## Where to next
- Do `exercises.md` (read an agent card, then add an MCP tool), or ask to be quizzed
  (`quiz.md`). To see it run, follow the project `README.md` and start the five services in
  order.
