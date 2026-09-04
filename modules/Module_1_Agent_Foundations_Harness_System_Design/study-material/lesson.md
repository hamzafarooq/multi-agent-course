# Module 01 — The Agent Loop: ReAct, Architectures, and the Claude Code Harness

## Learning objectives

By the end of this module the learner can:
- [ ] Explain what makes an LLM an "agent" and why you'd build one
- [ ] Describe the agent loop (prompt → intent → tool execution → observation → repeat)
- [ ] Distinguish the four levels of agentic architecture and when to use each
- [ ] Explain what a ReAct agent is (reasoning + acting)
- [ ] Explain what an agent harness is and what it adds around the model

## Prerequisites
- Have used ChatGPT or Claude before; new(ish) to building agents

---

## Concept 1 — What is an agent?

[Plain definition: an AI agent is software that interacts with its environment, gathers
data, and takes self-determined steps toward a goal. Contrast "copy-paste from a chatbot"
vs. an agent that acts. Use the LLM + Tools/Actions + State picture from the deck.]

**Check:** What's the difference between asking ChatGPT to write an email and an *agent*
that sends it?

## Concept 2 — The agent loop

[Walk the loop: prompt/context starts a task → LLM identifies intent and decides on tool
use → tools run externally, outputs come back → results feed back into context → repeat
until stop_reason says done.]

**Check:** What ends the loop?

## Concept 3 — Four levels of agentic architecture

[Level 1: Simple LLM. Level 2: LLM + tools (deterministic, finite branches). Level 3:
Thinking & reasoning (dynamic plans, ambiguous requests). Level 4: Agent-to-agent. Map the
"deterministic ↔ autonomy" and "complexity" axes. Mention the signs you've outgrown a level:
branching explosion, unpredictable user paths, dynamic tool selection, multi-step reasoning.]

**Check:** A task is a clean flowchart with <20 branches, done in seconds. Which level?

## Concept 4 — ReAct agents (Reason + Act)

[A ReAct agent combines chain-of-thought reasoning with external tool use. Walk the
Thought → Action → Observation → (answer found?) cycle. Tie back to the loop in Concept 2.]

**Check:** Why interleave reasoning *with* acting instead of planning everything up front?

## Concept 5 — The agent harness

[The harness is the deterministic execution + orchestration layer around the LLM that makes
it a stateful, autonomous agent rather than a text predictor. "The model thinks. The harness
does." Components: context management, agent loop, tools, memory, permissions, hooks.]

**Check:** In one line — what does the harness do that the model itself doesn't?

---

## Summary
1. An agent acts toward a goal; the agent loop is how it does that step by step.
2. Architectures range from a plain LLM to multi-agent systems — pick the simplest that fits.
3. ReAct = reasoning interleaved with tool use; the harness is the runtime body around it.

## Where to next
- Do `exercises.md` for hands-on, or ask to be quizzed (`quiz.md`).