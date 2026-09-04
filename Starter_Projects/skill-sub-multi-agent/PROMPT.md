Build a single-page Next.js app that teaches the 4 levels of Claude agent architecture through animated simulations. No real API calls — everything is pre-scripted.

**The concept:** Every level solves the same task — "Build a 30-day content plan for an AI SaaS startup targeting developers" — but with increasing agent sophistication. The user picks a level, clicks Run Demo, watches the agents animate, and reads an explanation below.

---

**Layout:**
- Header with app name
- Left sidebar: 4 level selector buttons, use case description pinned at bottom
- Main area: level title, breadcrumb stepper (1→2→3→4), visualization canvas (~480px tall), Run/Reset controls, final output panel, concept callout with two tabs

---

**The 4 levels:**

Level 1 — Single Skill: One agent node ("Content Strategist") centered on canvas. No connections. Clicks Run → thinking → done → outputs a 30-day content calendar.

Level 2 — Sub-Agent: Two nodes stacked. Main "Content Strategist" (top) spawns "Trend Researcher" (bottom). Sequence: main thinking → sub thinking → sub done (returns trends) → main done (uses trends to build plan). Connection lines: main→sub then sub→main.

Level 3 — Parallel Agents: Five nodes. "Content Strategist" at top fans out to 3 simultaneous agents ("Trend Researcher", "Competitor Analyst", "Audience Profiler") in a middle row, which all feed into a second "Content Strategist" (merge) at bottom. All 3 middle agents start at the same time, finish in staggered order, then the merge node synthesizes.

Level 4 — Orchestrator: Six nodes. "Orchestrator" at top routes to 4 specialists ("Trend Researcher", "Competitor Analyst", "Audience Profiler", "Content Writer") in a middle row, all feeding into "Synthesizer" at bottom. Orchestrator goes done first (announces it decomposed the goal), then 4 specialists run in parallel and finish staggered, then Synthesizer produces final output.

---

**Simulation engine:**
Each level has a steps array: `{ agentId, status: 'thinking'|'done', output?: string, delay: number }`. When Run Demo is clicked, steps fire sequentially after their delay. Thinking state = agent is active. Done state = agent shows output text. When an agent goes thinking, incoming connection lines activate (animate). When it goes done, outgoing connections activate. After all steps complete, show a Final Output panel with the last done agent's output.

**Agent states:** idle → thinking → done. Reset clears back to idle.

**Connections:** SVG lines drawn between agent nodes based on position. Inactive by default, animated when active. Each connection is `{ from: agentId, to: agentId }`.

---

**Concept callout (below the canvas):**
Two tabs — "What's happening" (plain-English explanation + one-sentence analogy) and "How to write it" (code snippet showing how to write this pattern using Claude's Agent tool).

---

**Interactions:**
- Run Demo: starts animation, disabled while running
- Reset: appears after done, clears all state
- Level selector: switching levels immediately resets simulation
- Two tabs in concept callout toggle independently of simulation state

---

Write realistic pre-scripted outputs for each agent. Use a clean white/light theme. No auth, no persistence, no mobile optimization needed.
