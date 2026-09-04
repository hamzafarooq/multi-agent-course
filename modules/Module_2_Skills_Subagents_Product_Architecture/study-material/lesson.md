# Module 02 — Skills, Subagents & Multi-Agent Orchestration

<!-- INSTRUCTOR: This is the teaching content Claude walks the learner through.
     Each ## is roughly one "concept" Claude presents, then checks understanding on.
     Source decks: 1_claude_code_ecosystem, 2_agents_v_subagents,
     3_Three_layer_architecture, 4_infra_tools, 5_sprint_zero. Keep chunks short. -->

## Learning objectives

By the end of this module the learner can:
- [ ] Define an agent precisely (session + system prompt + task + the ability to *act*)
- [ ] Explain what a subagent is and why **isolated context windows** are the whole point
- [ ] Describe the orchestrator + subagents pattern, and when work runs sequential vs. parallel
- [ ] Define a subagent in Claude Code (a markdown file in `.claude/agents/`)
- [ ] Divide work by specialization (good division vs. bad), using a spec as the coordination layer
- [ ] Name the multi-agent failure modes and the design move that prevents each
- [ ] Trace Sprint Zero as a concrete multi-agent system end to end

## Prerequisites
- Module 1 (the agent loop, ReAct, the harness). You've used Skills and invoked one with a slash command.

---

## Concept 1 — From one agent to many

[Recap then sharpen. In Module 1 you ran *one* agent in a loop. A Skill gives that one
agent a reusable workflow you invoke with a slash command — still one agent, one thing, in
sequence. Now be precise about what an agent *is*: a Claude session with (1) a system prompt
that defines its role, constraints, and tools, (2) a task, and (3) the ability to take
actions — read files, write code, call APIs, *spawn other agents*. The key word is actions:
a chatbot responds, an agent acts (perceive → reason → act → observe). Module 2 is what
happens when one agent isn't enough — going from "Claude doing one thing well" to "Claude
running a coordinated system that does many things at once." That jump is architectural, not
incremental.]

**Check:** What three things make a Claude session an "agent" rather than a chatbot?

## Concept 2 — Subagents and why isolated context windows matter

[A **subagent** is an agent spawned by another agent to handle a specific piece of work. The
spawner is the **orchestrator**; the ones it spawns are subagents. Each subagent gets its own
isolated context window, its own task, and its own tools, and returns a *result* when done.
Here's the detail most people miss: every session has a finite context window. Spawn a
subagent to analyze 50 support tickets and all that raw content lives in *its* window — your
main session only receives the summary. Your context stays clean; the subagent absorbs the
noise. This is also why a subagent beats one very long prompt: the problem with a long prompt
isn't length, it's that everything is mixed together. Subagents keep concerns separated by
design.]

**Check:** You ask a subagent to read 50 tickets. What does your main session get back — the
tickets, or something else? Why does that keep your context clean?

## Concept 3 — The orchestrator pattern

[The most common multi-agent shape: one orchestrator, several subagents.

    Orchestrator
    ├── Subagent A → Task A → Result A
    ├── Subagent B → Task B → Result B  (parallel with A)
    └── Subagent C → Task C → Result C  (parallel with A and B)
            ↓  orchestrator receives all results → synthesizes final output

The orchestrator's job is *coordination, not execution* — it decides what's done, who does
it, and how results fit. Some work must run **sequentially** (each step depends on the last);
some can run in **parallel** (independent work). Concrete: Sprint Zero writes its spec docs
sequentially (scope → PRD → decisions → stories → API contract — each builds on the last),
then builds backend and frontend in parallel from the shared contract. Key idea: parallel
wall-clock time = the *slower of the two*, not the sum. That's the efficiency unlock.]

**Check:** Why must the spec docs run sequentially but the two builders can run in parallel?

## Concept 4 — Defining a subagent in Claude Code

[Subagents in Claude Code are markdown files in `.claude/agents/`. Each file *is* the system
prompt for that agent — its identity, its job, its constraints. A basic one:

    # backend-engineer
    You are a senior backend engineer. Implement the API endpoints defined in the
    API contract you've been given.
    ## What you build
    - Express/Node.js server, Supabase for DB and auth, one endpoint per spec
    ## What you do NOT do
    - Build any frontend; make decisions not in the spec; add tables not in the data model
    ## Output
    - Return the full directory structure with all files created.

When the orchestrator spawns this agent it gets this system prompt *plus* the task content
(the API contract). Everything else is isolated. Note the "What you do NOT do" section —
constraints matter as much as the job description.]

**Check:** Where do subagent definitions live, and what does that markdown file actually
*become* when the agent runs?

## Concept 5 — Specialization is a design decision

[The most important thing you control in a multi-agent system is *how you divide the work*.
**Bad division:** "Agent 1 does the first half, Agent 2 the second" — splitting by volume.
**Good division:** each agent has a clear domain, clear inputs, clear outputs, so they never
need to talk mid-task — the shared spec is the coordination layer. Patterns: by **function**
(researcher → analyst → writer), by **layer** (backend / frontend / qa), by **dimension** for
reviews (security / performance / correctness, each looking only at its slice). Each agent
does one thing well and returns a structured result; the orchestrator combines them.]

**Check:** Why is "split the work in half by volume" a worse division than "give each agent a
domain"? What carries the coordination if the agents never talk?

## Concept 6 — What can go wrong (and how to design around it)

[Multi-agent systems add failure modes single sessions don't have. Each has a design fix:
- **Context leakage** — a subagent inherits noise from whatever it was handed. *Fix:* give
  explicit, minimal task briefs; don't pass the whole conversation.
- **Coordination gaps** — two parallel agents produce contradicting outputs. *Fix:* define a
  shared spec (e.g. the API contract) *before* parallel execution starts.
- **Cascading failures** — A fails and B, C depend on A, so the pipeline stalls. *Fix:* stage
  it so failures isolate — QA runs after builds; a failed build gets *reported*, not crashed on.
- **Prompt drift** — a vague subagent prompt produces vague results, because that prompt is its
  entire understanding of the job. *Fix:* write subagent prompts like acceptance criteria —
  specific, testable, scoped.]

**Check:** Two parallel agents disagree on the shape of a response payload. Which failure mode
is that, and what design move would have prevented it?

## Concept 7 — Sprint Zero: the pattern in practice

[Sprint Zero is the module's capstone — a multi-agent system on Claude Code. You give it a
product URL and answer three scoping questions; it returns six spec documents and a working
full-stack app in minutes. The pipeline *is* the orchestrator pattern:

    Orchestrator
        ↓  Spec writers (SEQUENTIAL — each doc depends on the last)
           scope → reference brief + PRD → decisions → user stories → API contract
        ↓  Parallel builders (INDEPENDENT — both work from the contract)
           backend agent  ‖  frontend agent
        ↓  QA validator (requires both builds done) → structured validation report

Why it must be multi-agent and not one big prompt: context is finite (6 docs + a build blow
through one window), parallelism is structural (one agent can't build both layers at once),
specialization makes better decisions, and failure stays isolated. The same shape generalizes:
competitive analysis (one agent per competitor), content pipelines, multi-dimension code
review, customer research (one agent per transcript).]

**Check:** In Sprint Zero, what single artifact lets the backend and frontend agents work in
parallel without ever talking to each other?

---

## Summary
1. A subagent is an agent spawned by an orchestrator with its **own isolated context** — that
   isolation, not raw horsepower, is why multi-agent beats one long prompt.
2. The orchestrator pattern coordinates specialized agents; sequential where work depends,
   parallel where it doesn't (wall-clock = the slower branch). A shared spec is the glue.
3. Sprint Zero is this pattern made real: sequential spec writers → parallel builders → QA.

## Where to next
- Do `exercises.md` (design an agent team, then write a real subagent), or ask to be quizzed
  (`quiz.md`). To see it run, work through the **Sprint Zero** project in the course materials.
