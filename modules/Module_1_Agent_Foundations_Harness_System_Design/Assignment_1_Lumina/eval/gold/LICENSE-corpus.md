# Gold corpus licence and provenance

The four documents in `corpus/` were written for this course by the FDE Agent Engineering
Bootcamp staff and are released under **Creative Commons Attribution 4.0 International
(CC BY 4.0)**: https://creativecommons.org/licenses/by/4.0/

You may use, copy, adapt, and redistribute them, including commercially, with attribution.

**Why authored rather than borrowed.** The PRD floated arXiv papers as the corpus (open
question 8). Writing it instead buys three things a grader needs:

1. **A deterministic gold set.** Every fact has one home, so a recall@5 number means what
   it says. With third-party PDFs, a question is often answerable from two documents and
   "the retriever missed it" becomes an argument.
2. **Stable page numbers.** `build-corpus.mjs` renders the Markdown to PDF with a fixed
   paginator, so `p. 3` is `p. 3` on every machine, and `pages.json` records where each
   heading landed.
3. **No licence question.** arXiv papers carry per-paper licences, many of which are not
   CC, and a course corpus that cannot be redistributed is not a provided corpus.

The subject matter deliberately overlaps Module 3 (retrieval, re-ranking, hybrid search),
so the Space you build for LUMINA is worth keeping.

## Contents

| File | Subject |
|---|---|
| `corpus/retrieval-basics.md` | BM25, dense retrieval, hybrid search, RRF, chunking, recall@k |
| `corpus/vector-search-on-mongodb.md` | Atlas Vector Search, filters, eventual consistency, M0 limits |
| `corpus/agent-loops-and-failure.md` | the loop, caps, termination, silent fallbacks, grounding, traces |
| `corpus/streaming-and-latency.md` | SSE, buffering, TTFT, percentiles, 202 and decoupling |

PDFs are generated from the Markdown, not maintained separately:

    node eval/gold/build-corpus.mjs

Edit the Markdown, re-run it, and re-check any gold item whose `page` may have moved
(`pages.json` tells you).
