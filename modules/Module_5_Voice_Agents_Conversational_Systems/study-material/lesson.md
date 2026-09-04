# Module 05 — Voice Agents

<!-- INSTRUCTOR: This is the teaching content Claude walks the learner through.
     Each ## is roughly one "concept" Claude presents, then checks understanding on.
     Source: the two capstone variants (…_cascading and …-s2s) and benchmarking_voice_agents
     (the systems ARE the lesson, same as Module 4) + this module's own README. Keep chunks short. -->

## Learning objectives

By the end of this module the learner can:
- [ ] Explain what turns a text agent into a voice agent, and the two new constraints that come with it
- [ ] Describe the **cascade** architecture (STT → sanitize → A2A Judge → agent → A2A Masker → TTS) and why each stage is separately owned
- [ ] Describe the **speech-to-speech (S2S)** architecture (Gemini Live) and why its security check has to become a post-hoc, concurrent guardrail instead of a pre-agent gate
- [ ] Argue the cascade vs. S2S trade-off using control/observability vs. latency/naturalness
- [ ] Explain how the benchmark isolates architecture as the only variable, and what its precision/recall-split metrics actually measure

## Prerequisites
- Module 4 (protocol layer: MCP, A2A, ADK). This module doesn't introduce a new agent — it
  takes the **exact same** ADK support agent, MCP tools, and Mem0 memory from the Module 4
  capstone and wraps it in speech, two different ways.

---

## Concept 1 — From text agent to voice agent

A voice agent is not a new kind of agent — it's the Module 4 support agent wrapped in
**speech-to-text (STT)** on the way in and **text-to-speech (TTS)** on the way out. Same tools,
same database, same Mem0 memory. So what actually changes?

Two things a chat UI never has to think about. First, **turn-taking** — in text, the user
decides when their turn ends by hitting send; in speech, the system has to detect when someone
has *stopped talking*, handle interruptions, and avoid talking over the user. Second, a
**latency budget** — a 2-second pause before a chat reply is invisible; a 2-second dead-air gap
in a phone call feels broken. Every design choice in this module — where the security check
sits, whether the reply streams or buffers — traces back to that latency budget.

That sets up the module's central design question: where does the intelligence live? As
**discrete, inspectable stages** (STT, a security check, the agent, TTS — cascade), or **fused
into one model** that hears audio and speaks audio directly (speech-to-speech)? Concepts 2 and 3
are the two answers.

**Check:** What two constraints does wrapping a text agent in speech introduce that a chat UI
doesn't have to solve?

## Concept 2 — The cascade architecture

**Cascade** keeps the Module 4 pipeline completely intact and bolts speech onto its edges:

    audio in → STT → sanitize → A2A Security Judge → ADK agent (+MCP tools, Mem0) → A2A Masker → TTS → audio out

Every stage is separately owned, independently swappable, and fully observable — Phoenix
records a span per stage, so you can see exactly how long STT, the Judge, the agent, and the
Masker each took on a given turn. Crucially, the Judge is a **full pre-agent gate**: a blocked
message never reaches the agent at all, exactly like the Module 4 capstone. The cost of that
control is additive latency — the total time is roughly the *sum* of every stage's time.

That latency budget shows up as a real trade-off in the code. Two env flags interact with a
deliberate interlock: `STREAM_ENABLED = AGENT_RESPONSE_STREAM and not MASK`. With masking on
(the default, `MASK=true`), the full reply is generated, run through the A2A Masker, and *then*
spoken — you can't mask a sentence you're already speaking. Turn masking off and streaming on,
and each sentence is spoken as the agent generates it, with no masking. You cannot have both
sentence-level streaming and masking at once; the code picks masking and warns you, it doesn't
silently do both.

**Check:** Why does turning masking on force streaming off, rather than the two working together?

## Concept 3 — The speech-to-speech (S2S) architecture

**Speech-to-speech** fuses the pipeline into one multimodal model: **Gemini Live**, driven by
ADK's bidirectional streaming (`runner.run_live()` with
`RunConfig(streaming_mode=BIDI, response_modalities=["AUDIO"])`). Audio goes straight into the
model and audio comes straight back out — the same ADK agent, MCP tools, and Mem0 memory are
still there, just reached through one live connection instead of four pipeline stages.

Here's the catch: because the model hears **raw audio directly**, there is no discrete
transcript to gate *before* the model responds — unlike cascade, there's no STT stage output
sitting there waiting to be checked first. So security becomes a **post-hoc, concurrent
guardrail**: when the Live API finishes transcribing what the user said, that transcript is sent
to the A2A Security Judge (its own instance, on a separate port from cascade's) *at the same
time* the model is already generating its spoken reply. If the Judge comes back with `BLOCKED`,
the UI shows a warning *after the fact* — it does not stop the audio already being spoken. Output
masking is display/log-only for the same reason: you can't un-speak audio that's already played.

This is a real, documented trade-off, not an oversight: you get much lower latency and far more
natural turn-taking (the model can be interrupted, react instantly, no pipeline hop between
stages) in exchange for a strictly weaker security guarantee than cascade's pre-agent gate.

**Check:** In S2S, can the Security Judge prevent the agent's spoken response from playing? Why
or why not?

## Concept 4 — Cascade vs. S2S: the trade-off

Put side by side:

| | Cascade | Speech-to-speech |
|---|---|---|
| Security check | Pre-agent gate — blocks before the agent runs | Post-hoc, concurrent — flags after the model has already heard/responded |
| Latency | Sum of every stage (STT + sanitize + Judge + agent + Masker + TTS) | One live connection; no pipeline hops |
| Control / observability | Every stage independently inspectable (a Phoenix span each) | One model call; less per-stage visibility |
| Turn-taking | As good as the STT/TTS layer allows | Natural — native to the Live API |

Same agent, same tools, same database, same memory in both — architecture is the *only*
variable. That's exactly what makes them comparable, and it's the whole premise of Concept 5:
if you hold everything else fixed, any difference you measure is caused by the architecture
choice itself.

**Check:** Name one thing cascade buys you that S2S can't, and one thing S2S buys you that
cascade can't.

## Concept 5 — Benchmarking voice agents

The `benchmarking_voice_agents` harness runs the **identical** agent through both architectures
on the same 15 audio clips, **3 times each**, with the database reseeded to the same baseline
and Mem0 empty for every run — so nothing except the architecture differs between the two arms.

It scores four quality numbers, each split into a **precision** and a **recall** half:

- **Tool accuracy** (precision) — of the tools it *called*, how many were the right tool with
  the right args? Graded **deterministically** — a tool call is an objective fact.
- **Tool recall** — of the tools it *should* have called, how many actually fired?
- **Response accuracy** (precision) — of what it *said*, how much was correct — including not
  claiming an action it never performed (an **LLM judge** grades this, because phrasing varies:
  "$120" and "one hundred twenty dollars" are the same fact said two ways. The judge is shown
  the actual tool calls, so a reply that claims "I've logged your return" with no `action-log`
  call gets penalized).
- **Response completeness** (recall) — of the info/actions the answer required, how much did it
  actually convey or do?

Plus STT **word-error-rate (WER)**, **latency** (time-to-first-audio and time-to-finish, timed
by one neutral stopwatch that excludes the Judge's time and the cascade's settle wait — so the
number is pure STT+agent+TTS), **cost per turn**, and **data-isolation leaks** (did a reply leak
another user's data?). Because both the agent and the LLM judge are sampled models, individual
runs wobble — that's why each query runs 3× and results are reported as **mean ± std**: the
*conclusion* should reproduce even when the exact numbers don't.

One more piece of vocabulary: a **hop** is a dependent tool call on the critical path
(excluding the always-on `search_memory`). "What's the status of order 3?" is **1 hop** — one
lookup. "Cancel my most recent order" is **2 hops** — list orders to find the newest id, *then*
log the cancellation using that id; the second call depends on the first call's result.

**Check:** Why is a tool call graded deterministically, but a spoken answer graded by an LLM
judge?

---

## Summary
1. A voice agent is a text agent plus STT/TTS, constrained by turn-taking and a latency budget.
2. **Cascade** keeps every stage separate and puts a real pre-agent gate in front of the model —
   at the cost of additive latency. **S2S** fuses everything into one model for lower latency and
   natural turn-taking — at the cost of security becoming a post-hoc, concurrent check.
3. The benchmark holds the agent, tools, DB, and memory fixed so architecture is the only
   variable, and scores both *what fired* (deterministic) and *what was said* (LLM-judged).

## Where to next
- Do `exercises.md` (trace the security check across both architectures, then run the stack and
  read a Phoenix trace) or ask to be quizzed (`quiz.md`).
- To see it run: follow the cascade project's `README.md`, then the S2S sibling, then
  `benchmarking_voice_agents/reproduce.py` to compare them yourself.
- This is the final module in the course — after this, `warmup` has nothing further to preview.
