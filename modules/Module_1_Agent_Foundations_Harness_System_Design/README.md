# Module 1 — Agent Foundations, Agent Harness & System Design

Demystify what an agent actually *is*: the perceive → reason → act loop, the **ReAct**
pattern, the four levels of agentic architecture, and what a production **harness** (like
Claude Code) adds on top of a 50-line loop. You'll build a ReAct agent from scratch — no
framework, no magic — then see what two real frameworks add on top.

> **New here?** This module is part of the [FDE Agent Engineering Bootcamp](../../README.md).
> Open the repo root in Claude Code and type `/start` — Claude reads `CLAUDE.md` and becomes
> your tutor for this module. The files below are what it teaches from.

## What this module covers

- The agent loop: prompt/context → intent → tool execution → observation → repeat until done
- **ReAct** (Reasoning + Acting)
- The four levels of agentic architecture, and when to use each
- Agent vs. workflow vs. chatbot — and how to defend the call
- Debugging an agent run by reading its trace
- What an agent harness adds around the model (context management, tools, memory, permissions)
- Agent frameworks: AgentPro and Hugging Face smolagents

## What's in this folder

### `study-material/` — the lesson and its support files

The tutor teaches from these (see `CLAUDE.md` at the repo root).

| File | What it is |
|------|------------|
| `lesson.md` | The main teaching content — what an agent is, the agent loop, the four architecture levels, ReAct, and the harness. |
| `key-concepts.md` | A quick glossary of the module's core terms for fast review. |
| `exercises.md` | Hands-on exercises (e.g. classify real tasks into the four architecture levels). |
| `quiz.md` | Self-check questions. The tutor hints before revealing answers. |
| `recap-and-preview.md` | A ~15-minute pre-class warm-up, used by the `warmup` skill. |

### `reference/` — deep dives

Background the tutor pulls from when you want more than the lesson.

| File | What it is |
|------|------------|
| `agent-architectures.md` | Deep dive on the four levels of agentic architecture. |
| `claude-code-anatomy.md` | How the Claude Code harness is layered — context management, the agent loop, tools, memory, and permissions. |
| `glossary.md` | The course-wide glossary — the source of truth for terminology. |

### `coding-examples/` — hands-on notebooks

The lab for this module. See [`coding-examples/README.md`](coding-examples/README.md) for setup,
API keys, and the suggested order.

| Notebook | What it covers |
|----------|----------------|
| `Agent Pro ReAct.ipynb` | A ReAct agent built from scratch — **start here**. |
| `AgentPro Starter Code.ipynb` | The same pattern through the AgentPro framework. |
| `Smol Agents Updated.ipynb` | Hugging Face smolagents — a `CodeAgent` and a JSON agent. |

## How to study this module

Type `/start` at the repo root, then just chat — Claude auto-invokes the right skill. Some openers:

- *"Teach me module 1"* — runs the interactive lesson (`teach-module`)
- *"Quiz me on the agent loop"* — assesses you and logs weak spots (`quiz-me`)
- *"Explain ReAct like I'm five"* — re-explains a concept simply (`explain-eli5`)
- *"Let's do the build-along for module 1"* — coaches you through the lab (`build-along`)
- *"I have class soon — warm me up for module 1"* — a ~15-min refresher (`warmup`)
- *"I don't get why ReAct beats plain planning"* — or any honest confusion

Say **"shorter"** or **"just tell me"** for direct answers, or **"go deeper"** for trade-offs and edge cases.

## What you'll be able to do after this module

- **Build** a ReAct loop from scratch — no framework, no magic.
- **Distinguish** the four levels of agentic architecture and pick the right one.
- **Read** a failed agent run like a stack trace and find the actual bug.
- **Decide** agent vs. workflow vs. chatbot, and defend it.
- **Name** what a production harness adds to a 50-line loop, and why each piece exists.
