# Reference — The Four Levels of Agentic Architecture

<!-- INSTRUCTOR: Deep-dive Claude can pull from when a learner wants more than the lesson.
     Filled with deck structure; expand as you like. -->

## The spectrum
From **deterministic workflow / predefined automation** → **autonomy / self-reflection**,
with increasing **complexity**.

## Level 1 — Simple LLM
Single prompt in, answer out. No tools, no loop. (e.g. "draft me an email asking for 2 weeks off".)

## Level 2 — LLM connected to tools
The model calls tools within a known process. Use when:
- You can map the process as a flowchart with clear decision points
- Execution paths are finite and predictable (<15–20 branches)
- Completion takes seconds to minutes
- The value is automating a *known* process, not discovering new approaches

## Level 3 — Thinking & reasoning
Dynamic planning over ambiguous requests. You need this when:
- Branching explosion (30+ nodes, new branches weekly)
- Unpredictable user phrasing
- Dynamic tool selection (decide *which* API from context)
- Multi-step reasoning requiring exploration, not predefined decomposition

## Level 4 — Agent-to-agent
Multiple agents coordinate, delegate, and hand off (e.g. "find candidates, schedule
interviews, then start background checks"). Highest autonomy and complexity.

## A caution
Reliability compounds: if each step is 95% accurate, a 30-step workflow rarely completes.
Going from prototype to reliable at scale is the hard "last mile."
