# FDE Cohort 3 (2026-04): assignments

Graded projects for cohort 3 of the Forward Deployed Engineering Bootcamp. Each one is a
scaffold: the data, the contract, the guardrails, the grader and a viewer are provided; you
build the part the assignment teaches, then prove it with an evaluation from a real run.

New to how these are structured? Read [`START_HERE.md`](../START_HERE.md) once. How to hand
in: [`SUBMISSION.md`](../SUBMISSION.md). Every project except Sprint Zero is submitted as
**one Vercel URL** that carries all three deliverables: the deployed product (`/`), the
evaluation report your run produced (`/evals`), and a short demo video embedded on that page.

| # | Assignment | Modules | You build | Core skills |
|---|---|---|---|---|
| 1A | [**Ledger**: procurement audit planner](Assignment_1_Ledger/) | 1–2 | The harness: three skills, three sub-agents, a three-member agent team, one QA check, and your decisions at two human gates | Skills, sub-agents, human-in-the-loop gates, agent teams, least-privilege tools, deterministic guardrails, evals |
| 1B | [**Sprint Zero**: a sub-agent product team](Assignment_1_Sprint_Zero/) | 1–2 | A working app from a reference product of your choice: your scope, your review of the six generated specs, and a core loop that passes QA | Scoping, spec-driven builds, sub-agent orchestration, API contracts, browser QA |

**Sprint Zero is the exception.** It is open ended: you pick the product, and there is no
rubric, grader or eval skill. You submit a demo video and the six spec docs, with no Vercel
URL and no `/evals` page. The two sections below describe Ledger and the projects that
follow it.

Herald (Modules 3–4), Chorus (Module 5) and the Capstone (Module 6) land here as the course
reaches them.

## Module 3 notebooks

Two notebooks for Module 3, used in class. They are practice, not an assignment: nothing to hand in and nothing graded. Run them on Colab, or clone the repo and run the same code in VS Code.

**On Colab:** add `OPENAI_API_KEY` and `SERP_API_KEY` in Colab's **Secrets** panel (the key icon) and switch on notebook access for each.
**In VS Code:** use [`ReAct_vs_Router_py/`](ReAct_vs_Router_py/): the same code as `.py` files, with a README on setup (a `.env` file for the keys, one virtual environment per part).

| Notebook | VS Code | What you do |
|---|---|---|
| [ReAct vs Router 1: from scratch in Python](ReAct_vs_Router_1_Python.ipynb) · [Open in Colab](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/FDE-03-assignments/ReAct_vs_Router_1_Python.ipynb) | [`1_python/router_vs_react.py`](ReAct_vs_Router_py/1_python/router_vs_react.py) | Build three tools, a router and a ReAct loop by hand, run both on the same question, trace them in Phoenix, add a tool of your own, and score both on the same 12 questions |
| [ReAct vs Router 2: with ADK 2.0](ReAct_vs_Router_2_ADK.ipynb) · [Open in Colab](https://colab.research.google.com/github/hamzafarooq/multi-agent-course/blob/main/FDE-03-assignments/ReAct_vs_Router_2_ADK.ipynb) | [`2_adk/router_vs_react_adk.py`](ReAct_vs_Router_py/2_adk/router_vs_react_adk.py) | The same two designs in Google ADK (an `Agent` and a `Workflow`), traced in Phoenix, your tool added, and the same eval, compared with your notebook 1 scores |

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
