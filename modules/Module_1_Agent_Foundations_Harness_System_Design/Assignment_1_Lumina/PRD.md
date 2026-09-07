# LUMINA — a Perplexity-style AI search engine

*Assignment 1 · FDE Agent Engineering Bootcamp, cohort 2026-03 · Week 1, due end of Week 2 · Owner: Hamza Farooq*

> **Read this one.** It is the product, in about fifteen minutes of reading, and it is
> everything you need to make design decisions. The exhaustive version — every status code,
> every threshold, every failure mode — is [`SPEC.md`](SPEC.md), written for a coding agent
> to work from. You will want it open while you build; you do not need it to start.
>
> **No thresholds appear in this document.** They live in `benchmark/sla.json`,
> `expectations.json` and `eval/rubric.json`, and those files are the only place they are
> true. A number restated in prose is a number that will be wrong by Week 2.

---

## What you are building

Ask a question. Get an answer that streams in as it is written, with citations you can
click, built from a live web search and from your own uploaded documents. It remembers what
you tell it, across sessions. Ask a harder question and it decomposes it, researches each
part, and merges everything into one set of citations.

Perplexity, in other words. Not a notebook that calls an LLM — a product a stranger can
open and use.

## Two gears, and the lesson is knowing which to use

**Quick** is the default. One pass: search, read a couple of pages, write a cited answer in
a few seconds. This is what most questions deserve.

**Deep** is Perplexity's Pro Search. It plans sub-questions, researches each one, and merges
the results into a single citation numbering. It costs several times as much and takes up to
a minute.

Building both is the assignment. Knowing which a question deserves is the lesson. A system
that runs deep machinery on "what port does mongod listen on?" is slow and uneconomic; one
that never digs is useless on a real question. Quick stays the default, deep is something a
user opts into, and the server never upgrades a request on its own — because a product that
escalates itself is a product with an unbounded bill.

## The five capabilities

| | What it means | Where it comes back |
|---|---|---|
| **The loop** | Plan, choose a tool, observe, repeat, stop. Yours, not a framework's. Bounded, and honest about why it stopped. | Every later project. The harness is the course. |
| **Search** | The web as a tool the agent chooses, with pages actually fetched and read rather than snippets skimmed. Cached, because repeats should be free. | ARGUS, EPYHIA |
| **Deep search** | Query decomposition, per-sub-question retrieval, merged citations. | Module 3's Pro search and re-ranking |
| **Memory** | Thread history, plus durable facts you can see and delete. | Module 2, VOXA |
| **RAG** | Your own documents, chunked and indexed, cited down to the page. | ARGUS extends this exact contract |

## The rules that decide your grade

Four, and they are the whole philosophy:

**Grounded or nothing.** Every `[n]` in an answer resolves to something the system actually
retrieved *in that request*. A citation that does not is an automatic fail, whether or not
the claim happens to be true. If retrieval comes back empty, the answer says so and cites
nothing.

**Fail loud.** A provider exception ends the run as an error and reaches the caller as a
`502`. Never a `try/catch` that returns a plausible answer. This rule has a precedent: a
previous cohort's translation service had every LLM call start throwing after a dependency
upgrade; the exception handler returned the input text untouched; it served English to every
user, with `200`s and nothing in the logs, for weeks. It was found by a person reading
output, not by a test.

**Bounded and honest.** Caps exist on tool calls and wall-clock time, per gear. Hitting one
is a different outcome from finishing, and the difference has to survive into the response.
A run that stopped because it ran out, reported as though it were done, has destroyed the
only signal that separates a working agent from a lucky one.

**Evidence over vibes.** Every number that grades you comes from a run against your deployed
app. Thresholds are declared before the first run — one set after seeing a score is a
description, not a target.

## What you get, and what you build

You get a **working React UI** and a **typed API contract**. You build the two Express
services behind them. When your backend works, the UI lights up; until then every panel says
`501 not implemented yet`, which is your progress bar.

You do not get to change the contract. The UI is the acceptance test, and conforming to an
interface you did not design is most of forward-deployed work.

```
  Browser ──HTTP+SSE──▶  Gateway  ──▶  Agent service  ──▶  Search · LLM · MongoDB Atlas
                         (yours)       (yours)
                         the edge:     the work: the loop, its tools,
                         CORS, auth,   memory, RAG, deep search,
                         validation,   the jobs worker.
                         rate limits.  Provider keys live ONLY here.
```

**Why two services?** Browser-facing concerns are not AI concerns. Splitting them means each
deploys and fails on its own, and your API keys never live somewhere the browser can reach.

**Why one database?** Atlas Vector Search puts the embedding in the same document as the
chunk text and its page number, so a citation is one document read instead of a join across
two stores that have to agree about ids.

**About the stack.** MERN is the taught path and what office hours will be able to help you
with: MongoDB Atlas, Express, React, Node — one language from the citation chip to the
vector query, so debugging never crosses a runtime boundary. The *contract* is what is
actually graded, and the grader speaks HTTP: if you would rather build the backend in
something else, `/health` must name what you used, and every gate still has to pass. That is
your call to make and your risk to carry.

## The five questions

Before you open an editor, write `DESIGN.md` from [`DESIGN.template.md`](DESIGN.template.md):

1. **Components** — what are the pieces, and where does each run?
2. **Responsibilities** — what is each piece the *only* one allowed to do?
3. **Communication** — how does each pair talk, and what happens when one is down?
4. **State** — what is stored, where, who owns it, and what is merely a cache?
5. **Trade-offs** — three decisions a reasonable engineer would have made differently, and
   what you gave up.

This is graded, it renders on your `/evals` page, and a stranger reads it. It is also the
rubric every later project in this course is measured against, so the habit matters more
than this assignment does.

## How you are graded

A hundred points across seven automated areas and three a human judges. The automated ones
are measured by `benchmark/bench.mjs` and `quality/check.mjs` against your deployed app;
`eval/rubric.json` is the authoritative list and what each row is worth.

Broadly: the UI lighting up against your contract, cited answers that are actually grounded,
memory that visibly crosses threads, RAG with page-level citations, deep search that is
genuinely deeper than quick, performance against the declared SLA, and observability good
enough that one request id explains an answer.

The three human rows are the ones automation structurally cannot do: whether a deep answer
is *better* or merely longer, whether you read one successful and one failing trajectory end
to end and learned something, and whether the thing actually deploys.

**Red lines** are automatic fails, listed in `eval/rubric.json`. The short version: no
fabricated citations, no `2xx` on an exception, no editing the provided folders, no secrets
reachable from the browser.

## How you submit

**One URL.** Your deployed app, with `/` working for a stranger and `/evals` rendering the
evaluation your run produced. No repo, no zip, no code — the running product and its own
evidence page are the submission. Course-wide rules are in
[`SUBMISSION.md`](../../../SUBMISSION.md); the exact flow and the deploy table are in
[`TECHNICAL.md`](TECHNICAL.md#submit).

## Where to go next

| You want | Read |
|---|---|
| To see it working before you read anything | [`README.md`](README.md) — start here, `npm run dev` |
| The exact wire format | `packages/contract/src/` — the schemas are the contract |
| Commands, architecture, checklists, troubleshooting | [`TECHNICAL.md`](TECHNICAL.md) |
| Every requirement, unabridged | [`SPEC.md`](SPEC.md) |
| The rules your coding agent must not break | [`AGENTS.md`](AGENTS.md) |
| What the numbers are | `benchmark/sla.json`, `expectations.json`, `eval/rubric.json` |
