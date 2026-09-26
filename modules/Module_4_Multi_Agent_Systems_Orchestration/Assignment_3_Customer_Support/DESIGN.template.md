# DESIGN

> Copy this file to `DESIGN.md` and answer it **before you write code**. Revise it as you
> learn, but keep the first version in git history. A stranger grades it (`G-DESIGN`), so
> write for someone who has never seen your code. The five headings are fixed; keep them.

## Components

What are the moving parts, and which of them are separate processes? Name each one and its
port. Why are the Judge and Masker separate services while the Guardrail runs in-process?
Answer in your own words, not SPEC's.

## Responsibilities

Which component decides that a customer may only see their own orders, and where exactly is
that line of code or SQL? Which component may hold an API key? Which one decides a turn is
over budget? For every rule in SPEC §11, say whether it is enforced **in code**, **in a
prompt**, or **both**, and why. This table is the core of `G-ENFORCE`.

## Communication

How does a message travel from the CLI or browser to the database and back? Name each hop's
protocol (function call, MCP, A2A JSON-RPC, HTTP, NDJSON). Which A2A method did you
implement, and what does a verdict look like on the wire?

## State

What is stored, where, and for how long: sessions, memories, traces, run logs, the action
log? Which of them contain customer data, and who can read each one? What happens to
memory when a customer's order changes after the memory was saved?

## Trade-offs

What did each guard cost you in latency (from your traces), and was it worth it? Did you
make the Guardrail fail closed, and what does that cost when Gemini is slow? If you changed
`T-MEM-MINSCORE` or argued against any threshold, give the evidence here, and keep the
original gate in your report.
