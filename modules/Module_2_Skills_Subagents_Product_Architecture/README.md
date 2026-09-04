# Module 2 — Skills & Subagents: Product Architecture & Coordination

Go from *one* agent doing one thing well to a *coordinated system* of agents doing many things
at once. You'll learn what a subagent actually is, why **isolated context windows** are the
whole point, the **orchestrator + subagents** pattern (sequential where work depends, parallel
where it doesn't), and how to define your own subagents in `.claude/agents/`. The capstone is
**Sprint Zero** — a multi-agent system that turns a product URL and three answers into six spec
documents and a working full-stack app.

> **New here?** This module is part of the [FDE Agent Engineering Bootcamp](../../README.md).
> Open the repo root in Claude Code and type `/start` — Claude reads `CLAUDE.md` and becomes
> your tutor. The files below are what it teaches from.

## What this module covers

- What an agent is, precisely — and what a **subagent** adds
- Why isolated context windows beat one very long prompt
- The orchestrator pattern: coordination vs. execution, sequential vs. parallel, wall-clock math
- Defining a subagent in Claude Code (`.claude/agents/*.md`)
- Specialization as a design decision (by function / layer / dimension) and the shared-spec coordination layer
- Multi-agent failure modes (context leakage, coordination gaps, cascading failures, prompt drift) and their fixes
- **Sprint Zero** — the pattern made real, end to end

## What's in this folder

### `study-material/` — the lesson and its support files

The tutor teaches from these (see `CLAUDE.md` at the repo root).

| File | What it is |
|------|------------|
| `lesson.md` | The main teaching content — agents vs. subagents, isolated context, the orchestrator pattern, defining subagents, specialization, failure modes, and Sprint Zero. |
| `key-concepts.md` | A quick glossary of the module's core terms for fast review. |
| `exercises.md` | Hands-on exercises — design an agent team, then write a real subagent in `.claude/agents/`. |
| `quiz.md` | Self-check questions. The tutor hints before revealing answers. |
| `recap-and-preview.md` | A ~15-minute pre-class warm-up, used by the `warmup` skill. |

### `reference/` — deep dives

Background the tutor pulls from when you want more than the lesson.

| File | What it is |
|------|------------|
| `multi-agent-patterns.md` | The orchestrator pattern, specialization patterns, failure modes, and how the shape generalizes. |
| `three-layer-architecture.md` | The full-stack picture the build agents target — frontend, backend, AI backend. |
| `infra-tools.md` | The six tools modern products run on — Supabase, Auth, Stripe, Git, GitHub, VS Code. |
| `glossary.md` | Module-local terms (kept consistent with the course-wide glossary in Module 1). |

### Lecture source (module root)

The raw decks/notes this module's teaching files were authored from:

| File | What it is |
|------|------------|
| `1_claude_code_ecosystem.md` | The Claude Code ecosystem and the move from one agent to many. |
| `2_agents_v_subagents.md` | Agents vs. subagents — the core lecture. |
| `3_Three_layer_architecture.md` | The three-layer (frontend / backend / AI backend) model. |
| `4_infra_tools.md` | The six infrastructure tools. |
| `5_sprint_zero.md` | Sprint Zero, the multi-agent capstone. |
| `v10-Module-2-skills-subagents-multi.pdf` | The slide deck. |

## How to study this module

Type `/start` at the repo root, then just chat — Claude auto-invokes the right skill. Some openers:

- *"Teach me module 2"* — runs the interactive lesson (`teach-module`)
- *"Quiz me on subagents"* — assesses you and logs weak spots (`quiz-me`)
- *"Explain isolated context like I'm five"* — re-explains a concept simply (`explain-eli5`)
- *"Let's do the module 2 exercises"* — coaches you through writing a subagent (`build-along`)
- *"I have class soon — warm me up for module 2"* — a ~15-min refresher (`warmup`)

Say **"shorter"** or **"just tell me"** for direct answers, or **"go deeper"** for trade-offs.

## What you'll be able to do after this module

- **Explain** why a subagent's isolated context beats one long prompt.
- **Design** an orchestrator + subagents system, choosing sequential vs. parallel correctly.
- **Write** a real subagent in `.claude/agents/` with scoped, acceptance-criteria-style prompts.
- **Diagnose** multi-agent failure modes and apply the design move that prevents each.
- **Trace** Sprint Zero end to end and recognize the same pattern in other problems.
