# DESIGN.md — ARGUS

> Copy this to `DESIGN.md` and answer it **before you write the paper and deck pipelines**.
> It is graded, and it renders as the design section of your `/evals` page — a stranger reads it.
>
> Keep the six headings; everything under each is yours. A paragraph each is right. Be specific
> to the choices *you* made: "page-aware chunks, 800 tokens, split on section boundaries because
> the survey's related-work section is one 4-page wall" is an answer. "Chunk the PDF sensibly"
> is not.
>
> **The spec fixes what must be true. This document is where you decide how.** Where they
> disagree, the spec wins — change your design, not the contract. Don't restate requirements
> here; you get no points for repeating the README back.
>
> At submission, `/fde-momentsearch-scaled-eval` interviews you against this file and records
> what you say. Answers that don't survive contact with what you shipped are the point of that
> step, not an accident — if you changed your mind while building, say so here or say so there.
>
> Delete this block when you answer.

---

## 1. Chunking — one strategy per source type, or one for all?

A 40-minute talk, a 30-page paper and a 60-slide deck are three different shapes of knowledge.
A talk chunk is bounded by who's speaking and when they stop; a paper chunk is bounded by
sections and page edges; a slide is already a chunk, and mostly image.

What did you choose for papers, and for decks? What is the unit, how big, and what do you split
on? Where does your strategy break — the two-column paper, the scanned PDF, the slide that's a
single diagram with four words on it? Name the failure you know you have.

## 2. Retrieval — how do three source types share one index?

They land in one hybrid index. That's the requirement. The interesting part is what that does
to ranking.

Does a query retrieve from all sources equally, or do you weight, filter or route? A dense
question about a concept and a lookup of a specific number are not the same query — do you
treat them the same? When a paper chunk and a video moment both match, what breaks the tie, and
is that the *right* tie-breaker or just the default one? If you did nothing here, say so and say
why nothing was the right call.

## 3. Enrichment — what do you spend an LLM call on during ingestion?

The video pipeline enriches before embedding. You decide what the document pipelines do.

What does a paper or a slide get — a summary, generated questions, an image caption, nothing?
Justify it in terms of what it buys at *query* time, then say what it costs per 100 sources. An
enrichment that doubles ingestion cost and moves recall by nothing is a decision you should be
able to defend or drop.

## 4. Grounding — how do you know a citation is real?

Every locator must point at something that exists: a real page, a real slide, a real timestamp.
The model must never invent a page number.

What structurally prevents that in your system? Not "the prompt says not to" — what makes it
impossible, or at least detectable? How does a page number survive parse → chunk → embed →
retrieve → render without drifting by one? How would you *catch* a drifted citation before a
user does?

## 5. Cost and caching — what do you cache, and what must never be cached?

ARGUS reports spend per 100 sources with and without the cache. That number is a design
outcome, not a measurement you take at the end.

What do you cache — embeddings, parsed documents, enrichment output, answers? What's the key?
What can't be cached and why? If you cached answers: what happens when a new source is indexed
that would have changed one of them? (That question has more than one defensible answer. Pick
one and own it.)

## 6. Trade-offs and what you'd do with another week

Three or four decisions a reasonable engineer would have made differently, and what you gave up
by choosing as you did. Include at least one you're still unsure about, and one thing that is
currently worse than you'd ship to a customer.

Then: the next thing you'd build, and why that one before the others.
