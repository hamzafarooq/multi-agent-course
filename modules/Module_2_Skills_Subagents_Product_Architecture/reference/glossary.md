# Reference — Module 02 Glossary

<!-- INSTRUCTOR: Module-local terms. The course-wide source of truth is
     modules/Module_1_Agent_Foundations_Harness_System_Design/reference/glossary.md — keep these consistent with it. -->

- **Agent** — A Claude session with a system prompt, a task, and the ability to take actions
  (incl. spawning other agents). A chatbot responds; an agent acts.
- **Subagent** — An agent spawned by another agent with its own isolated context, task, and
  tools; returns a result to the orchestrator.
- **Orchestrator** — The spawning agent; owns coordination, not execution.
- **Isolated context window** — A subagent's private context; raw work stays there, only a
  summary returns, keeping the main session clean.
- **Coordination layer / shared spec** — The artifact (e.g. API contract) all agents work from
  so parallel agents stay consistent without communicating.
- **Specialization** — Dividing work by domain (function / layer / dimension), not volume.
- **`.claude/agents/`** — Folder of subagent definitions; each markdown file is that agent's
  system prompt.
- **Sprint Zero** — Multi-agent Claude Code system: product URL + 3 answers → six spec docs +
  a working full-stack app (sequential spec writers → parallel builders → QA).
- **Three-layer architecture** — Frontend (React/Next.js) → Backend (Node/Express + Supabase) →
  AI backend (Claude API, embeddings, RAG). See `three-layer-architecture.md`.
- **API contract** — The document defining every endpoint before code is written; the handoff
  that lets backend and frontend agents build in parallel.
