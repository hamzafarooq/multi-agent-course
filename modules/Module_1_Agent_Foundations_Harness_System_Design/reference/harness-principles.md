# Harness design principles

*Nine rules that survive a change of language, framework and model. Each one is followed by
the line in LUMINA that implements it — read the rule, then go look at the code.*

The assignments hand you a lot of scaffolding, and scaffolding has a failure mode: you can
build the whole system by following instructions and never learn why any instruction exists.
Rules like *"flush after every token"* look like trivia. They aren't. Each one below is the
compressed form of a production incident.

If you only remember one thing: **a harness is the set of decisions that stay true when you
swap the model.** Everything the model does is temporary. Everything below is the system.

---

## 1. Stream the first token, not the first answer

A user waits ~1 second before a page feels broken. Your model takes 4–8 seconds to finish
thinking. The gap is bridged by showing work as it happens — the trace, the sources, then
tokens — not by making the model faster.

This is why `flush` appears in the instructions. Buffering a "stream" until it completes is
batch processing wearing a streaming costume: same total latency, same code shape, none of
the benefit. If your framework buffers by default (most do, for throughput), you must
explicitly defeat it at every layer — the model client, your handler, the proxy, the CDN.

> **LUMINA:** `sources` is emitted before the first `token` event, on purpose. A citation
> list that arrives with the answer is decoration; one that arrives before it is evidence the
> system found something.

**Test it:** curl the endpoint. If output appears all at once, you have not built streaming,
whatever the code says.

## 2. Make one unit of work, one durable record

Every answer should leave behind exactly one artifact describing how it was produced: the
tools called, in order, with inputs, outputs, timings and cost.

This is ten lines of adapter and it is the difference between debugging and guessing. You
cannot reason about an agent from its final message — the message is the one part that looks
fine when everything upstream went wrong. Agents fail in the middle: a tool returned empty
and the model improvised around it, a retry silently doubled cost, a step ran twice.

> **LUMINA:** one run log per answer, and `quality/check.mjs` reads those logs rather than
> the responses. The gates grade your trace, not your prose.

## 3. Declare the budget before you run

Latency, cost and quality targets are written down *before* the first measurement, not
derived from it. A number you invent after seeing the result is not a target, it is a
description with a ribbon on it.

This is why `sla.json` and `expectations.json` ship pre-filled. In a customer engagement you
will be asked "how fast will it be?" before you have built anything. The habit of committing
to a number and then meeting it — or explaining the gap honestly — is the job.

> **LUMINA:** `benchmark/sla.json`, declared up front. `bench.mjs` exits non-zero when you
> miss. Correct-but-slow fails; correct-but-expensive fails.

## 4. A tool is a contract, not a function

Whatever the model can call, define by its schema: name, typed inputs, typed outputs, error
shape. The model sees only that description, so the description *is* the tool as far as the
system is concerned. Half of all "the model is dumb" bugs are a tool whose description does
not say what it actually does.

Validate arguments coming in. Return typed errors, not prose. A tool that returns
`"Sorry, something went wrong"` teaches the model to hallucinate a recovery; one that returns
`{error: "rate_limited", retry_after: 30}` lets it do the right thing.

> **LUMINA:** the zod schemas in `packages/contract/`. They are not documentation of the
> API — they are the API, and both the UI and the grader are written against them.

## 5. Separate the hot path from the heavy path

A search is latency-critical, read-only and small. Ingesting a document is bursty, slow and
expensive. Run them in the same process and one backfill starves every user.

The seam is a queue. Accept the work, return an id immediately, let workers drain it at their
own pace. This is the single most common architectural mistake in AI products, because the
naive version works perfectly until the first real workload.

> **LUMINA:** upload returns `202` and a jobs collection carries the work.
> **ARGUS:** the whole assignment, with an SLA on search latency *during* a large ingest.

## 6. Commit state after the write that makes it true

Mark a document `indexed` only after the vector upsert succeeds. Mark a job `done` only after
its output is durable. Get this backwards and a worker that dies mid-task leaves state
claiming work that never happened — and no retry will fix it, because the system believes it
already finished.

Then make each step idempotent, because at-least-once delivery means every step will
eventually run twice. Idempotency is not a nicety here; it is the price of using a queue at
all.

> **ARGUS:** `bench.py --resilience` kills a worker mid-ingest and asserts zero loss with no
> re-run of finished stages. If your ordering is wrong, this is where you find out.

## 7. Ground every claim in something retrievable

If the system asserts a fact, it must be able to point at where the fact came from — a
document and a location inside it, not a vague reference to the corpus.

The test is not "does it cite" but "can the citation be checked". A page number the model
produced is a guess; a page number carried through parse → chunk → embed → retrieve is
evidence. Design so the locator travels with the text and the model never has to invent one.

And when retrieval finds nothing, return nothing. An agent that answers anyway is worse than
one that fails, because it fails invisibly.

> **Module 3:** every citation in the RAG notebooks carries its chunk. When the corpus lacked
> Uber's filing, the model said so rather than inventing figures — that was grounding
> working, and it is the only reason the missing data was caught at all.

## 8. Put the permission check before the work, not after the result

Filtering results after retrieval means the restricted content was already loaded, already
sent to the model, already summarised into an answer. The check belongs before anything is
embedded, searched or generated — and, for partial access, inside the query itself as a
filter the retriever cannot ignore.

The same applies to anything that remembers: a cache keyed only on the question will happily
serve one user's answer to another. Any store sitting behind an access check must be
partitioned by the same boundary.

> **Module 3:** route-level RBAC in notebook 001, file-level in 003, and a payload filter in
> 003's closing note. The cross-role cache leak is the bonus assignment precisely because
> it's the mistake people ship.

## 9. Fail loudly at the seams

The worst bug in this course's own materials was `wget -q` writing an error page to a `.pdf`
filename. The download "succeeded", the ingest ran, the collection was built, and months
later an agent answered questions about one company using another's financials.

Every boundary where data enters your system — a download, a parse, an upload, an API
response — needs an assertion that what arrived is what you asked for. Count the records.
Check the type. Assert the expected number of files. A loud failure at ingest costs minutes;
a silent one costs a semester of wrong answers.

> **Module 3:** the upload notebook now asserts all four filings loaded and prints their
> sizes. That assertion is worth more than the code it guards.

---

## Using these

When something in an assignment looks arbitrary, find the principle it serves. If you can't,
ask — either you've found the gap in your understanding, or you've found a bug in ours. Both
are worth surfacing.

When you design your own harness later, these are the questions to ask in order:

1. What does the user see in the first second?
2. What record does one unit of work leave behind?
3. What did I promise about latency, cost and quality — in writing, beforehand?
4. What exactly can the model call, and what does it see when that call fails?
5. What's on the hot path, and what must be moved off it?
6. What happens if this process dies right now?
7. Can every claim be traced to a source a human could open?
8. Where is the permission check, and what remembers things behind it?
9. Where could something fail silently, and what assertion would catch it?

None of these mention a model, a framework, or a language. That is the point.
