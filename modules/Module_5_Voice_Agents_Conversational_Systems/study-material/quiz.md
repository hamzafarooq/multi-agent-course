# Module 05 — Quiz

<!-- INSTRUCTOR: The quiz-me skill uses these. Answers are here so Claude can check,
     but the rule is Claude NEVER shows them before the learner attempts. Hint first. -->

## Q1. What two constraints does wrapping a text agent in speech add that a chat UI doesn't have?
- Type: recall
- **Answer:** Turn-taking (detecting when the user has stopped speaking, handling
  interruptions, not talking over them) and a much stricter latency budget (dead air feels
  broken in speech in a way an invisible delay doesn't in chat).
- **Hint:** Think about what a send button does for you that speech can't rely on.

## Q2. Why does turning masking on force streaming off in the cascade architecture?
- Type: explain-why
- **Answer:** Masking requires running the A2A Masker over the *complete* reply before it's
  spoken — you can't scrub PII out of a sentence that's already been spoken aloud. So
  `STREAM_ENABLED = AGENT_RESPONSE_STREAM and not MASK`: with masking on, the reply is
  buffered whole and only then spoken; streaming and masking can't both be on at once.
- **Hint:** Ask what it would mean to "un-speak" a word after masking finds PII in it.

## Q3. In the speech-to-speech architecture, can the A2A Security Judge stop the agent's spoken
reply from playing? Why or why not?
- Type: application
- **Answer:** No. Because the model hears raw audio directly, there's no discrete transcript to
  gate beforehand. The Judge only sees the transcript *after* the Live API finishes
  transcribing it, and it runs **concurrently** with the model's response generation — so by
  the time it flags `BLOCKED`, the model may already be speaking or finished. It's a post-hoc
  warning, not a pre-agent gate.
- **Hint:** Compare when cascade's Judge runs (before the agent) to when S2S's Judge runs
  (relative to the model already hearing the audio).

## Q4. Name one thing the cascade architecture buys you that speech-to-speech can't, and one
thing S2S buys you that cascade can't.
- Type: application
- **Answer:** Cascade buys a real pre-agent security gate and full per-stage observability
  (a Phoenix span per stage) — at the cost of additive latency. S2S buys lower latency and
  much more natural turn-taking (native to the Live API) — at the cost of a weaker, post-hoc
  security guarantee and less per-stage visibility.
- **Hint:** One trades control for speed; name what's gained and lost on each side.

## Q5. Why is a tool call graded deterministically in the benchmark, while a spoken answer is
graded by an LLM judge?
- Type: explain-why
- **Answer:** A tool call (which function, which args) is an objective fact you can check
  exactly. A spoken answer's *phrasing* varies ("$120" vs. "one hundred twenty dollars") even
  when the underlying fact is identical, so an LLM judge is needed to grade meaning rather than
  exact text — and the judge is also shown the actual tool calls, so it can penalize a reply
  that claims an action (e.g. "I've logged your return") that no tool call actually performed.
- **Hint:** One is a fact you can string-match; the other can be phrased many correct ways.
