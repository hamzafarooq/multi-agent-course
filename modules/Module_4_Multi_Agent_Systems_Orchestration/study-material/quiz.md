# Module 04 — Quiz

<!-- INSTRUCTOR: The quiz-me skill uses these. Answers are here so Claude can check,
     but the rule is Claude NEVER shows them before the learner attempts. Hint first. -->

## Q1. What problem does a protocol layer solve, and what does it replace?
- Type: explain-why
- **Answer:** Without it, every agent-to-agent and agent-to-tool connection is custom glue — an
  N² tangle of point-to-point integrations that breaks when anything moves. A protocol layer
  replaces that with shared *standards* (MCP, A2A, ADK) so any agent or tool talks to any other
  the same way, regardless of who built it.
- **Hint:** Think about what happens to the number of connections as agents and tools multiply.

## Q2. In the capstone, where do the database operations live, and how does the agent get them?
- Type: recall
- **Answer:** Not in the agent's code — they live in the **MCP Toolbox** server, defined in
  `tools.yaml` (`get-order-status`, `find-customer-orders`, `action-log`). The agent
  **discovers them at runtime** by loading the toolset (`load_toolset("cs_agent_tools")`) and
  never touches raw SQL.
- **Hint:** The agent doesn't import SQL; it asks a server what tools exist.

## Q3. How is calling an A2A agent different from spawning a Module-2 subagent?
- Type: application
- **Answer:** A Module-2 subagent is an in-process spawn by the orchestrator. An A2A agent is an
  independent **network service** with a published **agent card**, called over JSON-RPC / HTTP
  (e.g. the Judge on `:10002`). It can be in any language, deployed and scaled separately; the
  caller only needs its card, not its code.
- **Hint:** One lives in the same process; one lives behind a URL.

## Q4. Match each ADK primitive to its job: `LlmAgent`, `SequentialAgent`, `Runner`.
- Type: recall
- **Answer:** `LlmAgent` = a single agent (model + instruction + tools). `SequentialAgent` =
  runs its sub-agents in order (e.g. Judge → Mask). `Runner` = drives an agent — manages the
  session, feeds the message, and streams events until the final response (it runs the loop).
- **Hint:** One *is* an agent, one *chains* agents, one *executes* an agent.

## Q5. Summarize how MCP, A2A, and ADK compose, using the words define, connect, feed.
- Type: explain-why
- **Answer:** **ADK defines** the agents (`LlmAgent`, `SequentialAgent`, `Runner`); **A2A
  connects** them as network services (agent cards + JSON-RPC, Judge and Masker on their own
  ports); **MCP feeds** them tools (the Toolbox publishes the Postgres toolset). Each layer is
  independently swappable without touching the others.
- **Hint:** Three verbs, three layers — one each.

## Q6. The security pipeline runs sanitize → Judge → agent → Mask. Why is sanitize before the Judge, and why is masking on the output?
- Type: application
- **Answer:** `sanitize_input()` is a cheap **local** check (character whitelist, length,
  Model Armor) — run it first to reject obvious garbage before paying for an LLM call to the
  Judge. Masking is on the **output** because PII can only leak in what the agent *says back*;
  Google Cloud DLP strips it on the way out, after the agent has produced its response.
- **Hint:** Cheap-before-expensive on the way in; PII can only escape on the way out.
