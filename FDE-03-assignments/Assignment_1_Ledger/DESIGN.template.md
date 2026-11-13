# DESIGN.md: Ledger

> Copy this to `DESIGN.md` and answer the five questions **before you write a skill or an
> agent**, then revise it as the build teaches you. `eval/build_report.py` reads it by
> heading, so keep the five headings; everything under each is yours. It renders on your
> `/evals` page, where a person reads and grades it. A paragraph or a short list each,
> specific to the choices you actually made, not a restatement of the SPEC.
>
> Delete this block when you answer.

## Components

What are the pieces of your harness, and what kind of thing is each: a skill, a sub-agent,
a teammate, a script, a file, a human? For three of them, say why that kind and not
another. Why is the risk method a skill and not part of the risk-assessor's brief? Why is
the challenger a teammate and not a sub-agent?

## Responsibilities

For each component, what is it the ONLY one allowed to do? The interesting sentences are the
exclusions: which agent may run commands, which may only read summaries, which file each
one owns, which numbers no model may produce. Point at the tools lists you chose.

## Communication

How do the components talk: through files, through team messages, through the human?
Why files between the sub-agents and messages inside the team? What happens when a
component's input is missing or malformed, and who finds out?

## State

What is stored, where, and who owns it? Which state is authoritative (`outputs/`, the
auditor's decisions), which is derived and could be rebuilt (the register, the pack), and
which must never be treated as evidence (agent memory)? What does a re-run after the gate
change, and what must it leave alone?

## Trade-offs

Three or four decisions a reasonable engineer would have made differently, and what you
gave up. "The challenger cannot run Bash: it cannot verify a claim against the data itself,
so a challenge can only be as good as the summaries." Include at least one you are unsure about.
