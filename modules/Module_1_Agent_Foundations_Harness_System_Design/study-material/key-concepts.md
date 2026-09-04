# Module 01 — Key Concepts (Glossary)

- **AI agent** — Software that interacts with its environment, collects data, and takes
  self-determined steps toward a predetermined goal.
- **Agent loop** — The cycle: prompt/context → intent → tool execution → observation → feed
  results back → repeat until a stop condition.
- **Tool / action** — An external capability the LLM can invoke (search, calculator, code
  interpreter, an API).
- **ReAct** — "Reasoning and Acting"; a framework combining chain-of-thought reasoning with
  external tool use (Thought → Action → Observation, looped).
- **Agentic architecture levels** — L1 Simple LLM, L2 LLM+tools, L3 reasoning, L4 agent-to-agent;
  spanning deterministic/predefined to autonomous/self-reflective.
- **Agent harness** — The deterministic execution and orchestration layer around an LLM
  (context management, loop, tools, memory, permissions, hooks) that makes it a stateful agent.
- **Context management** — The agent's working memory: deciding what to include, exclude, and
  update in what the model sees.
- **stop_reason** — The signal that the loop is complete and no further tool calls are needed.
