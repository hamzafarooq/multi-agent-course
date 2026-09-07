# Agent Loops and How They Fail

*LUMINA gold corpus, document 3 of 4. FDE Agent Engineering Bootcamp. CC BY 4.0.*

## The loop

An agent is a loop around a model that can call tools. One iteration: send the state to the
model, receive either a tool call or a final answer, execute the tool, append the result to
the state, repeat. When the model answers instead of calling a tool, the loop ends.

That is the whole mechanism. There is no planner module and no reasoning engine; the
"planning" is the model choosing the next tool, and the loop's quality is decided by three
things that surround it — what tools it has, what the results look like when they come
back, and when it is made to stop.

## Bounded, or not a loop

An unbounded loop is a production incident with a countdown. Two caps are mandatory:

- a **maximum number of tool calls** per request, and
- a **maximum wall-clock time** per request.

Both must be enforced by the harness, not requested of the model. A prompt asking the model
to use at most eight tools is a suggestion; a counter in the loop is a cap.

Hitting a cap is not the same event as finishing, and the difference must survive into the
output. A run that stops because it ran out of budget and reports the same status as a run
that stopped because it was done has destroyed the only signal that distinguishes a working
agent from a lucky one.

The convention this course uses is a `terminated` field with three values, set explicitly at
the call site because no SDK provides it:

- **`done`** — the model produced a final answer on its own.
- **`cap`** — a tool-call or time cap ended the run. The answer, if any, is a partial and
  must say so.
- **`error`** — a tool or provider raised. The request fails.

## Tool results are the model's only senses

The model cannot see the world; it sees strings you hand it. A tool that returns an empty
string on failure has told the model "there is nothing there", which is a fact about the
world, not a fact about the tool. The model will believe it and answer accordingly.

So a failed tool call must be distinguishable from an empty successful one. In practice that
means every tool result carries a success flag and, when it failed, a non-empty error
string describing what went wrong. `{ok: false, error: "403 from publisher"}` teaches the
model to try another source. `""` teaches it that the source was blank.

## The silent fallback

The most expensive bug in this class of system is a `try/catch` that returns something
plausible.

The pattern: a provider call is wrapped in a catch, the catch returns a default — the input
unchanged, an empty result, the string "I could not find anything" — and the caller returns
200. Every layer above sees a success. Logs show no errors. Dashboards are green. The
product is broken, and the only way to find out is for a human to read the output and
notice it is wrong.

A real instance, and the reason this course states the rule: a translation service's LLM
calls all began throwing after a dependency upgrade. The exception handler returned the
input text untouched. The service returned English to every user, with a 200 and no error
logged, for weeks. It was caught by a person reading output, not by a test, because from
every automated angle the system was healthy.

The rule that follows: a provider exception ends the run with an error status and surfaces
as a failure to the caller — a `502` in an HTTP service. Never a success with a plausible
body. "Fail loud" is not a stylistic preference; it is the only way a failure becomes
information.

## Grounding

An agent that retrieves and then cites must be held to one arithmetic rule: every citation
resolves to something retrieved **in that request**.

This is checkable without judgment. Collect the citation markers in the answer; collect the
sources returned for that answer; the difference must be empty. A marker with no source is
a fabrication regardless of whether the underlying claim happens to be true. A source that
was retrieved in a previous request is not evidence for this one.

The stronger check is that the cited snippet is really present in the fetched page or the
indexed chunk. Compare after normalizing case, whitespace, and quotation marks, and require
a run of consecutive matching tokens — on the order of a dozen — rather than exact string
equality, because a curly apostrophe should not fail an honest citation.

Both checks are arithmetic. Neither asks a model for an opinion, which matters, because a
model asked to grade grounding will confidently approve a fabricated citation often enough
to make the metric worthless.

## Traces

A trace is the ordered record of what the loop did: each step, the tool, its input, whether
it succeeded, how long it took, and why the step happened. It is not a progress bar. It is
the artifact that lets someone reconstruct why an answer cited what it cited, weeks later,
without a debugger.

The test of a trace is a question: from this alone, can a reader explain this answer? If a
step's `reason` is missing, or a failure appears as an absence rather than an error, the
answer is no, and the trace is decoration.

## Judging a run

A streamed answer with a green status proves the process did not crash. It does not prove
the run worked. Four things prove that, and each is a number declared before the run rather
than after:

1. **Termination** — it stopped because it finished, not because it ran out.
2. **Grounding** — every citation resolves.
3. **Budget** — tokens, wall clock, and cost stayed inside what was declared.
4. **Retrieval** — the run actually retrieved, rather than answering from the model's own
   parameters.

The fourth is the one teams forget. An agent that answers a factual question correctly
without calling a single tool has not demonstrated retrieval; it has demonstrated that the
answer was in the training data. On the next question, where it is not, the same code path
produces a confident invention.

## Reading the trajectory

Before signing off on an agent, read one complete successful run and one complete failing
run, every step. Not a sample, not the summary — the whole thing, twice.

Automated gates check what you thought to encode. Reading a trajectory is how you find what
you did not: a tool called three times in a row because its error was swallowed, a retrieval
that returned the right chunk and was ignored, a step whose reason makes no sense. Teams
that cannot produce a failing trajectory on demand do not yet know their own failure
surface. If one will not occur naturally, revoke an API key and run again.
