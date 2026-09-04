# Product Evaluation — Live Translate

- **Student:** {{name}}
- **Date:** {{date}}
- **Video demo:** {{video_url}}
- **LLM provider / model:** {{provider_model}}
- **Backend target:** {{gateway_url}}

## Verdict

> {{one-paragraph honest verdict: is this shippable to a real user? what's the strongest part, what's the weakest?}}

**Rubric score (from `eval/report.json`):** {{auto_score}} / {{auto_max}} auto (+ {{manual_max}} manual)

## 1. Performance & cost (from `benchmark/bench.py`)

| Metric | Result | SLA | Pass? |
|---|---|---|---|
| Cache hit p95 | {{hit_p95}} ms | ≤ 60 ms | {{}} |
| Cache miss p95 | {{miss_p95}} ms | ≤ 3500 ms | {{}} |
| Cache hit rate | {{hit_rate}} % | ≥ 60 % | {{}} |
| Throughput | {{rps}} req/s | ≥ 20 | {{}} |
| Error rate | {{err}} % | ≤ 1 % | {{}} |
| Cost per miss | ${{cost_per_miss}} | — | — |
| Monthly savings from cache | ${{savings}} | — | — |

## 2. Live-website test

- **Site tested:** {{url}}
- **Translated whole page?** {{yes/no + notes}}
- **Coverage gaps:** {{anything left in English}}
- **Cache on re-translate:** {{hit badge + latency observed}}
- **Resilience:** {{CSP/console errors/layout breakage; note if a strict-CSP site blocked injection}}
- **Screenshots:** {{before/after file refs or "attached to submission"}}

### Sample translations (6–8)

| Original (EN) | Translation (es-MX) | Numbers/prices/codes kept? | OK? |
|---|---|---|---|
| {{}} | {{}} | {{}} | {{}} |

## 3. Dimension scorecard

| Dimension | Pass / Partial / Fail | Evidence |
|---|---|---|
| Translation accuracy | {{}} | {{}} |
| Mexican-Spanish register (es-MX) | {{}} | {{}} |
| Numbers / prices / codes preserved | {{}} | {{}} |
| Page coverage | {{}} | {{}} |
| Cache effectiveness | {{}} | {{}} |
| Latency vs SLA | {{}} | {{}} |
| Error handling (no silent English) | {{}} | {{}} |
| Resilience on a real site | {{}} | {{}} |
| UX polish | {{}} | {{}} |

## 4. Top fixes before shipping

1. {{}}
2. {{}}
3. {{}}
