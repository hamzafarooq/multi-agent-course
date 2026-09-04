# Skills, Sub-Agents & Multi-Agent Architectures

An interactive Next.js visualization that teaches three concepts most people get wrong.

## What this covers

**A skill is a reusable prompt.** Not an agent, not a pipeline — just a `.md` file with a system prompt and a task. You save it once, invoke it by name, and reuse it anywhere.

**Two skills do not make a sub-agent.** Chaining two prompts in sequence is just two API calls. A sub-agent is architecturally different — it runs in its own context window, with its own role, and the calling agent only sees the result. The isolation is the point.

**Sub-agents are different from skills.** A skill is something you invoke. A sub-agent is something Claude delegates to. One is a saved prompt; the other is a separate model call with its own instructions.

## The four levels

| Level | Name | What it teaches |
|-------|------|----------------|
| 1 | Single Skill | A skill = a `.md` file = a reusable prompt |
| 2 | Sub-Agent | Why delegation is not the same as calling two skills |
| 3 | Parallel Agents | Fan-out to multiple sub-agents, fan-in to one result |
| 4 | Orchestrator | A model call whose only job is to plan and dispatch |

Each level has an animated simulation, an explanation, and Python code using the Anthropic SDK.

## Run it locally

```bash
cd skill-sub-multi-agent
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000).

## What the code shows

All code examples use the Anthropic Python SDK. Level 1 shows the `.md` file pattern explicitly — the system prompt is loaded from a file, not hardcoded. Levels 3 and 4 use `asyncio.gather` for parallel calls.

```python
# A skill is just a .md file loaded as the system prompt
with open("skills/content-strategist.md") as f:
    skill_prompt = f.read()

response = client.messages.create(
    model="claude-opus-4-5",
    system=skill_prompt,
    messages=[{"role": "user", "content": "..."}]
)
```

## Files

```
skill-sub-multi-agent/
├── app/page.tsx              ← main page, level selector
├── components/
│   ├── SimulationView.tsx    ← animated agent graph
│   ├── ConceptCallout.tsx    ← explanation + code tabs
│   ├── AgentNode.tsx         ← individual node
│   └── LevelSelector.tsx     ← left nav
└── lib/demo-data.ts          ← all level content, briefs, code, sim steps
```

To update content — text, code examples, agent briefs — edit `lib/demo-data.ts`.
