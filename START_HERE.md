# Start here

Read this once, before your first assignment. It applies to LUMINA, ARGUS, VOXA and EPYHIA
alike, and it answers the three questions everyone hits in week one: *which of these files do
I actually read, what am I supposed to decide for myself, and how do I start the build with
Claude Code?*

Every project in this course ships the same set of files. They look redundant. They aren't —
each one exists because a different reader needs it, and two of those readers are not you.

---

## The files, and who reads them

| File | Who reads it | What it is |
|---|---|---|
| `README.md` | **You**, first | The map. What you're building, in what order, and how you prove it. Start here, always. |
| `PRD.md` | **You**, second | What the product *is* and the rules that decide your grade. Product, not implementation. |
| `TECHNICAL.md` | **You**, while building | The build guide — architecture, commands, checklists, the failures that cost people days. |
| `DESIGN.template.md` | **You**, before writing code | Copy to `DESIGN.md` and answer it. This is the part that is genuinely yours. It is graded. |
| `AGENTS.md` | **Your coding agent** | The non-negotiables. Short, blunt, written for a machine. |
| `SPEC.md` | **Your coding agent** | Every requirement stated explicitly, so an agent can build without guessing. |

You *can* read `SPEC.md` and `AGENTS.md` — nothing is hidden. But they are written to be
unambiguous rather than readable. If you're trying to understand the assignment, the README
and the PRD are the ones written for a human.

## The one rule that resolves every conflict

**`SPEC.md` is the contract. `DESIGN.md` is your reasoning about how you'll satisfy it.**

Where they disagree, the SPEC wins — and your DESIGN should change. You are never expected to
invent requirements that the SPEC already fixes, and you are never graded for restating them.
The SPEC says *what must be true*. Your design says *how you'll make it true, and what you gave
up to do it.*

So: your `DESIGN.md` does **not** need to be complete enough for an agent to build from. That's
the SPEC's job. Yours is the thinking — the parts a spec can't fix for you.

## What's actually yours to decide

The scaffolding is deliberately heavy. Contracts, gates and budgets are fixed so that everyone
is graded on the same thing. What's left open is the part that transfers:

- **Which components exist, and what each is the only one allowed to do.**
- **How they talk, and what happens to an in-flight request when one is down.**
- **What state is authoritative and what is a cache you could delete.**
- **The trade-offs** — decisions a reasonable engineer would have made differently.

If you find yourself agonising over a choice the SPEC already made, stop and re-read the SPEC.
If you find yourself with no choices at all, you're probably not looking at the design layer yet.

---

## Driving a coding agent through the build

This course assumes you build with Claude Code. If you haven't used it to write real code
before, do one of the [`Starter_Projects/`](Starter_Projects/README.md) first — a couple of
hours there will save you a day here.

The loop that works:

**1. Read it yourself before the agent does.** Skim the README and the PRD with your own eyes.
You cannot supervise a build you don't understand, and every one of these assignments is a
reading assignment first.

**2. Point the agent at its files, not yours.**

```
Read AGENTS.md and SPEC.md. Then read the contract in packages/contract/ (or src/).
Summarise what I'm building in ten lines, and list anything the spec leaves undecided.
```

That last clause is the useful one. What comes back is your design surface.

**3. Write DESIGN.md by argument, not dictation.** Use the agent as a sparring partner — the
`grill-me` skill exists for exactly this. Make it interrogate your choices before you commit to
them. Write the answers in your own words; a design doc that reads like generated text is
graded as one.

**4. Build one vertical slice at a time.** Not "implement the backend". One route, one tool,
one pipeline stage — then run it. The README's build order is sequenced so each step is
provable on its own.

**5. Run the gates constantly, not at the end.**

```bash
node eval/eval.mjs       # or the assignment's equivalent
```

The gates are not a final exam. They're your feedback loop, and they're the same ones the
grader runs.

**6. When something tiny looks arbitrary, ask why.** The nine rules in
[`modules/Module_1_Agent_Foundations_Harness_System_Design/reference/harness-principles.md`](modules/Module_1_Agent_Foundations_Harness_System_Design/reference/harness-principles.md)
cover most of them. Instructions like *"flush after every
token"* are small on purpose and load-bearing anyway — that one is the difference between a
streaming product and a batch one wearing a streaming costume. If a rule looks pointless, ask
your agent to explain what breaks without it. That question is where most of the learning in
this course actually lives.

## What "done" means

Done is not "it runs." Done is: the gates pass against your **deployed** app, the numbers on
your `/evals` page came from a real run, and you can explain every decision on the page without
looking anything up.

See [`SUBMISSION.md`](SUBMISSION.md) for what you hand in.

---

## If you're stuck at the start

That feeling of *"I've read all the files and still don't know where to put my hands"* is
common, and it's usually one of three things:

| It feels like | It's actually | Do this |
|---|---|---|
| "I don't know this stack" | A tooling gap, not a design gap | Run the app first, break it, read the provided code for the *one* path that already works end to end. Mirror it. |
| "I don't know what my design should say" | You're trying to write the SPEC again | Re-read the section above. Design = components, responsibilities, communication, state, trade-offs. |
| "I don't know how to start with the agent" | No entry command | Use the prompt in step 2 above, verbatim. |

Still stuck after an hour: ask in the cohort channel with what you tried. That's what it's for.
