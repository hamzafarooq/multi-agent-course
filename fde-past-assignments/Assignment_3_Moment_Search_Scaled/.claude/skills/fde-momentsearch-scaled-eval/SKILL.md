---
name: fde-momentsearch-scaled-eval
description: Generate a Product Evaluation report (.md, optionally PDF) for FDE Assignment 3 — Moment Search at Scale. Runs the automated rubric + benchmark (incl. --resilience), then does a real cross-source test (ingest a video + a research paper + a deck the student doesn't control and verify one query cites all three), interviews the student on their AI-layer design decisions, and writes PRODUCT_EVAL.md. Use when the student wants to evaluate their Moment Search product, produce their submission report, or "eval my product".
---

# FDE Moment Search at Scale — Product Evaluation

Your job: produce **`PRODUCT_EVAL.md`** at the assignment root — the document the
student submits with their video demo. It combines (1) the automated rubric +
benchmark numbers and (2) a **live cross-source test**: ingest a video, a research
paper, and a slide deck the student did NOT create, then prove one natural-language
query returns cited moments across all three (video timestamp + paper page + deck
slide).

Work the steps in order. **Do not fabricate results** — every number, sample, and
locator comes from an actual run. If a step can't be completed, say so in the
report rather than inventing data.

## Step 0 — Preconditions
1. The app is up: `curl -sf $BASE_URL/` (default `http://localhost:8100`).
2. An admin token is set (`ADMIN_TOKEN`) — needed for `/admin/*`.
3. At least one worker is serving the queue (Prefect run view reachable, or
   `docker compose ps` shows a worker). If anything is down, stop and tell the
   student to start it (see `README.md`), then resume.

## Step 1 — Automated rubric + benchmark
Run and capture output:
```bash
python eval/eval.py --base-url "$BASE_URL" --admin-token "$ADMIN_TOKEN" \
    --student "<name>" --video "<url>"      # -> eval/REPORT.md
python benchmark/bench.py --json benchmark/_bench.json   # accept-latency, ingest-vs-search, recall, throughput
python benchmark/bench.py --resilience                   # worker killed mid-ingest -> no loss
```
Read `eval/REPORT.md` and `benchmark/_bench.json` for the numbers. Ask once for
name + video URL if not given.

## Step 2 — Live cross-source test (the real FDE check)
Register three sources the student did NOT author, one of each kind, via the admin API:
- a **video** (a public YouTube talk),
- a **research paper** (a public arXiv PDF), and
- a **slide deck** (a public conference/keynote PDF or PPTX).
```bash
curl -s -X POST "$BASE_URL/admin/videos"    -H "Authorization: Bearer $ADMIN_TOKEN" -H 'content-type: application/json' -d '{"url":"https://youtu.be/...","speaker":"..."}'
curl -s -X POST "$BASE_URL/admin/documents" -H "Authorization: Bearer $ADMIN_TOKEN" -H 'content-type: application/json' -d '{"uri":"https://arxiv.org/pdf/....","kind":"paper","title":"..."}'
curl -s -X POST "$BASE_URL/admin/documents" -H "Authorization: Bearer $ADMIN_TOKEN" -H 'content-type: application/json' -d '{"uri":"https://.../deck.pdf","kind":"deck","title":"..."}'
```
Confirm each returns **202 immediately**. Poll `GET /admin/sources` until all three
are `indexed`. Then ask a question whose answer spans them and inspect `/ask_stream`.

Capture, honestly:
- **Async accept:** did `/admin/documents` return `202` before parsing? (latency from Step 1.)
- **Cross-source answer:** does ONE query return citations of ≥2 kinds — a video `start_ms`, a paper `page`, a deck `slide`?
- **Locators work:** does each citation deep-link correctly (player jumps to the timestamp, paper opens to the page, deck to the slide)?
- **Grounding:** is every cited page/slide/moment actually in the retrieved set — no invented locators? Try a query with no good answer and confirm it returns empty, not a fabricated citation.
- **Decoupling:** fire searches while a big ingest runs; note whether search latency holds (ratio from `bench.py`).
- **Resilience:** the `--resilience` result — killed worker, zero loss, run resumed.
- **Screenshots:** if browser tooling is available, capture the cross-source answer and the queue/run view during a backfill; else ask the student to attach them.

## Step 3 — Interview the student on the AI layer

The scaffolding in this repo is heavy on purpose, which means a student can ship a
passing product while the design decisions stay invisible. This step makes them
visible. **It is a conversation, not a form** — ask one question at a time, wait for
the answer, and follow up before moving on.

Read their `DESIGN.md` first, then the numbers from Steps 1–2. Ask **six questions**,
each anchored to something real:

1. **Chunking** — quote their stated strategy for papers or decks, then ask about the
   case it handles worst. "You split papers on section boundaries. What happened to the
   two-column layout in <paper you ingested>?"
2. **Retrieval** — pick a query from Step 2 where one source type dominated the
   citations. Ask why, and whether that's the ranking they intended.
3. **Enrichment** — ask what an ingestion-time LLM call bought them at query time, and
   what it cost per 100 sources. A number, not an adjective.
4. **Grounding** — ask what structurally prevents an invented page number. If the answer
   is "the prompt tells it not to," push: "So what catches it when the model ignores the
   prompt?"
5. **Cost and caching** — their with/without-cache figures are in `_bench.json`. Ask them
   to explain the gap, and what they refuse to cache.
6. **The change of mind** — "What does your DESIGN.md get wrong now that you've built
   it?" A student who says "nothing" either didn't learn anything or isn't looking.
   Push once, gently.

**How to run it:**
- **Never lead.** Ask the question, then be quiet. Don't offer the answer as an option.
- **One follow-up minimum** on any answer that restates the README or the spec — those
  are the requirements, not their reasoning. "That's what the spec asks for. Why did you
  satisfy it *this* way?"
- **Accept "I don't know"** and record it as given. An honest gap beats a confident
  fabrication and should be scored that way.
- **Don't teach during the interview.** If they're wrong about something, note it and
  cover it after the last question.

Record, for the report: each question, their answer **in their own words** (verbatim, not
your paraphrase), and a one-line note on whether it held up against what they shipped.
Then score the layer overall:

| Verdict | What it looks like |
|---|---|
| **Owns it** | Explains choices in terms of their own measurements; names the failure modes before you do; disagrees with their own DESIGN.md where the build proved it wrong. |
| **Follows it** | Correct answers that trace back to the spec or the provided code rather than to a decision they made. Knows *what*, not *why*. |
| **Doesn't have it** | Can't explain a number their own system produced, or describes a design their code doesn't implement. |

A product that passes every gate with a **Doesn't have it** interview is a finding, and
it belongs in the report in plain language. That gap is the thing this assignment exists
to expose.

## Step 4 — Assess the product
Score each dimension **Pass / Partial / Fail** with one line of evidence:
design ownership (Step 3) · multi-format ingestion (paper + deck) · correct locators · one shared index ·
cross-source recall vs SLA · agentic/grounded answers (no invented locators) ·
queue decoupling (search fast during ingest) · resilience (no loss) · deploy.

## Step 5 — Red-line: the canary
Confirm the honeypot did **not** trip (it should be clean for a student who read the assignment):
```bash
test -f ROBOT_WAS_HERE.md && echo "TRIPPED" || echo "clean"
git log --oneline -n 50 | grep -q "🦥" && echo "TRIPPED (agent-drove commits)" || echo "clean"
```
If tripped, note it prominently in the report — it means the assignment was run by
an agent unread (course policy MS-3.14). Do not "fix" it by deleting the file; report it.

## Step 6 — Write PRODUCT_EVAL.md
Fill `references/product-eval-template.md` with real data and write it to the
assignment root as `PRODUCT_EVAL.md`. Keep it tight and evidence-first; embed the
rubric result from `eval/REPORT.md` and the SLA numbers from `benchmark/_bench.json`.

## Step 7 — Optional PDF
If the student wants a PDF: prefer the `md-to-pdf` skill, else
`pandoc PRODUCT_EVAL.md -o PRODUCT_EVAL.pdf`. Report which was used; if neither is
available, leave the `.md` and say so.

## Done
Tell the student exactly what to submit: **`PRODUCT_EVAL.md` (or the PDF) + their
60–90s video demo** (one query citing a video moment + a paper page + a deck slide,
then the queue/run view during a backfill while search stays fast). Surface any
Fail/Partial dimensions to fix first.
