# Module 05 — Exercises

<!-- INSTRUCTOR: Hands-on tasks for the build-along skill. Goal first, then steps,
     then a "done when" check. Exercises 1 and 3 work by reading code/data — no stack
     needed. Exercise 2 needs the live stack; say so up front and offer the reading-only
     alternative if the learner can't run it. -->

## Exercise 1 — Trace the security check across both architectures

**Goal:** See exactly why S2S's security guarantee is weaker than cascade's, in the code, not
just in the description.

**Steps:**
1. In `advance-customer-support-agent-feature-A2A-MCP-ADK_cascading/cs_agent/voice/router.py`,
   find the `[1] local sanitizer` and `[2] A2A Security Judge` blocks. Notice the Judge call is
   `await`ed and a `blocked` response is sent *before* the agent ever runs.
2. In `advance-customer-support-agent-feature-A2A-MCP-ADK-s2s/cs_agent/voice.py`, find
   `_judge_transcript` and the `judge_mode` field set to `"concurrent"`. Read the comment
   explaining the guardrail runs "CONCURRENTLY so it never delays audio."
3. Note the two Judge instances run on different ports (cascade `10002`, S2S `11002`) — they
   aren't the same running service.
4. Answer in one sentence: in S2S, can the Judge stop the agent's spoken response from playing?

**Done when:** You can point to `judge_mode: "concurrent"` in `voice.py` and to the blocking
`await judge(clean)` in cascade's `router.py`, and explain the timing difference — gate-before
vs. flag-after — in your own words.

**Stretch (optional):** Start both stacks (`./run.sh web` for cascade, `./run.sh voice` for
S2S) and speak the sample injection query (`'; DROP TABLE users; --`) into each. Compare what
happens — and when.

## Exercise 2 — Run the cascade agent and read its Phoenix trace

**Goal:** See per-stage latency for real, not just as a diagram.

**Steps:**
1. In `advance-customer-support-agent-feature-A2A-MCP-ADK_cascading`, run `./run.sh setup` once,
   fill in `.env`, then `./run.sh web`.
2. Open `http://127.0.0.1:8000`, click the mic button, and ask a question (e.g. "what's the
   status of order 3?").
3. Open `http://localhost:6006` (Phoenix) and find the trace for your turn. Locate the
   `GUARDRAIL`, `CHAIN`, and `TOOL` spans.
4. Identify which span took the longest — STT, the Judge, the agent's reasoning, the MCP tool
   call, or the Masker.

**Done when:** You can name the slowest stage for your turn and say whether that matches the
"latency is additive" claim from Concept 2.

**Stretch (optional):** Edit `.env` to set `MASK=false` and `AGENT_RESPONSE_STREAM=true`,
restart, and repeat the same question. Compare the trace's shape — does the reply's audio start
sooner?

## Exercise 3 — Predict a benchmark result, then check it

**Goal:** Use the benchmark's own vocabulary (hop, precision/recall, WER) to make a falsifiable
prediction before looking at the answer.

**Steps:**
1. Open `benchmarking_voice_agents/manifest.json`. Find query `q01` ("What is the current status
   of my order number three?", `hops: 1`) and `q05` ("I'd like to cancel my most recent order...",
   `hops: 2`).
2. For each, write down the `expected_tools` and `expected_answer`.
3. Predict: which architecture (cascade or S2S) do you expect to have lower **tool recall** on
   `q05`, given that a 2-hop action depends on getting the first lookup's result correct before
   acting on it? Write your reasoning down before looking.
4. Open `comparison/comparison_table.png` (or `comparison/comparison_accuracy.png`) and check
   your prediction against the actual numbers.

**Done when:** You can state your prediction, the actual result, and — whether you were right or
wrong — explain *why*, using "hop," "precision," or "recall" correctly.
