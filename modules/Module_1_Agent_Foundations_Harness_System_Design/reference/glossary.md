# Course Glossary (Source of Truth)

<!-- INSTRUCTOR: Master list of terms across all modules. Per-module key-concepts.md files
     can repeat the subset relevant to that module. Keep definitions accurate — the
     explain-eli5 skill relies on these. -->

- **AI agent** — Software that interacts with its environment, collects data, and takes
  self-determined steps toward a goal.
- **Agent loop** — prompt/context → intent → tool execution → observation → repeat until done.
- **ReAct** — Reasoning + Acting; chain-of-thought reasoning interleaved with tool use.
- **Agent harness** — Deterministic execution/orchestration layer around an LLM.
- **Context management** — Deciding what the model sees: include, exclude, update.
- **Tool / MCP server** — External capability Claude can call; MCP = Model Context Protocol,
  the standard bridge between Claude and tools.
- **CLAUDE.md** — Project memory/instructions file, loaded automatically each session.
- **Skill** — A reusable instruction pack (a SKILL.md + optional files) auto-invoked by its
  description; "a saved prompt with superpowers."
- **Subagent** — A delegate with its own isolated context, system prompt, and tools.
- **Hook** — A deterministic automation that runs on an event (e.g. before/after a tool).
- **[add more as your course grows]**
