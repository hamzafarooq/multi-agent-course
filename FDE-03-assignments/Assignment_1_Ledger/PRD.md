# LEDGER: a procurement audit planner, built as a harness

*Assignment 1 · Forward Deployed Engineering Bootcamp, cohort 3 (2026-04) · Modules 1–2*

---

## What you are building

An internal auditor is about to plan a procurement audit of a real council. Today that means
reading a long rulebook, skimming years of committee papers, and pulling a small random sample
of payments without first looking at the whole population. It is slow, it varies by auditor, and
a random sample almost certainly misses the handful of payments that matter.

Ledger plans that audit from the council's public data. It reads the purchasing rulebook into
testable rules, analyses every payment against them, folds in past audit history, rates the risks
for the auditor to approve, and turns the approved risks into an audit planning pack: what to
test, which payments to pull, what to ask the council for. A team of agents then challenges and
checks the pack before the auditor signs it off.

It plans the audit. It does not perform it, and it reaches no findings. **Everything it produces
is a risk indicator to investigate, never an accusation.**

## The lesson

**A harness is the set of constraints that lets a model do judgment work you can trust.** Leave
it too loose and the model invents a threshold, paraphrases a quote, or does arithmetic in its
head, and the pack looks right and is wrong. Make it too tight and you have written a script that
cannot read a rulebook. The skill you are learning is the line between them: the model reads and
judges, code computes and checks, and a human decides.

You will build each kind of harness component once, on a real problem:

| Component | What it teaches |
|---|---|
| A **skill** you invoke yourself | A procedure in a file, versioned, watched, verified by code |
| **Sub-agents** | Isolated context for long, noisy work; files as the hand-off |
| A **skill loaded by an agent** | Separating the method from the job description |
| A **human gate** | The point where nothing proceeds without a person's decision |
| An **agent team** | Agents that argue and check each other, not just report |
| A **check you write** | Turning "it looks right" into a script that fails loudly |
| **Evals** | Proving each component, the team and the whole system, from a real run |

## The rules that decide your grade

- **Grounded or nothing.** Every quote is found word for word on its page. Every figure comes
  from a script that can be rerun. Every rating cites a rule, a metric or a past finding. Every
  sampled payment traces back to a verified rule and an approved risk.
- **Fail loud.** Missing or malformed input stops the run with a clear message. Nothing is
  guessed, patched or filled in from memory.
- **Bounded and honest.** Each agent has only the tools it needs and writes only its own file.
  Runs stay inside their declared budgets. The challenger cannot touch raw data; the checker
  cannot soften a failure.
- **Evidence over vibes.** Your evaluation comes from a real run, and the grader re-derives
  every number from your deployment. A number it cannot reproduce is fabricated, and
  fabrication is an automatic fail.
- **Indicators, not accusations.** Real council, real suppliers. Outputs describe patterns to
  investigate and controls to test. Supplier names are never published.

## What you get, and what you build

You get the data, the system brief, the file contract, the deterministic guardrails (the quote
verifiers, the register and pack builders, three of the four QA checks), the grader, and a
viewer site that renders whatever your run produces.

You build the harness: three skills, six agent definitions, the team lead's procedure, the
fourth QA check, and your own decisions at both human gates. Each piece is a numbered TODO with
its requirements in the SPEC and a provided tool that proves it.

## The five questions

Before you write a skill or an agent, answer these in `DESIGN.md`, in your own words. They are
graded, and they are the part of this assignment that transfers to every system you will build.

- **Components.** What are the pieces, and why is each a skill, a sub-agent or a teammate?
- **Responsibilities.** What is each one the only one allowed to do, and what is it forbidden?
- **Communication.** How do they hand work to each other, and what happens when an input is missing?
- **State.** What is authoritative, what is derived and rebuildable, and what is never evidence?
- **Trade-offs.** What did you give up, and which choice are you least sure of?

## How you are graded

Most of the grade is automated: arithmetic over your run, re-derived by the grader from your
deployed site. It covers whether the skill finds the right rules, whether every number is code's,
whether every rating and quote traces back, whether the gate held, whether the pack passes its
checks, whether your check catches planted mistakes, and whether the team actually worked as a
team. The rest is scored by a person: your design in your own words, two agent runs you read end
to end, your judgment as the auditor, and a short video.

## How you submit

Three things, all at one URL, your deployment on Vercel: the product (its front page shows
your audit pack), the evaluation report (its evaluation page: your scores, your design and
interview, a live test on rules the answer key does not cover, your two trajectories), and your
video, embedded on that page. No repository, no zip.

## Where to go next

[`README.md`](README.md) for the build in one screen, [`TECHNICAL.md`](TECHNICAL.md) to build,
[`SPEC.md`](SPEC.md) for exact requirements.
