# Product Evaluation — Moment Search at Scale

- **Student:** {{name}}
- **Date:** {{date}}
- **Video demo:** {{video_url}}
- **App target:** {{base_url}}
- **LLM / embedding provider:** {{provider_model}}
- **Queue:** {{prefect_or_own_broker}}

## Verdict

> {{one-paragraph honest verdict: does this ingest papers + decks alongside video and answer with grounded cross-source citations, without ingestion starving search? strongest part, weakest part.}}

**Rubric result (from `eval/REPORT.md`):** {{pass_count}} pass / {{total}} checks

## 1. Performance & scale (from `benchmark/bench.py`)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| `/admin/documents` accept p95 | {{accept_p95}} ms | ≤ 300 ms | {{}} |
| Search p95 during ingest ÷ idle | {{ratio}}× | ≤ 1.3× | {{}} |
| Cross-source recall@10 | {{recall}} | ≥ 0.70 | {{}} |
| Ingest throughput | {{throughput}} chunks/s | ≥ 8 | {{}} |
| No-loss under worker crash (`--resilience`) | {{yes/no}} | required | {{}} |

## 2. Live cross-source test

- **Sources ingested (not authored by student):** video `{{yt}}` · paper `{{arxiv}}` · deck `{{deck}}`
- **All reached `indexed`?** {{yes/no + how long}}
- **Async accept?** {{/admin/documents returned 202 before parsing}}
- **One query, multiple kinds?** {{query used; kinds returned}}
- **Locators deep-link correctly?** {{video→timestamp, paper→page, deck→slide}}
- **Grounding:** {{empty query returned empty? any invented locators?}}
- **Decoupling:** {{search latency while a backfill ran}}
- **Screenshots:** {{cross-source answer + queue view, or "attached to submission"}}

### Sample citations (one per kind)

| Kind | Locator | Snippet | Correct? |
|---|---|---|---|
| video | {{mm:ss}} | {{}} | {{}} |
| paper | p.{{n}} | {{}} | {{}} |
| deck | slide {{n}} | {{}} | {{}} |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Multi-format ingestion (paper + deck) | {{}} | {{}} |
| Correct locators (page / slide / timestamp) | {{}} | {{}} |
| One shared index | {{}} | {{}} |
| Cross-source recall vs SLA | {{}} | {{}} |
| Grounded answers (no invented locators) | {{}} | {{}} |
| Queue decoupling (search fast during ingest) | {{}} | {{}} |
| Resilience (no loss on crash) | {{}} | {{}} |
| Deploy (Fly.io, cross-source) | {{}} | {{}} |

## 4. Integrity check

- **Canary (course policy MS-3.14):** {{clean / TRIPPED — ROBOT_WAS_HERE.md or 🦥 commits found}}

## 5. Top fixes before shipping

1. {{}}
2. {{}}
3. {{}}
