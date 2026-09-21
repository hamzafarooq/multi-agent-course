# Stage 3: the numbers (write these before any prose)

Three JSON files hold every number in the assignment. Prose references them and never
restates them as truth. Write them now, with a reason per row, then copy the quality kit.
How those numbers get *proven* is the next stage (`04-evals.md`); this stage only declares them.

## `benchmark/sla.json`

```jsonc
{
  "_comment": "Targets declared BEFORE the first run, plus the cost model bench reads. Do not loosen the gates to pass. PRICES ARE PLACEHOLDERS.",
  "target": "http://localhost:8787",
  "user_id": "bench",
  "sla": {
    "ttft_p95_ms": 2500,            // one row per measurable target, snake_case, unit in the name
    "answer_p95_ms": 12000,
    "accept_202_p95_ms": 300,
    "min_citation_grounding": 0.95,
    "max_error_rate_pct": 1.0,
    "max_cost_per_answer_usd": 0.05
  },
  "_sla_notes": { "ttft_p95_ms": "the 'it's thinking' window a user tolerates", ... },
  "cost_model": { "llm_provider": "anthropic", "llm_model": "claude-sonnet-5", "input_usd_per_mtok": 3.0,
                  "output_usd_per_mtok": 15.0, "embedding_model": "text-embedding-3-small",
                  "embedding_usd_per_mtok": 0.02, "search_usd_per_call": 0.008,
                  "monthly_answer_volume": 100000 },
  "workload": { ... what the bench runs: counts, repeat fraction, concurrency ... }
}
```

Rules for choosing a target: pick it from the user's tolerance or the economics, write the
reason in `_sla_notes`, and never from what a first build would score. Include **at least one
row that measures the lesson directly** and cannot be talked around. LUMINA's, for example, is
`min_deep_source_ratio: 2.0`, "the same question, both gears; deep that reads no more is only
slower". Per-mode latency and cost are reported per mode, never blended: "averaging the two
gears together is exactly how a slow quick search hides behind a fast deep one".

## `expectations.json` (the quality kit's schema, read by `quality/check.mjs`)

```jsonc
{
  "$comment": "<CODENAME>. Declared BEFORE the first run. Asserted by arithmetic via quality/check.mjs.",
  "project": "<CODENAME>",
  "quality": { "rules": true, "budget": true },
  "budget": { "maxTokensPerRun": 180000, "maxToolCalls": 24, "maxWallClockSec": 240, "maxCostUsd": 0.35 },
  "trajectory": { "mustCallTools": [], "mustNotCallTools": [], "maxConsecutiveSameTool": 4, "mustTerminate": true },
  "eval": { "goldSetPath": "eval/gold/<name>.jsonl", "minCitationGrounding": 0.95, "minRecallAt5": 0.70,
            "minRetrievalRate": 1.0, "maxErrorRate": 0.01 }
}
```

`check.mjs` applies **one** budget to every run, so the budget is the widest legitimate
envelope; tighter per-mode envelopes are the bench's job (it can read the mode off the run).
Say so in a `$budget_comment`. Ratios must be in 0..1 and budgets positive or rule C1 fails
the file itself.

## `eval/rubric.json`

```jsonc
{
  "_comment": "Measurable rubric for Assignment <K>: <CODENAME>. automated = scored by eval/eval.mjs against the deployment; manual = a grader with evidence + the video. Total = 100.",
  "assignment": "Assignment <K>: <CODENAME>",
  "total_points": 100,
  "automated": [ { "id": "snake_id", "label": "...", "points": 10, "rules": ["C1"], "check": "one sentence a script can assert, naming the metric or route" } ],
  "manual":    [ { "id": "...", "label": "... (human half)", "points": 5, "rules": ["E3","P1"], "check": "what a person judges and why a model may not" } ],
  "stretch_bonus": [ { "id": "new_rule_with_precedent", "points": 5, "check": "a new rule submitted to the cohort rules.json: one executable sentence, a real incident as precedent, a self-check question" } ],
  "red_lines": [ "no secret reachable from the deployed app", "provided folders unmodified", "no fabricated citation (E2)",
                 "no 2xx on a provider exception (A1)", "no capped run reported as done (A2)", "<the lesson's red line>",
                 "the design section on /evals answers the five questions in the learner's own words" ]
}
```

Split: automated about 80, manual about 20, exactly 100 before bonus. The lesson gets an
automated row **and** a manual row ("better, not merely longer"). Always keep the three
manual rows automation cannot do: the lesson's human half, the human gate (P1: one
successful and one failing trajectory read end to end), deploy and docs. Keep the
`new_rule_with_precedent` bonus in every assignment: "it is the actual job".

Every `rules` entry must exist in `quality/rules.json`. Available ids: C1 contract coherence
· A1 tool errors surface · A2 terminates because done · A3 no thrash · R1 required tools ·
R2 forbidden tools · E1 gold set exists · E2 thresholds met · E3 judge may report, never
block · B1 tokens · B2 latency · B3 cost · P1 human read a trajectory · P2 rules cite precedents.

## `quality/`

Copy `check.mjs`, `rules.json` and `expectations.example.json` from LUMINA verbatim. The rules
file is cohort case law: append only, never renumber. **Do not invent precedents.** A1's
precedent is real (Live Translate, cohort 2026-01: a dependency mismatch made every LLM call
throw, the handler returned the input untouched, the translator served English for weeks and
was found by a person reading output). The `TODO` ones stay `TODO`; P2 warns until the cohort
fills them, and that nag is intentional.

## Two rule-interaction traps (check every assignment for both)

1. **A rule that requires evidence another rule forbids.** P1 wants a failing trajectory kept;
   A2 fails any run in `runs/` not terminated `done`. Resolution: deliberate failures live in
   `runs/failing/`, which the trajectory rules do not read and the report builder does.
   Neither rule is weakened. Write this into `AGENTS.md`.
2. **A global rule where the behaviour is conditional.** `mustNotCallTools` is one list, but a
   tool may be forbidden only in one mode. Leave the list empty, say why in the JSON, and
   assert the conditional version in the bench where the per-run context exists. Declaring it
   globally would fail every legitimate run; declaring nothing and checking nothing is worse.

## Checklist

- [ ] Every `sla` row has a note explaining why that number.
- [ ] One row measures the lesson directly, per mode, unblended.
- [ ] `expectations.json` passes C1 by inspection: budgets positive, ratios 0..1, gold path declared.
- [ ] Rubric sums to 100; every rule id exists in `rules.json`; three manual rows; bonus kept.
- [ ] Red lines include the lesson's own red line.
- [ ] Both traps checked; `runs/failing/` convention stated.
- [ ] `quality/` copied verbatim, no precedent invented.
