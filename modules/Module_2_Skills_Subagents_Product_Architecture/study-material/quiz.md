# Module 02 — Quiz

<!-- INSTRUCTOR: The quiz-me skill uses these. Answers are here so Claude can check,
     but the rule is Claude NEVER shows them before the learner attempts. Hint first. -->

## Q1. What is the single biggest reason a subagent beats stuffing everything into one long prompt?
- Type: explain-why
- **Answer:** Isolated context. The subagent's raw work (file reads, ticket text, tool output)
  lives in *its* window and only a summary returns to the orchestrator, so the main context
  stays clean. A long prompt mixes every concern together in one window.
- **Hint:** It's not about prompt length — it's about where the *noise* lives.

## Q2. In the orchestrator pattern, what is the orchestrator's actual job?
- Type: recall
- **Answer:** Coordination, not execution — decide what needs doing, who does it, and how the
  results fit together. The subagents do the actual work.
- **Hint:** It's the manager, not the worker.

## Q3. Sprint Zero writes its spec docs one after another but builds backend and frontend at the same time. Why the difference?
- Type: application
- **Answer:** The spec docs are sequential because each depends on the previous one (scope →
  PRD → decisions → stories → API contract). The builders are parallel because they're
  independent — both work from the finished API contract, so neither waits. Wall-clock = the
  slower builder, not the sum.
- **Hint:** Ask which steps *need* the previous step's output and which just need the contract.

## Q4. Two parallel agents return responses with mismatched payload shapes. Name the failure mode and the fix.
- Type: application
- **Answer:** Coordination gap. Fix: define a shared spec (the API contract) *before* parallel
  execution starts, so both agents build to the same interface.
- **Hint:** It's one of the four failure modes; the fix is the same thing that lets parallel
  agents avoid talking to each other.

## Q5. Where do you define a subagent in Claude Code, and what does that file become?
- Type: recall
- **Answer:** A markdown file in `.claude/agents/`. The file *is* the agent's system prompt —
  its identity, job, and constraints. At spawn time it gets that prompt plus the task content;
  everything else is isolated.
- **Hint:** It's a folder under `.claude/`, and the file isn't config — it's the prompt itself.
