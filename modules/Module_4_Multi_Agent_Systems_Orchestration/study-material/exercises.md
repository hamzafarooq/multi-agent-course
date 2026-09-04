# Module 04 — Exercises

<!-- INSTRUCTOR: Hands-on tasks for the build-along skill. Goal first, then steps,
     then a "done when" check. Grounded in the capstone project. Exercises work even
     without the full stack running — they're about reading and reasoning about the
     protocol layer, with optional run-it stretches. -->

## Exercise 1 — Read an agent card and trace a call

**Goal:** Understand what A2A publishes and how a call actually travels.

**Steps:**
1. Open `cs_agent/a2a/factories.py`. Find `create_judge_server` and read its `AgentCard`.
2. Write down four things a caller learns from that card: its **URL**, its **capabilities**, its
   **skill**, and its **input/output modes**.
3. Open `cs_agent/a2a/client.py`. In `_call_sync`, identify the JSON-RPC **method**, the **URL**
   it posts to, and where the user's text sits in the payload.
4. In one sentence, explain how the CLI reaches the Judge *without importing the Judge's code*.

**Done when:** You can name the JSON-RPC method (`tasks/send`), the port (`10002`), and explain
that the agent card — not a Python import — is the contract between caller and agent.

**Stretch (optional):** Start the A2A servers (`python -m cs_agent.a2a.run_servers`) and
`curl` a `tasks/send` request to `http://localhost:10002/rpc` with a benign message, then a
SQL-injection-looking one, and compare the verdicts.

## Exercise 2 — Add a new MCP tool

**Goal:** Prove that tools live in the MCP server's config, not the agent's code.

**Steps:**
1. Open `mcp_toolbox/tools.yaml`. Read how an existing tool (e.g. `get-order-status`) is
   defined — its name, its SQL statement, its parameters.
2. Define a new read-only tool, e.g. `get-recent-orders`, that returns the N most recent orders
   across all users (or by status). Write only the YAML — no Python.
3. Note in `cs_agent/prompts.py` where you'd add a usage guideline so the agent knows when to
   call your new tool.
4. Explain why you did **not** have to edit the agent's Python to add a tool.

**Done when:** You have a valid tool entry in `tools.yaml` and can articulate that the agent
discovers it at runtime via `load_toolset`, so no agent code changed.

**Stretch (optional):** Run the full stack and ask the agent a question that should trigger your
new tool. Watch it discover and call the tool you only declared in YAML.

## Exercise 3 — Map the security pipeline

**Goal:** Trace defense-in-depth across the three layers and justify the ordering.

**Steps:**
1. In `cs_agent/agent_cli.py`, read `validate_input()` (Layers 1 and 2) and `_mask_response()`.
2. Draw the path of one message: input → sanitize → A2A Judge → agent → A2A Mask → output.
   Label which layer is **local**, which is **LLM-powered**, and which protocol carries each.
3. For each layer, write the one threat it's there to stop.
4. Argue: why is sanitize **before** the Judge, and masking on the **output** side?

**Done when:** Your diagram shows all three layers with the right protocol on each hop, and you
can defend the ordering (cheap-before-expensive on input; PII can only leak on output).

**Stretch (optional):** The Judge returns the message unmodified or `"BLOCKED"`. What failure
mode appears if the A2A Judge server is down — and how does `_check_a2a_servers()` handle it?
