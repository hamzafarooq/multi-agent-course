# Module 04 — Key Concepts (Glossary)

<!-- INSTRUCTOR: Short, accurate definitions Claude uses to stay precise.
     The explain-eli5 skill reads from here to simplify without becoming wrong. -->

- **Protocol layer** — A small set of shared standards (MCP, A2A, ADK) that let any agent or
  tool talk to any other the same way, replacing N² point-to-point integration glue.
- **MCP (Model Context Protocol)** — The standard for exposing *tools and data sources* to an
  agent. You run an MCP server; the agent discovers and calls its tools at runtime.
- **MCP server / Toolbox** — A process that publishes operations as tools. In the capstone, the
  MCP Toolbox wraps PostgreSQL and serves `get-order-status`, `find-customer-orders`,
  `action-log` from a `tools.yaml` config — the agent loads the toolset, never raw SQL.
- **A2A (Agent-to-Agent)** — The standard for one agent to invoke *another agent* as an
  independent service over JSON-RPC 2.0 / HTTP, with optional SSE streaming.
- **Agent card** — A JSON description an A2A agent publishes: its name, URL, capabilities
  (e.g. `streaming`), and skills — so callers can discover what it does without importing it.
- **JSON-RPC 2.0** — The request format A2A uses; method `tasks/send` (sync) or
  `tasks/sendSubscribe` (SSE streaming), posted to the agent's `/rpc` URL.
- **ADK (Agent Development Kit)** — Google's framework for *defining* agents: `LlmAgent`,
  `SequentialAgent`, and the `Runner`.
- **`LlmAgent`** — A single ADK agent: a model (`gemini-2.5-flash`), an `instruction` (its system
  prompt), and a list of `tools`. The support agent, Judge, and Masker are each one.
- **`SequentialAgent`** — An ADK agent that runs its `sub_agents` in order. The capstone's
  `security_pipeline` chains `[judge_agent, mask_agent]`.
- **`Runner`** — The ADK component that drives an agent: manages the session, feeds the user
  message, and streams events until `is_final_response()`. It runs the agent loop for you.
- **Compose rule** — **ADK defines, A2A connects, MCP feeds.** Each layer is independently
  swappable without touching the others.
- **Security pipeline** — Defense in depth around the agent: `sanitize_input()` (local) → A2A
  Security Judge (LLM + 100+ regex → pass or `BLOCKED`) → the agent → A2A Data Masker (Cloud DLP
  PII masking on output).
- **Security Judge** — An A2A `LlmAgent` (port `10002`) that evaluates input for SQL injection,
  XSS, and other threats, returning the message unchanged or `BLOCKED`.
- **Data Masker** — An A2A `LlmAgent` (port `10003`) that masks PII in the agent's output via
  Google Cloud DLP before it reaches the user.
- **Mem0** — Persistent, cross-session memory the support agent searches by `USER_ID` to recall
  past conversations and preferences.
- **Startup order** — PostgreSQL → MCP Toolbox → A2A servers → (Phoenix) → agent. Each service
  depends on the one before it; the CLI refuses to start if the A2A servers are unreachable.
