# What `report.json` has to contain

The schema of truth is `EvalsReport` in `packages/contract/src/report.ts`. The UI parses
with it and shows a schema error rather than rendering a report it does not trust. Build it
with `node eval/build-report.mjs`; this file is here so you can see the shape without
reading the zod.

```jsonc
{
  "assignment": "Assignment 1: LUMINA",
  "student": "Priya Nair",
  "repo": "https://github.com/…",           // optional; the code is not the submission
  "video": "https://youtu.be/…",            // 60–90 s, embedded on the page
  "deployedAt": "2026-09-19T18:02:11Z",
  "runNotes": "claude-sonnet-5 · tavily · Atlas M0",

  "design": {                                // the five questions, in the learner's words
    "components": "…", "responsibilities": "…", "communication": "…",
    "state": "…", "tradeoffs": "…"
  },

  "gates": [ { "gate": 0, "name": "STATIC", "status": "pass", "detail": "…" } ],

  "rubric": {
    "total": 100,
    "awarded": 79,                           // automated only; manual rows stay open
    "automated": [ { "id": "memory", "label": "Memory", "points": 10, "awarded": 10,
                     "status": "pass", "evidence": "✓ …", "rules": [] } ],
    "manual":    [ { "id": "deploy_docs", "points": 5, "awarded": 0, "status": "manual",
                     "evidence": "…", "rules": [] } ],
    "redLines":  [ { "check": "…", "ok": true, "detail": "…" } ]
  },

  "bench":   { /* reports/bench.json: sla rows, grounding, recall, cache, cost, pass */ },
  "quality": { /* reports/quality.json: rule-by-rule results, errors, warnings */ },

  "trajectories": {
    "successful": { "requestId": "req_…", "terminated": "done",
                    "steps": [ { "step": 1, "tool": "web_search", "ok": true, "ms": 812 } ],
                    "notes": "what reading it taught me" },
    "failing":    { "requestId": "req_…", "terminated": "error", "steps": [ … ], "notes": "…" }
  }
}
```

## The three fields a script cannot produce

Everything else is measured. These come from the student and nowhere else:

| Field | Why it cannot be generated |
|---|---|
| `design` | It is their design reasoning, written before the build, graded as their own words. |
| `trajectories.*.notes` | Rule P1 asks what a human learned from reading a run. A summary of the steps is not that. |
| `video` | Somebody has to point a screen recorder at the working product. |
