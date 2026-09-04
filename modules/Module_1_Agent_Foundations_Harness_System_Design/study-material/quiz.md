# Module 01 — Quiz

## Q1. What turns a plain LLM into an "agent"?
- Type: recall
- **Answer:** The ability to take actions via tools and loop on the results toward a goal —
  not just produce text. (LLM + tools/actions + state, run in a loop.)
- **Hint:** Think about what happens *after* the model produces text.

## Q2. Put the agent loop steps in order.
- Type: recall
- **Answer:** Prompt/context → intent → tool execution → observation → feed back → repeat
  until stop_reason.
- **Hint:** It starts with context and ends with a stop condition.

## Q3. A task has 30+ flowchart nodes, users phrase requests unpredictably, and the agent
must choose which API to call from context. Which level, and why?
- Type: application
- **Answer:** Level 3 (reasoning) — branching explosion, unpredictable paths, and dynamic
  tool selection are the signals you've outgrown a deterministic L2 design.
- **Hint:** Review the "you'll know you need a different architecture when…" signals.

## Q4. In one sentence, what does the harness do that the model does not?
- Type: explain-why
- **Answer:** The model thinks (reasons/produces); the harness *does* — it runs the loop,
  executes tools, manages context/memory, and enforces permissions and hooks.
- **Hint:** "The model thinks. The harness ___."
