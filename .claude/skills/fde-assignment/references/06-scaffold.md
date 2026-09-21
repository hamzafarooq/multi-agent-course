# Stage 6: the scaffold plan (what staff must build before students see it)

The documents describe a scaffold. Until it exists, a student following the README hits
missing directories (LUMINA's first draft listed six provided components and none existed).
This stage does not build the scaffold; it writes the exact list, in build order, into the
final summary and into SPEC §15's status column as `⬜ To build`.

## The provided set, in the order to build it

| # | Component | Path | Why in this order |
|---|---|---|---|
| 1 | Workspace scaffold: root `package.json` with workspaces, `npm run dev`, `docker-compose.yml`, `.env.example`, lint + typecheck config | repo root | everything else installs into it |
| 2 | Contract package: schemas + types for every route, event and collection in SPEC §7-8 | `packages/contract/` | UI, skeletons and bench all import it |
| 3 | `501` skeletons for both services, `/health` live, everything else `501` | `backend/gateway/`, `backend/agent/` | makes README step 1 true on day zero |
| 4 | The UI, importing the contract types, every panel wired, `/evals` page rendering `report.json` | `web/` | the acceptance test |
| 5 | Index / setup scripts, labelled `CONVENIENCE, not a gate` | `scripts/` | Mongo-only helpers, not graded |
| 6 | Gold set + corpus + validator, at least 30 items (rule E1) | `eval/gold/` | the bench needs it before it can measure recall |
| 7 | Bench reading `sla.json`, zero dependencies, speaks HTTP only, per-mode reporting, writes `reports/bench.json` and `reports/eval.json` with the metric names `check.mjs` reads | `benchmark/bench.mjs` | the SLA gate |
| 8 | Gate runner (six gates in order, stops at first failure) and report builder (assembles `report.json` from `reports/`, refuses a smoke run, exits non-zero on a red line) | `eval/eval.mjs`, `eval/build-report.mjs` | the grader |
| 9 | Quality kit copy | `quality/` | already done in stage 3 |
| 10 | The eval skill `/fde-<codename>-eval` | `.claude/skills/fde-<codename>-eval/SKILL.md` | turns a run into the `/evals` page |

## The eval skill

Copy LUMINA's `.claude/skills/fde-lumina-eval/SKILL.md` and adapt: the gate command, the two
manual rows (one is always the lesson's human half, one is P1), the video shot list, and the
"Do not" list naming this assignment's two lesson-guarding thresholds ("if they fail, the fix
is the planner, not the number"). Keep the one rule: **never write a number a run did not
produce.**

## Grader hygiene (from LUMINA's retrofit)

- The bench, the gate runner and `check.mjs` import no database driver and no web framework.
- Gate 0 tolerates a missing `lint` / `typecheck` script rather than failing a project built outside the workspace.
- Grounding is verified against the real page or chunk, normalized, requiring a run of about
  twelve consecutive tokens; a page the bench cannot fetch makes a citation *unverifiable*,
  excluded and reported, never counted as wrong. A dangling `[n]` is a fabrication and fatal.
- Per-mode percentiles and cost, never blended.
- **Run the grader against a throwaway stub backend before a student sees it, and keep the
  stub out of the repo** (it is an answer key). LUMINA's grader had eight bugs until it was
  run, two of which would have failed every correct submission.

## Deliverable of this stage

A "Staff build list" section in the final summary: the ten rows above with `✅ Built`,
`✅ Written` or `⬜ To build`, and the sentence "the grader has not been run against a stub"
until it has.
