---
name: fde-assignment
description: Break a one-line problem or product idea ("build a Perplexity clone", "a voice receptionist for a clinic") into a complete specification pack a coding agent can build from and be graded against - declared thresholds in JSON, a contract, an exhaustive SPEC.md, AGENTS.md, TECHNICAL.md, a short PRD.md with no numbers, README.md, DESIGN.template.md, a rubric, and the scaffold plan. Use when a learner or instructor wants to turn a problem into a spec, write an assignment or capstone brief, scaffold a project for an agent to build, or asks how a spec like LUMINA's is derived.
---

# Problem to spec pack

**Premise: problem solving with AI is as good as the spec you write.** A coding agent builds
what you can state precisely and nothing you cannot. A long prompt describes a gate; a spec
pack runs one. This skill breaks a one-line problem into that pack through seven moves, each a
question put to the problem before the next is asked. The detail is what falls out when the
questions are asked in the right order.

The house pattern was extracted from LUMINA
(`modules/Module_1_Agent_Foundations_Harness_System_Design/Assignment_1_Lumina/`). Use it as the
worked example for voice and file shapes, not as a template to copy: a different problem gives
different answers to the same questions. `references/00-how-lumina-happened.md` shows each
move done once, for real.

## Two ways to run it

- **Learner mode (default).** The learner brings a problem. You interview, they think, you write
  what they decided in their words. Socratic: one question at a time, no solutions volunteered,
  push back on vague answers ("what would a stranger *see*?"). Honor the teaching style in
  `progress/learner-progress.md` if one is recorded.
- **Instructor mode** (`--generate`, or the user is clearly authoring for a cohort). Ask the
  open decisions once in one message (codename, module slot and due date, taught stack, whether
  a UI is provided, points split), take defaults for the rest, produce the full folder.

Both modes go through the same seven moves and end at the same lint.

## The seven moves

| # | Move | The question that drives it | Reference |
|---|---|---|---|
| 1 | **Deconstruct** | What does a stranger open and use? Where does a naive build fail on *both* sides? What returns later? What gets cut? | `references/01-deconstruct.md` |
| 2 | **Contract** | If the UI already existed, what exactly would it call, and in what order would events arrive? | `references/02-contract.md` |
| 3 | **Numbers** | What number would prove this worked, declared before the first run, per mode, with a reason? | `references/03-gates.md` |
| 4 | **Evals & QA** | What *measures* each number, against what gold set, under which rules with which precedents, in what order do gates run, and what may only a person judge? | `references/04-evals.md` |
| 5 | **Documents** | Who reads which file, and what does each reader need that the others do not? | `references/05-documents.md` |
| 6 | **Scaffold** | What has to exist so day one is "run it and click", not "read fourteen thousand words"? | `references/06-scaffold.md` |
| 7 | **Lint** | `node .claude/skills/fde-assignment/scripts/lint-assignment.mjs <dir>` | script |

**Move 1 ends in a one-page shape. Stop there and get it approved.** Everything after it is
derivation; deriving eight thousand words from a wrong shape is the expensive mistake. Once the
shape is approved, run moves 2 through 7 without pausing.

## Order matters: numbers first, README last

Write `sla.json`, `expectations.json` and `rubric.json` before any prose. Then `SPEC.md`
(quotes them under a header saying the JSON wins), `AGENTS.md`, `TECHNICAL.md`,
`DESIGN.template.md`, `PRD.md` (no digits at all), `README.md` last. The README depends on
everything; writing it first is how prose drifts from the truth.

## The disciplines

1. **One lesson.** Every problem has one judgement a naive build gets wrong on both sides. Name it
   first; it decides what gets cut and where the points go.
2. **Numbers live in exactly one place.** JSON. Prose references, never restates. The lint checks the PRD.
3. **Declared before the first run.** A threshold set after seeing a score is a description.
4. **Grade the contract, not the stack.** Graders speak HTTP and read JSON. `/health` names what is
   live as free strings. Helper scripts are labelled `CONVENIENCE, not a gate`.
5. **Arithmetic, never a judge.** Every gate compares against a declared number. A model may report
   at warn; it may never block. Manual rows are the few things only a person can judge.
6. **Every rule cites its failure.** Use the house precedents in `quality/rules.json` or leave
   `TODO`. Never invent an incident.
7. **Two readers.** A human wants fifteen minutes and the why; a coding agent wants every status
   code once, explicitly. One document cannot serve both, so there are six.
8. **The UI is the acceptance test.** Ship `501` skeletons so day one is clicking, not reading.
9. **Run the grader against a stub before anyone sees it.** It will be wrong the first time.

## Output and finish

Learner mode: write into the folder the learner names, never inside a course assignment folder.
Instructor mode: `modules/<Module>/Assignment_<K>_<Codename>/`. Finish with the reading ladder
(real word counts), the lint result, and the staff build list from move 6 with what is still
`⬜ To build`. In learner mode also update `progress/learner-progress.md`: the problem, the
lesson they found, where they stopped.
