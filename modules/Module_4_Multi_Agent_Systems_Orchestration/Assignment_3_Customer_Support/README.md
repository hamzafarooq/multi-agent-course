# Assignment 3: Customer Support

> Build a support desk for an online shop, from an empty folder, where you can see every
> decision the system makes. The hard part isn't the chatbot. It's the guards around it,
> and knowing when they're wrong.

## What this assignment is, in plain words

Imagine you run an online shop. Customers message your support desk: *"Where's my
keyboard?"*, *"Cancel my last order"*, *"Please leave packages at the back door."* You're
going to build the AI that answers them.

It answers from the shop's real database, so it can't make up an order status. It remembers
what each customer told it, so Diana doesn't have to repeat her delivery instructions next
week. And it's protected: every message passes a few guards before the AI sees it, and
another on the way out, so a customer can't trick it into leaking someone else's orders or
dropping the database.

You'll build it twice over the same core: first a terminal program, then a web page. Both
show every step as it happens, and every message leaves a trace you can read afterwards.

## Why it matters

The model is rarely what goes wrong in a support agent. The system around it is. When this
course's own reference version of this project was tested:

- Alice asked about someone else's order number and **got Bob's order**, his address and
  what he paid. The instructions said "only this user". The database query didn't.
- The safety check **refused a real customer** ("leave my packages at the back door") and
  **let a poem request through**.
- A layer meant to hide personal data was **quietly lowercasing every answer**, and no test
  noticed.

So you're graded on blocking attacks **and** on not blocking real customers. A guard
nobody has measured on both sides is a guess.

## What you'll learn

- How agents use tools through **MCP**, and why "who may see what" belongs in the tool, not
  the prompt.
- How agents call other agents through **A2A**, with a security service that runs on its own.
- How to make memory something the system does reliably, not something the model may forget
  to do.
- How to trace a multi-agent system, so "what happened?" always has an answer.
- How to tell whether a guard works, using numbers you commit to before you start.

## What you get, and what you build

**You get:** these Markdown files, a database seed and seven sets of test messages. That's
all. There's no starter code, no UI to fill in and no `501` skeleton. If you did LUMINA,
this one also has no Vercel deploy; it all runs on your machine.

**You build:** everything. The database, the tools, the support agent, three guards, the
personal-data masker, memory, tracing, the command-line app, the web app, and the program
that tests it all.

**Reading check:** so we know who reads the README, make the first line of your
`BUILD_LOG.md` exactly this sentence: *Alice never sees Bob's laptop.*

## How you'll work (and how you'll know what's happening)

You'll probably build this with a coding agent. That's allowed; the risk is a working
system you don't understand. So the build has **ten stages**, each working the same way:

1. **You decide** something the spec leaves open, before asking the agent for code.
2. **You build** that stage with your agent.
3. **You prove it** by running a check and reading the result yourself.
4. **You log it**: what you expected, what happened, and the evidence.

Your coding agent has been told (in `AGENTS.md`) to ask you the decisions, stop at every
check, and never write your log or design notes for you.

## Read in this order

| # | Read | Why | Time |
|---|---|---|---|
| 1 | This README | What you're building and why | 5 min |
| 2 | [`PRD.md`](PRD.md) | The product and the lesson, in full | 15 min |
| 3 | [`TECHNICAL.md`](TECHNICAL.md) | The build, stage by stage. Keep it open. | 20 min, then as you go |
| 4 | [`EVALS.md`](EVALS.md) | The database seed and the test messages | 10 min |
| 5 | [`THRESHOLDS.md`](THRESHOLDS.md) | Every number you'll be measured against, and why | 5 min |
| 6 | [`SUBMISSION.md`](SUBMISSION.md) | What to hand in | 3 min |

For your coding agent: [`SPEC.md`](SPEC.md), [`AGENTS.md`](AGENTS.md) and
[`CLAUDE.md`](CLAUDE.md). Skim them too, so you know what your agent has been told.

## Start here

1. Make an empty repo, and copy this folder's Markdown into it.
2. Copy `DESIGN.template.md` to `DESIGN.md`, and `BUILD_LOG.template.md` to `BUILD_LOG.md`.
3. Answer the five design questions in `DESIGN.md`. Rough answers are fine; you'll revise
   them.
4. Open `TECHNICAL.md` at stage 1, and tell your agent: *"We're on stage 1. Read AGENTS.md
   first."*

## Stuck?

`TECHNICAL.md` ends with Troubleshooting: the problems that cost the reference build the most
time. Check there first, then ask in the course channel with your trace id.
