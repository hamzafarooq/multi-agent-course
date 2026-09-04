// Coordinates are within the 720×440 fixed canvas — see SimulationView.tsx.
// NODE_W = 170, NODE_H = 78

export type AgentStatus = 'idle' | 'thinking' | 'done';

export interface AgentDef {
  id: string;
  name: string;
  role: 'human' | 'single' | 'main' | 'sub' | 'orch' | 'merge';
  x: number;
  y: number;
  sublabel?: string;
  brief: string;
  detail?: string;
}

export interface Connection {
  from: string;
  to: string;
}

export interface SimStep {
  agentId: string;
  status: 'thinking' | 'done';
  output?: string;
  delay: number;
}

export interface LevelDef {
  id: number;
  name: string;
  tagline: string;
  description: string;
  analogy: string;
  explanation: string;
  code: string;
  agents: AgentDef[];
  connections: Connection[];
  steps: SimStep[];
}

export const LEVELS: LevelDef[] = [
  /* ──────────────────────────── LEVEL 1 ──────────────────────────── */
  {
    id: 1,
    name: 'Single Skill',
    tagline: 'A skill is a reusable prompt',
    description:
      'A skill is a reusable prompt — a named, repeatable instruction you save once and invoke by name. One developer handles the entire website: design, frontend, backend, and deployment. One prompt, one answer.',
    analogy: 'Like hiring one developer and asking them to be the designer, frontend engineer, backend engineer, and QA — all at once.',
    explanation:
      'A skill is nothing more than a reusable prompt. No tools, no memory, no file access, no web search. Everything the model knows has to come from its training or from what you put in the prompt. That is the constraint. It is also why skills are fast, cheap, and predictable — there is nothing else to go wrong.',
    code: `# A skill is just a .md file — a saved, reusable prompt.
#
# skills/full-stack-developer.md
# ───────────────────────────────
# You are a full-stack web developer. Given
# a project brief, produce a complete plan:
# tech stack, file structure, and key code.

import anthropic

client = anthropic.Anthropic()

# In code: load the .md file as the system prompt
with open("skills/full-stack-developer.md") as f:
    skill_prompt = f.read()

response = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system=skill_prompt,
    messages=[{
        "role": "user",
        "content": "Build a full-stack task manager app "
                   "with React frontend and FastAPI backend."
    }]
)

result = response.content[0].text`,
    agents: [
      {
        id: 'fullstack',
        name: 'Full-Stack Dev',
        role: 'single',
        x: 275,
        y: 181,
        brief:
          'Gets one project brief and handles everything alone — design decisions, frontend, backend, and deployment plan. No helpers, no hand-offs. Fast, but the scope is wide.',
        detail: `## This is a Skill

A skill is a reusable prompt — nothing more. In practice it is a \`.md\` file with a system prompt and a task. That is the entire definition.

\`\`\`
skills/full-stack-developer.md
───────────────────────────────
You are a full-stack web developer. Given a
project brief, produce a complete plan.
\`\`\`

### Skills have no tools
A skill cannot search the web, read a file, run code, or remember anything from a previous session. Everything has to come from the model's training or from what you put in the prompt.

Use a skill when the task is bounded and the model already knows enough to answer it.`,
      },
    ],
    connections: [],
    steps: [
      { agentId: 'fullstack', status: 'thinking', delay: 300 },
      {
        agentId: 'fullstack',
        status: 'done',
        delay: 2400,
        output:
          'Full-stack task manager plan\n' +
          '─────────────────────────────\n' +
          'Stack\n' +
          '  Frontend  React 18 + TypeScript\n' +
          '  Backend   FastAPI + PostgreSQL\n' +
          '  Hosting   Vercel (FE) + Fly.io (BE)\n' +
          '\n' +
          'File structure (excerpt)\n' +
          '  /frontend\n' +
          '    TaskList.tsx  TaskCard.tsx  api.ts\n' +
          '  /backend\n' +
          '    main.py  models/task.py  routes/\n' +
          '\n' +
          'Steps\n' +
          '  1  Scaffold monorepo\n' +
          '  2  FastAPI + SQLModel setup\n' +
          '  3  CRUD endpoints\n' +
          '  4  React components\n' +
          '  5  Wire frontend to API\n' +
          '  6  Deploy',
      },
    ],
  },

  /* ──────────────────────────── LEVEL 2 ──────────────────────────── */
  {
    id: 2,
    name: 'Sub-Agent',
    tagline: 'Skill vs Sub-Agent — side by side',
    description:
      'You hand a goal to the Planner Agent. It decides how to split the work: formatting goes to the Formatter Skill (just a prompt, no tools), research goes to the Research Agent (has tools, isolated context). The Planner sees only the results — never the work in progress.',
    analogy:
      'Like a project manager who knows which tasks need a template and which need someone to go research first. They hand off both, wait, and assemble the result.',
    explanation:
      'The Skill and the Sub-Agent look similar — both receive a task and return a result. The difference is capability. The Skill has no tools; it only knows what the model was trained on. The Sub-Agent can use tools: web search, file access, code execution. That is why the Planner routes research to the Sub-Agent and formatting to the Skill.',
    code: `import anthropic

client = anthropic.Anthropic()

# Sub-agent: research runs in its own isolated context window
# It can use tools — the Planner never sees its reasoning, only the result
research_resp = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=512,
    system="You are a tech researcher with web search access.",
    messages=[{
        "role": "user",
        "content": "Best stack for a task manager app in 2025?"
    }]
)
stack_research = research_resp.content[0].text

# Skill: just a reusable prompt — no tools, no isolated context
# In practice this is a .md file loaded as the system prompt
format_resp = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=256,
    system="You are a sprint formatter. Convert any plan into "
           "a clean sprint card structure.",
    messages=[{
        "role": "user",
        "content": "Format spec: 2 sprints, 5 days each, "
                   "with owner and status fields."
    }]
)
format_spec = format_resp.content[0].text

# Main agent: sees only the two results — not the reasoning behind them
plan_resp = client.messages.create(
    model="claude-opus-4-5",
    max_tokens=1024,
    system="You are a project planner.",
    messages=[{
        "role": "user",
        "content": f"Build a task manager sprint plan.\\n"
                   f"Stack research:\\n{stack_research}\\n"
                   f"Format spec:\\n{format_spec}"
    }]
)`,
    agents: [
      {
        id: 'human',
        name: 'You',
        role: 'human',
        x: 275,
        y: 25,
        sublabel: 'human',
        brief: 'Starts the process with a plain-English goal. No technical knowledge required.',
        detail: `## Human

You type a goal. That is the entire input. The Planner Agent handles everything from here — deciding what needs research, what needs formatting, and how to assemble the result.

### What you provide
- A plain-English goal
- Nothing else

### What you get back
- A finished sprint plan grounded in current stack research and formatted cleanly`,
      },
      {
        id: 'planner',
        name: 'Planner Agent',
        role: 'main',
        x: 275,
        y: 181,
        brief:
          'Receives your goal and decides how to split the work. Routes formatting to the Skill (fast, no tools) and research to the Sub-Agent (has tools). Assembles both results into the final plan.',
        detail: `## Main Agent

The Planner Agent receives your goal and makes two routing decisions:
1. Send the format spec task to the Formatter Skill — it is templated and the model already knows how to do it
2. Send the research task to the Research Agent — it needs to look things up, so it needs tools

### The Planner does not do this work itself
It delegates, waits for both results, then synthesises. It never sees the reasoning inside either call — only what comes back.

### Not an orchestrator yet
An orchestrator (Level 3) delegates everything and does no work itself. The Planner here still assembles the final output — it is a main agent, not a pure router.`,
      },
      {
        id: 'skill',
        name: 'Formatter',
        role: 'single',
        x: 80,
        y: 330,
        sublabel: 'skill · no tools',
        brief:
          'A reusable prompt. Converts a raw plan into a clean sprint format. Fast — no tools needed, the model already knows how to format.',
        detail: `## Skill

A skill is a saved, reusable prompt — nothing more. No tools, no memory, no file access.

\`\`\`
skills/sprint-formatter.md
───────────────────────────
You are a sprint formatter. Convert any plan
into a clean sprint card structure with owner,
status, and dependency fields.
\`\`\`

### Why use a skill here?
Formatting is a templated task. The model already knows how to structure sprint cards — there is nothing to look up, no file to read. A skill is faster and cheaper than a full agent call.

### The constraint
If the task ever requires current information (e.g. "what format does Linear use today?"), a skill cannot answer it. That is when you reach for a sub-agent with tools.`,
      },
      {
        id: 'research',
        name: 'Research Agent',
        role: 'sub',
        x: 470,
        y: 330,
        sublabel: 'agent · has tools',
        brief:
          'Searches the web for current stack options. Returns grounded recommendations the Planner uses to build the plan. Runs in its own isolated context — the Planner only sees the result.',
        detail: `## Sub-Agent

The Research Agent runs in complete isolation — its own system prompt, its own context window. The Planner never sees its tool calls or reasoning. It only receives the final recommendations.

### What tools unlock
\`\`\`
name: research-agent
tools:
  - WebSearch   ← look up current stack trends
  - Read        ← read existing project files
  - Write       ← save findings to disk
\`\`\`

A skill can only use what the model was trained on. A sub-agent with tools can go and get what it needs right now — current library versions, recent benchmarks, live documentation.

### Isolation is the point
The Planner gets one clean result. It never sees the search queries, intermediate findings, or dead ends. That boundary keeps the main agent's context clean.`,
      },
    ],
    connections: [
      { from: 'human', to: 'planner' },
      { from: 'planner', to: 'skill' },
      { from: 'planner', to: 'research' },
      { from: 'skill', to: 'planner' },
      { from: 'research', to: 'planner' },
    ],
    steps: [
      { agentId: 'human', status: 'thinking', delay: 300 },
      {
        agentId: 'human',
        status: 'done',
        delay: 700,
        output: 'Build me a task manager app.\nModern stack, full sprint plan.',
      },
      { agentId: 'planner', status: 'thinking', delay: 500 },
      { agentId: 'skill', status: 'thinking', delay: 900 },
      { agentId: 'research', status: 'thinking', delay: 100 },
      {
        agentId: 'skill',
        status: 'done',
        delay: 1200,
        output:
          'Sprint format spec\n' +
          '──────────────────\n' +
          'Sections   Goal · Stack · Sprint 1 · Sprint 2\n' +
          'Cards      Title · owner · days · deps\n' +
          'Status     Todo / In Progress / Done\n' +
          'Notes      Inline, max 1 line per card',
      },
      {
        agentId: 'research',
        status: 'done',
        delay: 1400,
        output:
          'Stack research (web)\n' +
          '────────────────────\n' +
          'Frontend  React 18 — dominant, Vite for speed\n' +
          'Backend   FastAPI rising, Express still default\n' +
          'DB        PostgreSQL + Prisma ORM popular pairing\n' +
          'Host      Vercel (FE) · Railway (BE) — lowest friction\n' +
          'Auth      Clerk gaining vs NextAuth\n' +
          'Trend     tRPC + React Query replacing REST+Axios',
      },
      {
        agentId: 'planner',
        status: 'done',
        delay: 900,
        output:
          'Task manager — sprint plan\n' +
          '──────────────────────────\n' +
          'Stack   React 18 · FastAPI · PostgreSQL · Prisma\n' +
          'Host    Vercel (FE) · Railway (BE)\n' +
          '──────────────────────────────────────────────────\n' +
          'Sprint 1 — Core (5 days)\n' +
          '  D1  DB schema + Prisma migration\n' +
          '  D2  FastAPI CRUD routes\n' +
          '  D3  React board + TaskCard\n' +
          '  D4  Wire API with React Query\n' +
          '  D5  Drag-and-drop (dnd-kit)\n' +
          'Sprint 2 — Ship (4 days)\n' +
          '  D1  Auth (Clerk)\n' +
          '  D2  Priority badges + assignees\n' +
          '  D3  Deploy: Vercel + Railway\n' +
          '  D4  QA + polish',
      },
    ],
  },
  /* ──────────────────────────── LEVEL 3 ──────────────────────────── */
  {
    id: 3,
    name: 'Orchestrator',
    tagline: 'The agent decides the team',
    description:
      'The Project Lead reads the goal and decides who is needed — you do not hardcode that in your script. Same code, different goal → different specialists dispatched. The topology is dynamic.',
    analogy:
      'Like a project lead who reads the brief and figures out who to call. A landing page? Just designer + frontend. A full app? The whole team. The decision lives in the agent, not in your code.',
    explanation:
      'If you hardcoded asyncio.gather(designer, frontend, backend) in your script, the team is fixed forever — change the project, rewrite the code. Here, the Project Lead reads the goal and decides the team at runtime. Change the goal from "full app" to "landing page" and it dispatches only two specialists. You change the prompt, not the code. The topology is dynamic.',
    code: `# Level 3 — project lead plans, team executes, tech lead integrates.
import asyncio
import anthropic

aclient = anthropic.AsyncAnthropic()

async def run(system: str, prompt: str) -> str:
    r = await aclient.messages.create(
        model="claude-opus-4-5", max_tokens=512,
        system=system,
        messages=[{"role": "user", "content": prompt}]
    )
    return r.content[0].text

goal = "Build a full-stack task manager with React, FastAPI, and PostgreSQL."

# Step 1: Project lead scopes the work
brief = await run(
    "You are a project lead. Break the goal into "
    "specialist briefs for your team. Return JSON.",
    goal
)

# Step 2: All specialists work in parallel
design, frontend, backend, qa = await asyncio.gather(
    run("UI Designer",        f"Brief: {brief}"),
    run("Frontend Developer", f"Brief: {brief}"),
    run("Backend Developer",  f"Brief: {brief}"),
    run("QA Engineer",        f"Brief: {brief}"),
)

# Step 3: Tech lead integrates into the final build plan
final = await run(
    "Tech Lead",
    f"Integrate into one build plan:\\n"
    f"Design: {design}\\nFrontend: {frontend}\\n"
    f"Backend: {backend}\\nQA: {qa}"
)`,
    agents: [
      {
        id: 'orch',
        name: 'Project Lead',
        role: 'orch',
        x: 275,
        y: 30,
        sublabel: 'plan + dispatch',
        brief:
          'Reads the project goal and decides who handles what. Does not write any specs — its only job is to scope the work and send the team off.',
        detail: `## Orchestrator — dynamic topology

The difference from a hardcoded script: **you do not write the team into your code**.

If you wrote \`asyncio.gather(designer, frontend, backend)\`, that team is fixed forever. Here, the project lead reads the goal and **decides the team at runtime**:

\`\`\`python
# Same code for any goal
brief = await run(
    "You are a project lead. Decide which specialists "
    "are needed and write each one a brief. Return JSON.",
    goal   # ← this is the only thing that changes
)
\`\`\`

Full app → dispatches designer + frontend + backend + QA.
Landing page → maybe just designer + frontend.
API only → backend + QA, no designer.

**You change the goal. The agent changes the team.**

### Why this matters for scale
Adding a new capability (security review, accessibility audit) means adding a specialist skill file — not editing the orchestrator or any existing prompt. The topology grows without the code growing.`,
      },
      {
        id: 'designer',
        name: 'UI Designer',
        role: 'sub',
        x: 20,
        y: 200,
        brief:
          'Produces the design system: component structure, style guide, and interaction patterns. Dispatched by the project lead with a scoped brief.',
        detail: `## Specialist Sub-Agent

Dispatched by the project lead with a specific brief.

This agent does not know about the other three specialists running in parallel. Its context is clean: one role, one question, one output.

### Dispatched, not chained
In a chained workflow, each step runs after the previous finishes. Here, the project lead dispatches all four specialists at once — this one runs in parallel with the frontend dev, backend dev, and QA engineer.

### The brief determines the quality
The project lead's scoping brief is the most important input this agent receives. A vague brief produces a vague design. A tight brief produces something the tech lead can integrate directly.`,
      },
      {
        id: 'frontend',
        name: 'Frontend Dev',
        role: 'sub',
        x: 190,
        y: 200,
        brief:
          'Specs the React component tree, state management, and data-fetching strategy. Runs in parallel — no awareness of what the designer or backend dev are producing.',
        detail: `## Specialist Sub-Agent

Scopes the React component tree, state management, and data-fetching strategy. Returns a frontend spec the tech lead can use directly.

Runs in parallel with three other specialists. Its output goes directly to the tech lead — the project lead never sees its raw work.

### Scoped to one domain
The tighter the scope from the project lead's brief, the more useful this agent's output. A frontend spec that bleeds into backend design produces something neither specialist nor integrator can use cleanly.`,
      },
      {
        id: 'backend',
        name: 'Backend Dev',
        role: 'sub',
        x: 360,
        y: 200,
        brief:
          'Designs the data models, REST API endpoints, and database schema. Isolated from the frontend and design specs — they meet at the tech lead.',
        detail: `## Specialist Sub-Agent

Designs the data models, API endpoints, and DB schema. Returns a backend spec the tech lead can integrate with the frontend and design outputs.

Isolated context, narrow focus. The tech lead slots this spec into the build plan alongside the design system and frontend component tree.

### Each specialist sees only its brief
This agent does not see what the UI designer or frontend dev produced. That isolation is deliberate — it prevents anchoring and keeps each output independent. The tech lead is the only place where all specs meet.`,
      },
      {
        id: 'qa',
        name: 'QA Engineer',
        role: 'sub',
        x: 530,
        y: 200,
        brief:
          'Writes the test plan and acceptance criteria before a line of code exists. Works from the project brief alone.',
        detail: `## Specialist Sub-Agent

Writes the test plan and acceptance criteria in parallel with the other three specialists — before any code exists.

This is possible because the project lead's brief carries enough context. The QA engineer does not need to see the component tree or API design to define what "done" looks like.

### Skills-as-workers pattern
Each specialist here is a skill file with a focused role:
\`\`\`
skills/qa-engineer.md
──────────────────────
You are a QA engineer. Given a project brief,
produce a test plan: unit tests, integration
tests, E2E scenarios, and acceptance criteria.
\`\`\`

The orchestrator pattern works because every worker is interchangeable — a skill file you can swap, tune, or replace without touching anything else.`,
      },
      {
        id: 'synth',
        name: 'Tech Lead',
        role: 'merge',
        x: 275,
        y: 362,
        sublabel: 'integrate',
        brief:
          'The only agent that sees all four specialist outputs at once. Turns them into one coherent build plan — stack, sprints, testing strategy, deployment.',
        detail: `## Synthesiser

The final agent. Receives outputs from all four specialists and composes the finished build plan.

This is the only agent in the pipeline that sees everything at once. It is also the only one whose output the team actually ships from.

### Context discipline
The tech lead never sees raw reasoning — only distilled specs. Four full context windows of thinking get compressed into four tight outputs before they arrive here. That keeps the tech lead's context tight and its plan coherent.

### Still just a skill
\`\`\`
skills/tech-lead.md
────────────────────
You are a tech lead. Given specialist specs
from design, frontend, backend, and QA,
produce an integrated build plan with stack
decisions, sprint breakdown, and test strategy.
\`\`\`

The complexity is in the architecture — the pipeline that feeds this agent. The agent itself is a plain skill file.`,
      },
    ],
    connections: [
      { from: 'orch', to: 'designer' },
      { from: 'orch', to: 'frontend' },
      { from: 'orch', to: 'backend' },
      { from: 'orch', to: 'qa' },
      { from: 'designer', to: 'synth' },
      { from: 'frontend', to: 'synth' },
      { from: 'backend', to: 'synth' },
      { from: 'qa', to: 'synth' },
    ],
    steps: [
      { agentId: 'orch', status: 'thinking', delay: 300 },
      {
        agentId: 'orch',
        status: 'done',
        delay: 1600,
        output:
          'Team briefs\n' +
          '─────────────\n' +
          '1. Designer  · Kanban UI · style guide · drag-drop\n' +
          '2. Frontend  · React component tree · state mgmt\n' +
          '3. Backend   · REST API · data models · DB schema\n' +
          '4. QA        · test plan · acceptance criteria\n' +
          'Dispatching all four in parallel.',
      },
      { agentId: 'designer', status: 'thinking', delay: 700 },
      { agentId: 'frontend', status: 'thinking', delay: 0 },
      { agentId: 'backend', status: 'thinking', delay: 0 },
      { agentId: 'qa', status: 'thinking', delay: 0 },
      {
        agentId: 'designer',
        status: 'done',
        delay: 2000,
        output:
          'Design system\n' +
          '───────────────\n' +
          'Board   3-col Kanban · drag placeholder\n' +
          'Card    title · assignee avatar · priority badge\n' +
          'Colors  #1a1a1a · #f5f5f0 · terracotta accent\n' +
          'Motion  200ms ease · 0.85 drag ghost opacity',
      },
      {
        agentId: 'frontend',
        status: 'done',
        delay: 600,
        output:
          'Frontend spec\n' +
          '───────────────\n' +
          '<Board> <Column> <TaskCard> <TaskModal>\n' +
          'State   Zustand · React Query\n' +
          'Router  Next.js App Router\n' +
          'DnD     dnd-kit for drag-to-reorder',
      },
      {
        agentId: 'backend',
        status: 'done',
        delay: 700,
        output:
          'API + data model\n' +
          '──────────────────\n' +
          'Task    id · title · status · priority\n' +
          '        assignee_id · due_date\n' +
          'Routes  CRUD /tasks · PATCH /:id/status\n' +
          'Auth    JWT · POST /auth/login\n' +
          'DB      PostgreSQL + SQLModel',
      },
      {
        agentId: 'qa',
        status: 'done',
        delay: 900,
        output:
          'Test plan\n' +
          '───────────\n' +
          'Unit   TaskCard renders priority badge\n' +
          '       PATCH /tasks/:id returns updated task\n' +
          'E2E    Create → drag to Done → verify DB\n' +
          'Perf   Drag operations < 100ms\n' +
          'Done   all columns render · auth flow works',
      },
      { agentId: 'synth', status: 'thinking', delay: 800 },
      {
        agentId: 'synth',
        status: 'done',
        delay: 2800,
        output:
          'Full-stack build plan — final\n' +
          '═══════════════════════════════════════════\n' +
          'Stack    Next.js · FastAPI · PostgreSQL\n' +
          'Design   Kanban · Inter · dnd-kit drag-drop\n' +
          'Auth     NextAuth + JWT\n' +
          '\n' +
          'Sprint 1  Foundation\n' +
          '  D1  Monorepo setup + DB schema + migrations\n' +
          '  D2  FastAPI CRUD endpoints + auth\n' +
          '  D3  <Board> <Column> <TaskCard>\n' +
          '  D4  React Query ↔ API integration\n' +
          'Sprint 2  UX + Quality\n' +
          '  D1  Drag-to-reorder + optimistic updates\n' +
          '  D2  TaskModal + priority badges\n' +
          '  D3  Unit + E2E tests (pytest + Playwright)\n' +
          'Sprint 3  Ship\n' +
          '  D1  Vercel (FE) + Fly.io (BE) deploy\n' +
          '  D2  CI/CD GitHub Actions\n' +
          '  D3  Error tracking + monitoring',
      },
    ],
  },

  /* ──────────────────────────── LEVEL 4 ──────────────────────────── */
  {
    id: 4,
    name: 'Production Agent',
    tagline: 'Agentic loop · hooks · MCP tools',
    description:
      'This is what a real agent looks like in production. Every outgoing tool call passes through a PreToolUse hook (intercept before execution) and every result passes through a PostToolUse hook (normalise before the model sees it). The loop runs until stop_reason is "end_turn" — the model decides when it is done.',
    analogy:
      'Like a support rep whose actions pass through two checkpoints: one before they act (is this allowed?) and one after the system responds (is this data clean?). The loop keeps running until the case is resolved.',
    explanation:
      'Four things separate a production agent from a demo: (1) the loop is driven by stop_reason, not a fixed counter; (2) a PreToolUse hook intercepts every outgoing call — it can block, redirect, or log before execution; (3) a PostToolUse hook normalises every result before the model processes it — format cleanup, policy enforcement, data enrichment; (4) programmatic gates in code (not prompts) enforce tool ordering for safety-critical sequences.',
    code: `import anthropic

client = anthropic.Anthropic()
verified_customer_id: str | None = None

# ── PreToolUse hook — fires BEFORE a tool executes ────────────
def pre_tool_use(tool_name: str, tool_input: dict) -> dict | None:
    """Return None to allow. Return a result dict to block and short-circuit."""

    # Gate: block order/refund ops until identity is verified
    if tool_name in ("lookup_order", "process_refund"):
        if not verified_customer_id:
            return {                          # ← blocked, tool never runs
                "isError": True,
                "errorCategory": "validation",
                "isRetryable": False,
                "content": "Call get_customer first"
            }

    # Rate-limit: block refunds above $500 before the tool even executes
    if tool_name == "process_refund":
        if tool_input.get("amount", 0) > 500:
            return {                          # ← blocked, escalate instead
                "isError": True,
                "errorCategory": "permission",
                "content": "Exceeds $500 limit — use escalate_to_human"
            }

    return None  # allowed — proceed to tool execution

# ── PostToolUse hook — fires AFTER a tool returns ────────────
def post_tool_use(tool_name: str, result: dict) -> dict:
    """Normalise and enrich the result before the model sees it."""

    # Normalise Unix timestamps → ISO 8601
    for key in ("created_at", "last_login", "updated_at"):
        if key in result and isinstance(result[key], int):
            result[key] = to_iso8601(result[key])

    return result

# ── Tool execution with both hooks ────────────────────────────
def run_tool(name: str, inputs: dict) -> tuple[dict, bool]:
    global verified_customer_id

    blocked = pre_tool_use(name, inputs)   # PreToolUse fires first
    if blocked:
        return blocked, True               # short-circuited

    raw = execute_tool(name, inputs)       # tool actually runs

    if name == "get_customer" and not raw.get("isError"):
        verified_customer_id = raw["customer_id"]

    return post_tool_use(name, raw), raw.get("isError", False)

# ── The agentic loop ──────────────────────────────────────────
messages = [{"role": "user", "content": "Refund order #4421 — $89.99"}]

while True:
    response = client.messages.create(
        model="claude-opus-4-7",
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        tools=TOOLS,
        messages=messages,
    )

    if response.stop_reason == "end_turn":   # model decided it is done
        print(response.content[0].text)
        break

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result, is_error = run_tool(block.name, block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    **({"is_error": True} if is_error else {})
                })
        messages.append({"role": "user", "content": tool_results})`,
    agents: [
      // Row 1 — customer
      {
        id: 'customer',
        name: 'Customer',
        role: 'human',
        x: 275,
        y: 5,
        sublabel: 'human',
        brief: 'Sends a plain-language support request. The agent handles everything — verification, lookup, refund, or escalation.',
        detail: `## Customer

The only input to the system: a natural-language message. The agent does not know in advance whether this will take 1 tool call or 4.

### What the customer never sees
- The PreToolUse hook checking each call before execution
- The PostToolUse hook normalising every result
- The programmatic gate blocking order ops until identity is verified

They see one thing: a resolved case or a human on the line.`,
      },

      // Row 2 — agent alone (center)
      {
        id: 'pre_hook',
        name: 'PreToolUse',
        role: 'merge',
        x: 80,
        y: 202,
        sublabel: 'hook · fires before tool',
        brief:
          'Fires before every tool executes. Can block the call entirely (returns a result without running the tool), redirect it, or log it. This is where programmatic gates and policy enforcement live.',
        detail: `## PreToolUse Hook

Fires before a tool executes — the tool may never run at all.

\`\`\`python
def pre_tool_use(tool_name: str, inputs: dict) -> dict | None:
    # Return None  → allow (tool runs normally)
    # Return dict  → block (tool is skipped, dict is the result)

    if tool_name in ("lookup_order", "process_refund"):
        if not verified_customer_id:
            return {"isError": True,
                    "content": "Call get_customer first"}

    if tool_name == "process_refund":
        if inputs.get("amount", 0) > 500:
            return {"isError": True,
                    "content": "Exceeds $500 — use escalate_to_human"}

    return None  # allowed
\`\`\`

### PreToolUse vs prompt instructions
A prompt saying "always verify identity first" fails in ~12% of production cases. The PreToolUse hook makes the gate deterministic — the tool physically cannot run until the condition is met.

### Other uses
- Rate limiting: count calls per session, block if over threshold
- Audit logging: record every outgoing call with its inputs
- Input sanitisation: strip PII from tool arguments before they leave your system`,
      },
      {
        id: 'agent',
        name: 'Support Agent',
        role: 'orch',
        x: 275,
        y: 98,
        sublabel: 'loop · stop_reason',
        brief:
          'Runs the agentic loop. Sends tool calls through the PreToolUse hook, receives normalised results back from the PostToolUse hook. Stops when stop_reason is "end_turn" — never on a fixed counter.',
        detail: `## The Agentic Loop

\`\`\`python
while True:
    response = client.messages.create(
        model="claude-opus-4-7",
        tools=TOOLS,
        messages=messages,
    )

    if response.stop_reason == "end_turn":
        break                    # model decided it is done

    if response.stop_reason == "tool_use":
        messages.append({"role": "assistant",
                          "content": response.content})
        tool_results = []
        for block in response.content:
            if block.type == "tool_use":
                result, is_error = run_tool(block.name,
                                            block.input)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": str(result),
                    **({"is_error": True} if is_error else {})
                })
        messages.append({"role": "user",
                          "content": tool_results})
\`\`\`

### Why stop_reason beats a counter
A fixed \`for _ in range(5)\` caps the loop arbitrarily. A simple case closes in 2 iterations; a complex one may need 6. Using \`"end_turn"\` means the model decides when the work is complete — not your config.

### What the agent sees between iterations
Every tool result (already normalised by PostToolUse) is appended to conversation history. The next decision is informed by everything that happened so far.`,
      },
      {
        id: 'post_hook',
        name: 'PostToolUse',
        role: 'merge',
        x: 470,
        y: 202,
        sublabel: 'hook · fires after tool',
        brief:
          'Fires after a tool returns, before the model sees the result. Normalises formats (Unix → ISO 8601), enriches data (account tier, policy flags), and logs every result for observability.',
        detail: `## PostToolUse Hook

Fires after a tool returns but before the model processes the result.

\`\`\`python
def post_tool_use(tool_name: str, result: dict) -> dict:
    # Normalise Unix timestamps → ISO 8601
    for key in ("created_at", "last_login", "updated_at"):
        if key in result and isinstance(result[key], int):
            result[key] = to_iso8601(result[key])

    # Trim verbose fields the model does not need
    if tool_name == "lookup_order":
        result = {k: result[k] for k in
                  ("order_id","status","amount","date")
                  if k in result}

    return result
\`\`\`

### PostToolUse vs prompt instructions
Prompt: "always convert timestamps to ISO 8601" — probabilistic.
Hook: converts every timestamp, every time, deterministically.

### Three jobs for PostToolUse
1. **Normalise**: consistent formats so the model never sees raw Unix timestamps, numeric status codes, or locale-specific currency
2. **Trim**: strip 40-field order responses down to 5 relevant fields before they fill up the context window
3. **Enrich**: add data the tool did not return — account tier, policy flags, cached metadata`,
      },

      // Row 3 — MCP tools (even spacing: 5, 185, 365, 545)
      {
        id: 'get_customer',
        name: 'get_customer',
        role: 'sub',
        x: 5,
        y: 322,
        sublabel: 'MCP tool · step 1',
        brief:
          'Looks up the customer record. Returns a verified customer_id. The PreToolUse hook gates all downstream tools until this completes successfully.',
        detail: `## MCP Tool — get_customer

\`\`\`python
{
  "name": "get_customer",
  "description": "Look up a verified customer record by email
    or phone. Must be called before lookup_order or
    process_refund — the PreToolUse hook enforces this.",
  "input_schema": {
    "type": "object",
    "properties": {
      "identifier": { "type": "string" }
    },
    "required": ["identifier"]
  }
}
\`\`\`

### Structured error responses
MCP tools should return typed errors, not strings:

\`\`\`python
# Bad
return {"error": "not found"}

# Good — agent can decide what to do
return {
  "isError": True,
  "errorCategory": "validation",
  "isRetryable": False,
  "content": "No customer found for identifier"
}
\`\`\`

Types: \`transient\` (retry), \`validation\` (bad input), \`permission\` (escalate).`,
      },
      {
        id: 'lookup_order',
        name: 'lookup_order',
        role: 'sub',
        x: 185,
        y: 322,
        sublabel: 'MCP tool · step 2',
        brief:
          'Fetches order details. Gated by PreToolUse — only runs after a verified customer_id exists. PostToolUse trims the 40-field response to 5 relevant fields.',
        detail: `## MCP Tool — lookup_order

Returns order status, amount, fulfilment date, and line items.

### Context window hygiene
Raw order responses can have 40+ fields. The PostToolUse hook trims to only what the agent needs:

\`\`\`python
# PostToolUse trims before the model sees it
KEEP = {"order_id", "status", "amount", "date", "items"}
result = {k: v for k, v in raw.items() if k in KEEP}
\`\`\`

A 40-field response accumulates fast across multiple tool calls. Trimming in PostToolUse keeps context clean without changing the tool itself.`,
      },
      {
        id: 'process_refund',
        name: 'process_refund',
        role: 'sub',
        x: 365,
        y: 322,
        sublabel: 'MCP tool · step 3',
        brief:
          'Issues a refund. The PreToolUse hook blocks calls above $500 before the tool ever runs — the backend never sees a policy-violating request.',
        detail: `## MCP Tool — process_refund

### The full hook sequence for this tool

\`\`\`
Agent sends: process_refund(amount=89.99)
         ↓
PreToolUse: amount > 500? No → ALLOW
         ↓
Tool executes → returns {status: "approved", refund_id: ...}
         ↓
PostToolUse: normalise timestamps, trim verbose fields
         ↓
Agent receives clean result
\`\`\`

If the amount were $600:
\`\`\`
PreToolUse: amount > 500? Yes → BLOCK
         ↓
Returns: {isError: true, content: "use escalate_to_human"}
         ↓
Tool never executes. Backend never sees the request.
\`\`\`

Pre-hook blocking is safer than post-hook interception for financial operations — the transaction never initiates.`,
      },
      {
        id: 'escalate',
        name: 'escalate_to_human',
        role: 'sub',
        x: 545,
        y: 322,
        sublabel: 'MCP tool · fallback',
        brief:
          'Transfers the case to a human with a structured handoff. Called when the customer requests a human, refund exceeds limits, policy is ambiguous, or no progress after 2 attempts.',
        detail: `## MCP Tool — escalate_to_human

### Explicit escalation criteria (in the system prompt)
1. Customer explicitly requests a human — honour immediately
2. Refund exceeds $500 — PreToolUse blocks process_refund, agent must escalate
3. Policy is ambiguous or silent on the specific request
4. No meaningful progress after 2 tool attempts

### Structured handoff
The human agent has no conversation transcript. The handoff must be self-contained:

\`\`\`python
escalate_to_human(
    customer_id = "CUST-9821",
    reason      = "refund_exceeds_limit",
    summary     = "Order #4421 · $89.99 · customer requests "
                  "refund · approved under policy · "
                  "recommended: approve"
)
\`\`\`

### Why explicit criteria beat confidence scores
Self-reported confidence is a feeling, not a condition. "Policy is silent on competitor price matching" is a condition. Escalation triggers should be specific and testable.`,
      },
    ],
    connections: [
      // customer → agent
      { from: 'customer', to: 'agent' },
      // agent sends calls through pre-hook
      { from: 'agent', to: 'pre_hook' },
      // pre-hook forwards (or blocks) to tools
      { from: 'pre_hook', to: 'get_customer' },
      { from: 'pre_hook', to: 'lookup_order' },
      { from: 'pre_hook', to: 'process_refund' },
      { from: 'pre_hook', to: 'escalate' },
      // tools return through post-hook
      { from: 'get_customer', to: 'post_hook' },
      { from: 'lookup_order', to: 'post_hook' },
      { from: 'process_refund', to: 'post_hook' },
      { from: 'escalate', to: 'post_hook' },
      // post-hook returns normalised result to agent
      { from: 'post_hook', to: 'agent' },
    ],
    steps: [
      { agentId: 'customer', status: 'thinking', delay: 300 },
      {
        agentId: 'customer',
        status: 'done',
        delay: 700,
        output: 'Refund order #4421\nI was charged $89.99 — item never arrived.',
      },
      { agentId: 'agent', status: 'thinking', delay: 500 },

      // ── Iteration 1: get_customer ──
      { agentId: 'pre_hook', status: 'thinking', delay: 800 },
      {
        agentId: 'pre_hook',
        status: 'done',
        delay: 550,
        output:
          'PreToolUse — get_customer\n' +
          '───────────────────────────\n' +
          'Check: first call, no gate active\n' +
          'Decision: ALLOW → tool executes',
      },
      { agentId: 'get_customer', status: 'thinking', delay: 200 },
      {
        agentId: 'get_customer',
        status: 'done',
        delay: 1100,
        output:
          'customer_id  CUST-9821\n' +
          'name         Jane Doe\n' +
          'status       active\n' +
          'created_at   1716624000\n' +
          'last_login   1716537600',
      },
      { agentId: 'post_hook', status: 'thinking', delay: 200 },
      {
        agentId: 'post_hook',
        status: 'done',
        delay: 500,
        output:
          'PostToolUse — get_customer\n' +
          '────────────────────────────\n' +
          'created_at  → 2024-05-25T08:00:00Z\n' +
          'last_login  → 2024-05-24T08:00:00Z\n' +
          'Timestamps normalised. Gate unlocked.',
      },

      // ── Iteration 2: lookup_order ──
      { agentId: 'agent', status: 'thinking', delay: 350 },
      { agentId: 'pre_hook', status: 'thinking', delay: 600 },
      {
        agentId: 'pre_hook',
        status: 'done',
        delay: 500,
        output:
          'PreToolUse — lookup_order\n' +
          '───────────────────────────\n' +
          'Check: customer_id verified ✓\n' +
          'Decision: ALLOW → tool executes',
      },
      { agentId: 'lookup_order', status: 'thinking', delay: 200 },
      {
        agentId: 'lookup_order',
        status: 'done',
        delay: 1000,
        output:
          'order_id  #4421\n' +
          'status    delivered\n' +
          'amount    89.99\n' +
          'date      2024-05-20\n' +
          'carrier   FedEx · tracking 7489...\n' +
          'warehouse EAST-03 · picker JD44\n' +
          '... 34 more fields',
      },
      { agentId: 'post_hook', status: 'thinking', delay: 200 },
      {
        agentId: 'post_hook',
        status: 'done',
        delay: 480,
        output:
          'PostToolUse — lookup_order\n' +
          '────────────────────────────\n' +
          'Trimmed 40 fields → 4 relevant\n' +
          'Kept: order_id · status · amount · date\n' +
          'Context saved: ~1,800 tokens',
      },

      // ── Iteration 3: process_refund ──
      { agentId: 'agent', status: 'thinking', delay: 350 },
      { agentId: 'pre_hook', status: 'thinking', delay: 600 },
      {
        agentId: 'pre_hook',
        status: 'done',
        delay: 500,
        output:
          'PreToolUse — process_refund\n' +
          '────────────────────────────\n' +
          'Check: amount $89.99 ≤ $500 ✓\n' +
          'Decision: ALLOW → tool executes',
      },
      { agentId: 'process_refund', status: 'thinking', delay: 200 },
      {
        agentId: 'process_refund',
        status: 'done',
        delay: 900,
        output:
          'refund_id  REF-441\n' +
          'amount     89.99\n' +
          'status     approved\n' +
          'processed  2024-05-25T09:14:00Z',
      },
      { agentId: 'post_hook', status: 'thinking', delay: 200 },
      {
        agentId: 'post_hook',
        status: 'done',
        delay: 480,
        output:
          'PostToolUse — process_refund\n' +
          '──────────────────────────────\n' +
          'processed  → 2024-05-25T09:14:00Z ✓\n' +
          'Result clean. Returning to agent.',
      },
      {
        agentId: 'agent',
        status: 'done',
        delay: 650,
        output:
          'stop_reason = "end_turn"\n' +
          '──────────────────────────\n' +
          'Hi Jane — refund of $89.99 approved.\n' +
          'Refund ID: REF-441\n' +
          'Arrives in 3–5 business days.\n' +
          '\n' +
          'Loop: 3 iterations · 3 pre-hook\n' +
          'checks · 3 post-hook normalises\n' +
          '0 blocks · 0 escalations',
      },
    ],
  },
];
