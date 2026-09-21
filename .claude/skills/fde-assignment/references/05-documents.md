# Stage 5: the six documents, written in dependency order

Write `SPEC.md` first (it quotes the JSON), then `AGENTS.md` (a compression of the SPEC's
non-negotiables), then `TECHNICAL.md`, `DESIGN.template.md`, `PRD.md`, and `README.md` last.
The README depends on everything; writing it first is how prose drifts.

Before writing, read LUMINA's `PRD.md` and `AGENTS.md` in full for the voice: short declarative
rules, a "why" for every "what", precedents told as stories with a date and a cost, tables for
anything with three or more parallel items, no hedging.

| File | Audience | Budget | Job |
|---|---|---|---|
| `SPEC.md` | coding agent | as long as it needs (LUMINA 8,600) | every requirement, status code, shape and failure mode, stated once |
| `AGENTS.md` | coding agent, always loaded | ~1,300 | non-negotiables; what may and may not be edited; reading order |
| `TECHNICAL.md` | human, open while building | ~4,000 | architecture, commands, build order, what gates measure, checklists, deploy table, troubleshooting |
| `DESIGN.template.md` | human, before code | ~300 | the five questions with a prompt under each heading |
| `PRD.md` | human, read once | <= 1,500, **no digits** | the product, the lesson, the four rules, how graded, how submitted |
| `README.md` | human, first 3 minutes | <= 800 | run it; the reading ladder; provided vs yours; the build in one screen; pointers |

## `SPEC.md`

Header, verbatim shape (the lint checks for these three sentences):

```markdown
> **This is the exhaustive specification, written to be read by a coding agent.** It is
> deliberately dense: every requirement, status code, threshold and failure mode is stated
> once, explicitly, so an agent working from it cannot quietly skip one.
>
> **If you are a human, read [`PRD.md`](PRD.md) first** ... use the section numbers: ...
>
> **No number in here is authoritative.** Thresholds live in `benchmark/sla.json`,
> `expectations.json` and `eval/rubric.json`; the wire format lives in
> `packages/contract/`. Where this document and one of those disagree, they win and this
> document is stale — say so.
```

Then the metadata table (Project, Track, Kicks off, Owner, Status, Stack, Lives in,
Replaces), the one-line, the lesson as a blockquote, and the numbered sections:

1 Problem · 2 Goals · 3 Non-goals · 4 Users & scenarios · 5 Requirements (Must/Should/Could
tables, one subsection per capability, the lesson's subsection says where its points live) ·
6 Architecture (diagram, why the stack, why the split, the async pattern) · 7 API contract ·
8 Data model · 9 Performance, SLA & cost (table: metric, target, why) · 10 Observability ·
11 Non-negotiables (becomes `AGENTS.md`) · 12 Grading (table with rule ids, red lines, bonus) ·
13 Quality bar (four laws, declared expectations, run-log shape, the six gates, "read the
trajectory, not the answer") · 14 Build order by week · 15 Provided vs built · 16 Risks &
assumptions (table: risk, mitigation) · 17 Open questions (with owners) · 18 Stretch goals ·
19 Submission.

Every Must row is later a rubric `check` or a bench assertion. If a Must cannot be asserted
by arithmetic, it is a Should, or it is the manual row.

## `AGENTS.md`

Open with "You are helping a student complete Assignment K: CODENAME. This file is the
contract you must satisfy. Do not relax, reinterpret, or 'improve' these requirements."
Then the **reading-order paragraph** (SPEC is for you; contract outranks prose; TECHNICAL is
the build guide; README and PRD for intent, never for numbers; JSON beats prose on numbers,
"if prose disagrees, say so rather than following it").

Sections: What you may and may not touch (BUILD folders; **DO NOT EDIT** folders, "editing
them is a red line and it is checked"; the `runs/failing/` rule; DESIGN before code) · Hard
requirements grouped as in SPEC §5 plus Contract, Grounding, Observability, Hygiene,
Evidence. Bullets, imperative, one idea each. Caps and status codes may be quoted here; this
file is for the machine.

## `TECHNICAL.md`

Header block naming the other files and the "no number here is authoritative" sentence.
Sections: Architecture (ASCII diagram with PROVIDED / YOU labels; why the split; why one
store) · What's provided vs what you build (table with paths) · The API contract, the rules
that matter (bullets, link to SPEC §7) · Build it: recommended order (Part 0 scaffold commands,
Part 1 agent service numbered steps, Part 2 gateway, Part 3 see it live, Part 4 ship it with
the **deploy table** and the deploy commands) · Performance, SLA & cost (table + bench
commands + how grounding is verified + where a failing run lives) · Requirements checklist ·
Definition of Done with a **self-verify block** of curl commands, numbered · Grading table
with a **sample scorecard** ("illustrative only; fabricating numbers is an automatic fail") ·
Stretch goals · Submit (the eval skill command, the video shot list, "no repo, no zip, no
code") · Troubleshooting (the failures that cost the most time, each as symptom -> cause -> fix).

The deploy table is the same in every assignment:

| Piece | Host | Fixed? |
|---|---|---|
| The UI | **Vercel**, this URL is the submission | Yes |
| Public API / gateway | Anywhere reachable | Your choice |
| Anything holding provider keys or enforcing a cap | Anywhere **not** publicly reachable | Your choice, but not public |
| Database | Per assignment | Per assignment |

## `DESIGN.template.md`

The five headings are fixed because the report builder parses by heading: Components ·
Responsibilities · Communication · State · Trade-offs. Under each, two to four sentences of
prompt specific to this assignment ("Which component may hold a provider key? Which decides a
request is over its cap?"). Header block tells them to copy to `DESIGN.md`, answer before
opening an editor, and that a stranger grades it.

## `PRD.md`

Title, byline in italics (assignment, cohort, week, due, owner: the one place digits are
allowed), then the header quote: "Read this one ... The exhaustive version is SPEC.md ...
**No thresholds appear in this document.** They live in ... A number restated in prose is a
number that will be wrong by Week 2."

Sections: What you are building · The lesson (its own section, with the failure on each
side) · The capabilities table (what it means, where it comes back) · The rules that decide
your grade (the four, with the Live Translate story under Fail loud) · What you get and what
you build (ASCII split, why two services, why one database, the stack paragraph) · The five
questions · How you are graded (in words: "a hundred points across seven automated areas and
three a human judges", then "broadly:" one sentence per row, then the manual rows, then red
lines) · How you submit · Where to go next (table).

Write numbers as words or drop them. `[n]`, `2xx`, `501`, `502` are allowed only inside
backticks. Ordered lists use `1.` markers, which the lint ignores. Run the lint; each
surviving digit needs a reason or a rewrite.

## `README.md`

Order is fixed: title and a two-sentence blockquote · "You are given X. You build Y. When your
backend works, the UI lights up. That's the whole game." · **Start here** (three shell lines,
then "click everything; every panel says `501 not implemented yet`, which is correct: that
message is your progress bar") · **Then read, in this order** (table: #, Read, Why, with
minutes; row 0 is `START_HERE.md`; agents' files named at the end) · **What you build**
(provided / yours table by folder; the DO NOT EDIT sentence) · **The build, in one screen**
(numbered, each a TECHNICAL section) · **How you prove it** (three commands) · **How you
submit** (one URL; the eval skill; link to TECHNICAL#submit and SUBMISSION.md) · **Stuck?**
(one paragraph naming the troubleshooting entries).

Nothing above the run commands except the blockquote. No architecture prose: "a student who
has clicked the 501 panels already understands the architecture better than a paragraph would
have taught them."

## Cross-document rules

- Relative links and `#anchors` must resolve; the lint checks file links.
- Deep references point at `SPEC.md §n`; entry points (module README, course README) point at `PRD.md`.
- The eval skill is named `/fde-<codename>-eval` everywhere.
- Word counts go in the final summary as the reading ladder: README -> PRD -> TECHNICAL -> AGENTS -> SPEC.
