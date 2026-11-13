# FDE Cohort 3 (2026-04): assignments

Graded projects for cohort 3 of the Forward Deployed Engineering Bootcamp. Each one is a
scaffold: the data, the contract, the guardrails, the grader and a viewer are provided; you
build the part the assignment teaches, then prove it with an evaluation from a real run.

New to how these are structured? Read [`START_HERE.md`](../START_HERE.md) once. How to hand
in: [`SUBMISSION.md`](../SUBMISSION.md). Every project is submitted as **one Vercel URL** that
carries all three deliverables: the deployed product (`/`), the evaluation report your run
produced (`/evals`), and a short demo video embedded on that page.

| # | Assignment | Modules | You build | Core skills |
|---|---|---|---|---|
| 1 | [**Ledger**: procurement audit planner](Assignment_1_Ledger/) | 1–2 | The harness: three skills, three sub-agents, a three-member agent team, one QA check, and your decisions at two human gates | Skills, sub-agents, human-in-the-loop gates, agent teams, least-privilege tools, deterministic guardrails, evals |

Herald (Modules 3–4), Chorus (Module 5) and the Capstone (Module 6) land here as the course
reaches them.

## How every assignment is graded

- **A measurable rubric** (`eval/rubric.json`): about eighty points scored by arithmetic over
  your run, twenty by a person (your design and the interview on it, the trajectories you read,
  the video).
- **A live test on something you did not build for**: rules the answer key does not cover,
  checked by you against the source.
- **Bars declared before you run** (`benchmark/sla.json`, `expectations.json`). They never move.
- **The URL proves itself.** The grader re-derives your numbers from your deployment. A number
  it cannot reproduce is fabricated, and that is an automatic fail.
- **Feedback cites rule IDs, then evidence.** See the quality bar in the course
  [README](../README.md#the-quality-bar-how-work-is-judged-and-how-to-give-feedback).

## How to work through one

1. Read the assignment's `README.md`, then its `PRD.md`.
2. Copy `DESIGN.template.md` to `DESIGN.md` and answer it before you build.
3. Build one TODO at a time; prove each with the tool its stub names.
4. Run the evaluation constantly, not at the end.
5. Deploy, run the assignment's eval skill, and submit the URL.
