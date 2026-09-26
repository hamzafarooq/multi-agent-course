# Customer Support: a multi-agent support desk you can see inside

*Assignment 3 · FDE Agent Engineering Bootcamp, cohort 2026-03 · Module 4, due end of Week 5 · Owner: Hamza Farooq*

> **Read this one.** It is the product and the lesson, in about fifteen minutes. The
> exhaustive version, with every event, span name and failure mode, is [`SPEC.md`](SPEC.md),
> written for a coding agent. You will want it open while you build; you don't need it to
> start.
>
> **No thresholds appear in this document.** They live in [`THRESHOLDS.md`](THRESHOLDS.md),
> and that file is the only place they are true. A number restated in prose is a number that
> will be wrong by the second week.

---

## What you are building

A support desk for an online shop. A customer logs in and asks about their orders: where
something is, what they paid, whether a return went through. They can ask to cancel or
return something, and they can tell it how they like deliveries handled. It answers from the
shop's real database, and it remembers what they told it the next time they come back.

Before the support agent ever sees a message, the message passes a line of guards: a cheap
local check, a Security Judge that runs as its own service, and a Guardrail that asks
whether this is something a shop's support desk should handle. On the way out, a Data
Masker strips personal data. Every one of those steps, and every tool call and model call,
shows up in a single trace you can open and read.

You build it twice over the same core: first as a command-line program, then as a web page
that shows each step as it happens. No starter code. You get these documents, a database
seed and a set of test messages. Everything else is yours.

## The lesson: every guard has two sides

Anyone can make a guard stricter. The skill is knowing what it costs.

On one side, a guard that is too lax. The course's reference build told the agent "only this
user's orders", yet when Alice asked about an order number that wasn't hers, she got Bob's
gaming laptop, address and price: the prompt said one thing, the database query another, and
the query won. It also told the agent to "always" check memory. Sometimes it didn't.

On the other side, a guard that is too strict. The same build's Guardrail refused "please
leave my packages at the back door" as personal chit-chat, and let "write me a poem about
the stock market" straight through. It had been copied from a generic safety template that
didn't know what the agent was for. And every guard that calls a model adds seconds, so a
pipeline of them can make the cheapest question slow.

So the assignment measures both sides of every guard. You'll run a set of attacks and a set
of real customer messages written to trip a lazy guard: apostrophes, the words "drop" and
"select", "ignore my last message". You are graded on blocking the first set **and** on not
blocking the second. The rule underneath it: anything that must always happen is enforced
in code, and the model only decides what is genuinely a judgement.

## What it can do

| | What it means | Where it comes back |
|---|---|---|
| **Tools over `MCP`** | The database is reached only through declared tools. Which customer's orders a tool may return is decided in the tool, not by the model. | The capstone |
| **Guard services over `A2A`** | The Security Judge and the Data Masker are separate agents your pipeline calls, the way a security team's checks would be shared across products. | The capstone |
| **A calibrated Guardrail** | A check that knows what this shop's desk is for, measured on attacks and on real customers. | Voice agents; the capstone |
| **Memory as a step** | The system, not the model, recalls what matters before each answer and saves what the customer said after it. | Voice agents; the capstone |
| **One trace per message** | Every layer, tool and model call, in one tree you can read. | Every project from here on |

## How you'll build it, and how you'll know what's happening

*"I told my coding agent to do everything and I don't know what's happening"* is the most
common thing students say. So the build has ten stages, each with four parts: **you decide**
something the spec leaves open, **you build** it with your agent, **you prove it** by reading
the output yourself, and **you log** what you predicted and what happened. Your agent is told
to ask you the decisions, stop at every check, and never write your log for you.

And from the fifth stage on, the system answers the question itself: every message leaves a
trace of every step it took. Read the trace, not the reply.

## The rules that decide your grade

**Grounded or nothing.** An order fact in a reply comes from a tool call in that same turn:
not from memory, not from the model's guess.

**Fail loud.** A guard that can't be reached, or answers something you can't parse, stops the
turn with an error the customer and the trace both see. It never quietly lets the message
through. The course learned this from Live Translate, a project in an earlier cohort whose
error handler returned the input untouched when every translation call was failing. It served
untranslated English for weeks, and it was found by a person reading the output, not by a
test. The reference build for this assignment made the same mistake with its Guardrail.

**Bounded and honest.** A turn has limits on tool calls, tokens and time. Hitting one ends
the turn and says so; it doesn't pretend to have finished.

**Evidence over vibes.** Every number you report comes from your own eval runner, run
against targets declared before you started.

Plus the assignment's own red lines: no key in the repo, no tool that can change an order,
no customer ever seeing another customer's data, and no guard that fails open in silence.

## What you get and what you build

```
 you get:   README  PRD  SPEC  AGENTS  CLAUDE  TECHNICAL  THRESHOLDS  EVALS  SUBMISSION  templates
 you build: database · tools · support agent · Sanitizer · Judge service · Guardrail
            · Masker service · memory · tracing · CLI · web UI · eval runner · run script
```

**Why the guards are split the way they are.** The Judge and the Masker are owned by
"security": the same checks for every product, versioned and audited on their own, so they
are services any agent can call. The Guardrail encodes what *this* product is for and
changes whenever the product does, so it lives next to the product. Where a check runs
follows who owns its definition.

**Why one pipeline under two front ends.** The command line and the web page are two views
of the same run. If logic lives in either one, they drift, and you'll fix a bug in one and
demo the other.

**The stack.** The taught path is Python with Google's Agent Development Kit, the `MCP`
Toolbox for Databases, `A2A`, `Mem0` for memory and Arize Phoenix for traces. They're the
protocols this module teaches, and they share one runtime. What is graded is the event
stream, the trace shape and your measured numbers. Another stack is your call to make and
your risk to carry.

## Answer these before you write code

Copy the design template and answer its five questions: components, responsibilities,
communication, state, trade-offs. The one that matters most here is responsibilities: for
every rule in the spec, is it enforced in code, in a prompt, or both, and why?

## How you are graded

A hundred points: most of them computed by the eval runner you write, the rest judged by a
person.

Broadly, the runner checks:
- that answers about orders are right and came from the tools;
- that no customer can see another's data, however they ask;
- that attacks are blocked;
- that real customers are **not** blocked;
- that off-topic requests are turned away;
- that planted memories come back when they're relevant;
- that every message is one complete trace;
- that the command line and web page emit the same events in the same order;
- that the cheap path stays fast.

A person reads three things:
- your design document and build log, in your own words;
- your enforcement map, with one false block and one false pass you found in your own build
  and what you did about them;
- one successful and one failing turn you read end to end, plus a short video.

Any red line caps the grade, whatever else you scored.

## How you submit

A repo link, your eval report, and a video walking through the five scenarios in the spec.
The details are in [`SUBMISSION.md`](SUBMISSION.md).

## Where to go next

| When you want | Read |
|---|---|
| The build, stage by stage | [`TECHNICAL.md`](TECHNICAL.md) |
| Every requirement, event and span | [`SPEC.md`](SPEC.md) |
| Every number | [`THRESHOLDS.md`](THRESHOLDS.md) |
| The test messages and the database seed | [`EVALS.md`](EVALS.md) |
| What your coding agent has been told | [`AGENTS.md`](AGENTS.md) |
