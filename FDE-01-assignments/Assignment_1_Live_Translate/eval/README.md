# Eval — how your submission is scored

Every FDE project is graded against a **measurable rubric**. You generate the
evidence yourself and submit a **Product Evaluation** report **alongside your video demo**.

> **Do this:** run the **`/fde-live-translate-eval`** skill (in `.claude/skills/`).
> It runs everything below *plus* a live-website test on a real site (e.g.
> homedepot.com) and writes **`PRODUCT_EVAL.md`** (PDF optional) at the assignment
> root — **that is what you submit.** The steps below are what the skill runs under
> the hood; run them directly only if you want to score the rubric without the skill.

## Score the rubric (the scorecard)

With both services running and your backend built:

```bash
python eval/eval.py --student "Your Name" --video "https://…"
```

This writes, next to this file:

- **`REPORT.md`** — human-readable scored rubric + captured evidence. This is the
  **intermediate scorecard** the skill folds into `PRODUCT_EVAL.md`. Read it to see
  where you stand and fix any Fail/Partial dimensions.
- **`report.json`** — the same data, machine-readable.

## How scoring works

- **`auto` criteria** (70 pts) are scored right here by running your backend:
  contract shapes, cache behavior + persistence, the SLA benchmark, logging/observability,
  status codes. See `rubric.json` for the exact checks.
- **`manual` criteria** (30 pts) — Mexican-Spanish quality and deploy/docs — are scored by
  the grader using the evidence the report captures (sample translations, cost/latency numbers)
  plus your video.

The report also flags red lines automatically: committed secrets, or any edits to
the **provided** `widget/`, `extension/`, or `benchmark/` files (you shouldn't touch them).

## Submit

1. **`PRODUCT_EVAL.md`** (or the PDF) — the report the `/fde-live-translate-eval` skill
   writes at the assignment root. Not `REPORT.md` — that's the intermediate scorecard it's built from.
2. A 60–90s screen recording: fresh page → widget translating live → whole-page translate → a cache hit shown in the badges.

> This eval/report pattern is the FDE-track standard — every future assignment ships its own `eval/` with a rubric and this same `eval.py` flow.
