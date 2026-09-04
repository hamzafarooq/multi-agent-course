# Module 02 — Exercises

<!-- INSTRUCTOR: Hands-on tasks for the build-along skill. Goal first, then steps,
     then a "done when" check. Exercise 2 produces a real .claude/agents/ file. -->

## Exercise 1 — Design the agent team

**Goal:** Take a real multi-step job and decompose it into an orchestrator + subagents,
deciding what runs sequentially vs. in parallel.

**Steps:**
1. Pick a task with ≥3 distinct parts (e.g. "review a PR", "research 4 competitors", "turn
   raw interview notes into a report").
2. List the subagents you'd spawn. Give each a one-line domain, its inputs, and its output.
3. Mark which run **sequentially** (each needs the previous one's output) and which run in
   **parallel** (independent).
4. Name the **shared spec** that lets the parallel agents stay consistent without talking.

**Done when:** You have an orchestrator diagram where every agent has clear inputs/outputs and
you can justify each sequential vs. parallel call.

**Stretch (optional):** Identify one failure mode (Concept 6) your design is exposed to, and
the change that removes it.

## Exercise 2 — Write a real subagent

**Goal:** Author a working subagent definition in `.claude/agents/` and reason about its
constraints.

**Steps:**
1. Pick one agent from Exercise 1 (e.g. a `security-reviewer`).
2. Create `.claude/agents/<name>.md` with: a role line, a **What you build/do** section, a
   **What you do NOT do** section, and an **Output** section (structured result).
3. Write the prompt like acceptance criteria — specific, testable, scoped. No vague verbs.
4. Spawn it on a small real task and read the result.

**Done when:** The agent returns a structured result that stays inside its stated scope, and
you can point to the line in the prompt that kept it from drifting.

**Stretch (optional):** Run two specialized review agents (e.g. security + performance) over
the same diff and have a third "orchestrator" turn pass synthesize their findings.
