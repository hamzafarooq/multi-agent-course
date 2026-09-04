# Reference — Multi-Agent Patterns

<!-- INSTRUCTOR: Deep-dive Claude pulls from when a learner wants more than the lesson.
     Sources: 2_agents_v_subagents, 5_sprint_zero. -->

## The orchestrator + subagents pattern

    Orchestrator
    ├── Subagent A → Task A → Result A
    ├── Subagent B → Task B → Result B  (parallel with A)
    └── Subagent C → Task C → Result C  (parallel with A and B)
            ↓  orchestrator receives all results → synthesizes final output

The orchestrator coordinates; the subagents execute. Each subagent has its own isolated
context, task, and tools, and returns a structured result.

## Sequential vs. parallel

- **Sequential** when each step depends on the previous one's output (a spec pipeline:
  scope → PRD → decisions → user stories → API contract).
- **Parallel** when steps are independent and share a spec (backend + frontend builders both
  working from the API contract).
- **Wall-clock for parallel work = the slowest branch, not the sum.** That's the efficiency unlock.

## Specialization patterns

- **By function:** researcher → analyst → writer.
- **By layer:** backend-agent (API + DB) ‖ frontend-agent (UI + state) → qa-agent (validation).
- **By dimension** (for reviews): security-reviewer ‖ performance-reviewer ‖ correctness-reviewer,
  each looking only at its slice; findings merged by the orchestrator.

**Good division** gives each agent a clear domain, inputs, and outputs so they never talk
mid-task. **Bad division** splits by volume ("agent 1 does the first half"). The shared spec
is the coordination layer.

## Failure modes and fixes

| Failure mode | What happens | Design fix |
|---|---|---|
| Context leakage | Subagent inherits noise from what it was handed | Explicit, minimal task briefs; don't pass the whole conversation |
| Coordination gaps | Parallel agents produce contradicting outputs | Define a shared spec *before* parallel execution |
| Cascading failures | A fails; B, C depend on A; pipeline stalls | Stage so failures isolate; report failures, don't crash |
| Prompt drift | Vague subagent prompt → vague result | Write prompts like acceptance criteria — specific, testable, scoped |

## Where the pattern generalizes

Once you see it, the orchestrator pattern is everywhere: competitive analysis (one agent per
competitor, synthesized), content pipelines (research → outline → write → SEO), multi-dimension
code review, customer research (one agent per transcript). You stop prompting and start
architecting.

## Defining a subagent (Claude Code)

Subagents live as markdown files in `.claude/agents/`. The file *is* the system prompt. A
good definition includes the role, a **What you build / do** section, a **What you do NOT do**
section (constraints matter as much as the job), and a structured **Output** section. At spawn,
the agent receives this prompt plus the task content; everything else is isolated.
