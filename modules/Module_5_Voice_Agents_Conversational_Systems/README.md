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
| [Assignment](#assignment--a-production-style-voice-reservation-agent-for-hotels) | **Aurora Hotel voice reservation agent** — build a production-style cascade with booking tools, front-desk transfer, guardrails, telemetry, and evals. See [`FDE-01-assignments/Assignment_2_voice_agent`](../../FDE-01-assignments/Assignment_2_voice_agent/). |
| [`bonus/`](bonus/) 🎁 | **Optional** — LLM inference optimization: 4-bit quantization + KV caching, and speculative decoding from scratch. Not required to finish the module. |

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

---

## Assignment — A Production-Style Voice Reservation Agent for Hotels

> **Project:** [`FDE-01-assignments/Assignment_2_voice_agent`](../../FDE-01-assignments/Assignment_2_voice_agent/)
> — **Aurora Hotel**, a reservations voice agent. Runs fully offline in mock mode (no API key),
> then switches to OpenAI or Groq with one `.env` line.

The module's projects contrast two architectures; the assignment has you build and harden **one
cascade end to end** for a real business workflow:

```
caller audio → VAD/endpointing → STT → AgentRouter → LLM → RAG + tools → TTS
```

| Part | Goal | Where it lives |
|:--|:--|:--|
| **4.1 Understand the voice agent architecture** | Trace how audio flows through speech recognition, the LLM, tool calls, and TTS, and where each component fits in a production voice stack. | `pipeline/voice_loop.py`, `pipeline/providers.py`, `mocks/sip-ivr-call-flow.md` |
| **4.2 Build the reservation workflow** | Check room availability, create mock reservations, and manage multi-turn conversations with structured tool calling. | `pipeline/agent.py` (`check_availability`, `create_booking`) |
| **4.3 Handle real-world call scenarios** | Transfer complex requests to the front desk, redirect off-topic conversations back to reservations, and end calls naturally with appropriate fallbacks. | `transfer_to_human`, `end_call`, guardrails in `SYSTEM_PROMPT`, `knowledge/hotel_policies.md` |
| **4.4 Think like a Forward Deployed Engineer** | Analyze model boundaries, operational fallbacks, latency, observability, and what must change before production. | `pipeline/telemetry.py`, `evals/`, `pipeline/scale_check.py`, `livekit/` |

**Get started** (no API key needed):

```bash
cd FDE-01-assignments/Assignment_2_voice_agent/pipeline
python3 smoke_test.py
python3 -m unittest -v test_features.py
PROVIDER=mock python3 voice_loop.py --text
cd ../evals && python3 run_evals.py --suite all
```

Then follow the assignment's [`README.md`](../../FDE-01-assignments/Assignment_2_voice_agent/README.md)
for the live provider and LiveKit setup, and its
[`RUNBOOK.md`](../../FDE-01-assignments/Assignment_2_voice_agent/RUNBOOK.md) for the staged
walkthrough (text agent → tools/RAG → voice → LiveKit → barge-in → telemetry → evals → scale → SIP).

**Connecting it to this module:** Aurora is a cascade, so every Concept 2 trade-off applies —
latency is additive across stages, and each stage is separately observable. For 4.4, use
Concept 4 to argue whether a speech-to-speech version would be acceptable for a booking flow
that mutates state, and use Concept 5's precision/recall framing to extend `evals/`.

---

## Bonus (optional) — LLM inference optimization

> Not required to complete the module. These are self-contained deep-dives for the curious —
> the inference-level techniques that decide *where* a voice agent's latency and cost land.

- [`bonus/Quantization_and_KV_Caching`](bonus/Quantization_and_KV_Caching/) — 4-bit
  quantization with bitsandbytes + Transformers, and measuring TTFT / inter-token latency /
  throughput full-precision vs. quantized (Llama-3.1-8B goes ~30 GB → ~6 GB VRAM).
- [`bonus/Speculative_Decoding_from_scratch`](bonus/Speculative_Decoding_from_scratch/) — a
  small draft model proposes tokens, a large model verifies them in parallel; built from
  scratch to show the accept/reject mechanics.

A GPU is recommended (the notebooks benchmark on an NVIDIA A40 via RunPod).
