# PRODUCT_EVAL.md: the shape

`python eval/build_report.py` renders `reports/PRODUCT_EVAL.md` from `reports/report.json`, and
`viewer/collect.mjs` publishes it at `/evals/PRODUCT_EVAL.md`. **Nobody writes or edits it by
hand**: every number in it comes from the run. This page documents the sections so a student
knows what the grader will read. It follows the FDE product-evaluation shape (Verdict,
measurements, live test, scorecard, integrity, top fixes).

| Section | Source in report.json | What it says |
|---|---|---|
| Header | `student`, `generatedAt`, `url`, `video` | Who, when, where, the video link |
| Verdict | `score`, `bars`, `system.verdict`, `gate.signoff`, `red_lines` | Automated score, bars met, QA verdict, signed off, any red-line flag |
| 1. The declared bars | `bars` | Each bar in `benchmark/sla.json`: this run vs the target |
| 2. Live test | `live_test` (from `live-test.md`) | Five or more rules from clauses the answer key does NOT cover, checked by the student against the PDF |
| 3. Rubric scorecard | `rubric` | Every row: points, awarded, status, evidence; self-reported rows marked; manual rows "for the grader" |
| 4. Pipeline, planted errors, golden thread | `system.gates`, `system.planted_errors`, `system.golden_thread` | Every gate, seven plants, every sampled payment traced |
| 5. Integrity and red lines | `red_lines`, `integrity` | What this run can say about each red line, and who decides |
| 6. Design and the interview | `design` (from `DESIGN.md`, `design-interview.md`) | Whether the five headings are answered; the interview answers, verbatim |
| 7. Trajectories | `trajectories` (from `trajectories.md`) | The two runs chosen; full steps and notes are on `/evals` |
| 8. Top fixes | `rubric.automated` | The first three rows not at full marks, with their evidence |
