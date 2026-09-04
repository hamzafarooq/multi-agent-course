# Module 02 — Recap & Preview (15-Minute Warm-Up)

<!-- INSTRUCTOR: A quick "before class" bridge. Recaps Module 01 and previews Module 02.
     Designed for a ~15-min review with Claude right before the live session. -->

## Last time (Module 01 — The Agent Loop, ReAct & the Harness)
The big ideas you should still have in your head:
- An agent is a model running in a **loop**, using tools, until a goal is met — not a smarter chatbot.
- The four levels of agentic architecture, and picking the simplest one that fits.
- **The model thinks. The harness does** — context management, tools, memory, permissions, hooks.

**Quick gut-check:** In one line, what does the harness do that the model itself doesn't?

## How it connects
Module 01 was *one* agent in a loop. Module 02 asks what happens when one agent isn't enough —
when you spawn a *team* of agents that coordinate. Same agent loop, now multiplied and
orchestrated.

## Coming up (Module 02 — Skills, Subagents & Multi-Agent Orchestration)
What you'll be able to do after today:
- Define an agent precisely, and explain what a **subagent** adds
- Explain why **isolated context windows** are the whole reason subagents work
- Use the orchestrator pattern: sequential where work depends, parallel where it doesn't
- Write a real subagent in `.claude/agents/` and divide work by specialization
- Trace **Sprint Zero** — six spec docs and a working app from one URL and three answers

**Watch for:** the difference between *sequential* and *parallel* work, and the idea that a
**shared spec** (like an API contract) is what lets parallel agents avoid talking to each other.
That's the trick the whole pattern rests on.

## If you only remember one thing walking into class
> A subagent is an agent with its own clean context. Multi-agent power comes from isolation +
> specialization + a shared spec — not from one bigger, longer prompt.
