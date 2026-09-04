# Module 5 — Real-Time Voice Agents & Conversational Systems

This module is built around **voice agents**: how a text agent becomes a spoken one,
the two architectures for doing it (cascade vs. speech-to-speech), and how to benchmark them
honestly on cost, latency, and capability.

---

## What's in this module

| Folder | What it covers |
|:--|:--|
| [`study-material/`](study-material/) | The conceptual companion — `lesson.md`, `key-concepts.md`, `exercises.md`, `quiz.md`, `recap-and-preview.md`. |
| [`advance-customer-support-agent-feature-A2A-MCP-ADK_cascading`](advance-customer-support-agent-feature-A2A-MCP-ADK_cascading/) | **Cascade voice agent** — STT → sanitize → A2A judge (gate) → ADK agent (+MCP tools, Mem0) → TTS. A pipeline of separately-owned stages. |
| [`advance-customer-support-agent-feature-A2A-MCP-ADK-s2s`](advance-customer-support-agent-feature-A2A-MCP-ADK-s2s/) | **Speech-to-speech voice agent** — Gemini Live, native audio in/out, tools via function calling, judge as a concurrent monitor. One model instead of a pipeline. |
| [`benchmarking_voice_agents`](benchmarking_voice_agents/) | **Cascade vs. S2S benchmark** — runs the *same* agent through both architectures on 15 audio queries and compares cost, latency, and agentic capability. |

> **Note:** Like Module 4, this module is taught primarily through its hands-on projects — the
> two capstone variants and the benchmark *are* the lesson. The conceptual companion lives in
> [`study-material/`](study-material/): read `lesson.md` for the concepts (cascade vs. S2S and
> the benchmark's metrics), then go run the projects below. `exercises.md` and `quiz.md` work
> directly off the actual source files referenced above.

---

## Voice agents

A voice agent is a text agent wrapped in **speech-to-text (STT)** on the way in and
**text-to-speech (TTS)** on the way out. The interesting design question is *where the
intelligence lives*, and there are two answers this module contrasts head-to-head:

- **Cascade** — discrete stages, each independently owned and swappable: STT → sanitize →
  security gate → agent (with tools + memory) → TTS. Maximum control and observability;
  latency is the *sum* of the stages.
- **Speech-to-speech (S2S)** — a single multimodal model (Gemini Live) takes audio in and
  emits audio out, calling tools inline. Lower latency and more natural turn-taking; less
  control over each stage, and the security judge has to run as a concurrent monitor rather
  than an in-line gate.

Both agents share the same tools, database, and memory (Mem0) — so the `benchmarking_voice_agents`
harness can isolate the *architecture* as the only variable. It grades four quality axes
(tool precision/recall, response accuracy/completeness) plus STT word-error-rate, latency
(time-to-first-audio and time-to-finish), cost, and PII leaks.

**Concepts:** STT → LLM → TTS pipeline, turn-taking, latency budgeting, cascade vs. S2S
trade-offs, benchmarking voice systems.

---

## Getting started

Each subfolder is self-contained with its own `README.md` and `requirements.txt`. Start with
`advance-customer-support-agent-feature-A2A-MCP-ADK_cascading` (`./run.sh setup` provisions the
conda env, Postgres, seed data, and `.env`), then run the `-s2s` variant, then compare them with
`benchmarking_voice_agents/reproduce.py`.
