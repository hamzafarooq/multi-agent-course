# Module 02 — Key Concepts (Glossary)

<!-- INSTRUCTOR: Short, accurate definitions Claude uses to stay precise.
     The explain-eli5 skill reads from here to simplify without becoming wrong. -->

- **Agent** — A Claude session with a system prompt (role, constraints, tools), a task, and
  the ability to take actions — read/write files, call APIs, spawn other agents. A chatbot
  responds; an agent *acts*.
- **Subagent** — An agent spawned by another agent to handle a specific piece of work, with
  its own isolated context, task, and tools; returns a result when done.
- **Orchestrator** — The agent that spawns and coordinates subagents. Its job is coordination,
  not execution: decide what's done, who does it, and how results combine.
- **Isolated context window** — Each subagent has its own context; raw work lives there and
  only a summary returns to the orchestrator, keeping the main session clean.
- **Orchestrator + subagents pattern** — The common multi-agent shape: orchestrator fans out
  tasks to subagents (sequential or parallel) and synthesizes their results.
- **Sequential vs. parallel** — Run steps sequentially when each depends on the last; run them
  in parallel when independent. Parallel wall-clock time = the slowest branch, not the sum.
- **Specialization** — Dividing work by domain (function / layer / dimension) rather than by
  volume, so each agent has clear inputs and outputs and never needs to talk mid-task.
- **Coordination layer (shared spec)** — The artifact (e.g. an API contract) all agents work
  from, so parallel agents stay consistent without communicating.
- **`.claude/agents/`** — The folder where subagents are defined; each markdown file *is* that
  agent's system prompt.
- **Failure modes** — Context leakage, coordination gaps, cascading failures, prompt drift —
  each prevented by a specific design move (minimal briefs, shared spec, staged isolation,
  acceptance-criteria-style prompts).
- **Sprint Zero** — A multi-agent Claude Code system: from a product URL + three answers it
  produces six spec docs and a working full-stack app (sequential spec writers → parallel
  builders → QA validator).
