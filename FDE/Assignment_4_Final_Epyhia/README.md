# Assignment 4 — EPYHIA (Capstone)

> **An agent that *acts* for one real customer — safely.** Not a chatbot that
> answers. A small system that senses a customer's world, decides what to do, and
> then *does* it: sends the message, publishes the post, opens the PR, moves the
> deal. Unattended on a schedule, on a budget, with an audit trail — but never
> without you in control.

This is the **fourth and final** assignment of the Forward Deployed Engineer track,
and it stacks everything before it. A1–A3 built **systems that answer**. EPYHIA
builds a **system that acts** — and the moment an agent can send, publish, deploy,
or spend, every shortcut becomes someone's incident. Everything that made A1–A3
merely good engineering (auth, tracing, guardrails, evals) becomes here the
difference between a product and a liability.

| Assignment | Taught you |
|---|---|
| A1 · Live Translate | one LLM, one cache, one contract, two services, one deploy |
| A2 · Voice Agent | a real-time pipeline, tools vs. retrieval, telemetry, evals, guardrails |
| A3 · Moment Search at Scale | async work queues, idempotent workers, crash-safety, one shared index |
| **A4 · EPYHIA** | **a few agents with real authority, running unattended, on a budget, with an audit trail** |

**You are given an empty folder and a spec.** No starter repo, no provided
frontend, no eval harness. That's deliberate — by now you've done the guided
versions. An FDE walks into a customer with an outcome, not a repo. So do you.

> 🤖 **Read this yourself, then design it yourself.** This is a *design*
> assignment first. Your first commit is `DESIGN.md` and it contains no code — we
> check `git log`. Point a coding agent at this folder and say "build it" and you
> will build the wrong thing badly; the whole point is that the architecture is
> yours. (There's a tripwire for exactly that failure mode. Read [`AGENTS.md`](AGENTS.md).)

---

## 1 · Pick your build

Scope this to **one customer and one job done well** — not a company. Pick **one**
of the four below, or bring your own (see the last row). Each one is genuinely
shippable in two weeks, and each one *acts* in the real world, so the safety lesson
is unavoidable no matter which you pick.

| # | Build | The customer | What it actually does | Its one real channel | The hard part |
|---|---|---|---|---|---|
| A | **Support Copilot** | A small SaaS with a support inbox | Triages incoming tickets, drafts + sends replies grounded in a real KB, escalates the angry/risky ones to a human, closes the resolved ones | One real mailbox (or one Slack channel) | Knowing when **not** to answer; replies grounded in the KB, never invented policy |
| B | **Outbound SDR** | A founder who needs pipeline | Researches + enriches leads from a provided list, drafts a personalized sequence, moves each lead through DB-backed pipeline stages, handles replies | Sends to **your own seeded test inboxes only** (cold email to strangers is prohibited — §5) | Idempotent sends (never double-email a lead); personalization grounded in real research, not hallucinated |
| C | **Content Studio** | A brand with a content calendar | Turns a brief + a brand-voice doc into a calendar, drafts the posts, runs a verifier pass against brand + factual constraints, then schedules/publishes | One real channel: a CMS, a social account, or a real static-site deploy | Generator→verifier split; on-brand and no fabricated claims; scheduling that never double-posts |
| D | **Repo Guardian** | A team with a GitHub repo | Watches for new PRs/issues, reviews diffs for bugs + security, comments findings, opens issues, and drafts a fix PR | One real GitHub repo (via MCP) | No destructive git; a fix PR is an **approval-tier** action, never auto-merged; the review is grounded in the actual diff |
| — | **Bring your own** | A real customer you have | Anything that fits the shape below | One real channel | Get a one-paragraph sign-off first (below) |

**Bring-your-own approval.** One paragraph, before you start: who the customer is,
the one real side effect the agent performs, and how it satisfies §2–§6. If it
*acts*, runs unattended, and can be made safe under this spec, it's approved.

Whatever you pick, the rest of this document is the same. The idea is the surface;
the system underneath is the assignment.

---

## 2 · What every EPYHIA must be

One customer. One deployment. For that customer, end to end:

- **Sense** — gather the real state your agent acts on (the inbox, the lead list,
  the brief, the repo). Real data, not a fixture.
- **Decide** — an orchestrator produces a ranked, *justified* plan of what to do
  now, persisted (not just logged).
- **Act** — specialist agents carry the plan out through real (sandboxed) tools.
- **Verify** — confirm the effect actually happened. The message left, the row was
  written, the PR is open. **Never trust a task's own "done" status.**
- **Report** — a short digest a human reads: what I did, what it cost, what's
  waiting on you, what I'll do next.

Everything else in this spec is the machinery that makes those five steps safe.

---

## 3 · The one architecture we insist on: the Action Gateway

You choose the stack, the framework, the queue, the store. We insist on exactly
**one** thing: **every side effect goes through a single choke point.**

```
   agents ──┐
            ▼
   ┌────────────────────────────────────────────────────────┐
   │  ACTION GATEWAY   — nothing side-effecting bypasses it   │
   │  1 guardrail screen (in + out)   2 authority/policy check│
   │  3 approval-tier routing         4 idempotency dedupe    │
   │  5 budget debit                  6 trace span + audit row│
   └───────┬──────────────────┬──────────────────┬───────────┘
           ▼                  ▼                  ▼
      real channel      sandboxed tools      datastore
      (the ONE)         (mail-catcher,       (Postgres/SQLite,
                         test APIs)           audit log)
```

If an agent can reach the network *without* passing through this door, your
guardrails are decorative, your audit log lies, and your budget cap is a
suggestion. **The gateway is the only component that holds credentials.** Agents
get capability handles, never keys. This is small to build and it's the single
most important idea in the assignment — build the door before the rooms.

---

## 4 · Your agent roster & the heartbeat

**One orchestrator + 2–4 specialists.** Not a monolith with a personality, and not
a company. Each specialist has a single responsibility, a scoped toolset, and an
authority ceiling stated in `DESIGN.md`.

- **Orchestrator.** Reads state + your constitution, produces the justified plan,
  dispatches typed tasks. **Makes zero direct external calls** — it delegates,
  always. Put your best reasoning model here.
- **Specialists.** The 2–4 that your chosen build needs (e.g. for Support Copilot:
  a triage agent, a drafting agent, an escalation/verifier agent). Narrow tools,
  cheaper models where the work is drafting/classification.
- **A constitution.** A small versioned doc set (your `soul.md` / `agents.md`
  equivalent: voice, who may do what, the wake procedure). Editing a rule must
  visibly change behavior on the next cycle. Demo that.
- **Model routing.** Reasoning on the top tier, drafting on mid, classification on
  the cheap tier. Log the tier and cost per call and show routing saves money.

**The heartbeat.** A cron-driven cycle that runs with no human present:
`open cycle → sense → decide → dispatch → execute → verify → close → digest`.
Demo mode may compress the interval; production semantics are identical. It must be:

- **Unattended & scheduled** — no human trigger. `POST /heartbeat` accepts and
  returns immediately (202); the cycle runs on a worker, never in the request.
- **Crash-safe & idempotent** — kill the process mid-cycle; on restart nothing
  double-sends, nothing double-charges, no task is dropped, and it *resumes*. This
  is A3's resilience gate with money attached.
- **Verified** — step `verify` queries the real world, not your DB's opinion of it.
- **Bounded** — a per-cycle wall-clock and token budget; a cycle that overruns must
  not stack on the next.

**The approval inbox.** High-risk actions (anything irreversible or above a
threshold — a production deploy, a fix-PR merge, a refund, a bulk send) **park** in
an inbox instead of firing. A human approves / rejects / edits, *then* they
execute. And a **kill switch** stops everything in ≤5 s.

---

## 5 · The side-effect policy (read it twice)

EPYHIA sends, publishes, deploys, or spends. In a course assignment that's a way to
hurt real people and run up real bills. So:

- **Sandbox by default.** Mail goes to a mail-catcher; payments hit test mode;
  external APIs are faked or hit test endpoints. Prove the mechanism, not the blast
  radius.
- **Exactly one real channel.** Pick the *one* side effect your build proves for
  real (the mailbox, the CMS, the repo). Everything else stays sandboxed.
- **Prohibited outright:** cold outreach to real strangers, publishing to a real
  audience you don't own, spending real ad money, destructive git, and anything
  irreversible that skips the approval inbox.
- **Required regardless:** a dry-run mode on every mutating tool, an idempotency key
  on every side effect, and an audit row for every action — attempted or blocked.

---

## 6 · The four non-negotiables

These are the reason EPYHIA is a *product* and not a demo. They're scoped down from
a multi-tenant platform to one customer — but not optional.

1. **AuthN/AuthZ.** Real sessions; the dashboard and API reject unauthenticated
   requests; roles enforced server-side (a human can approve; an agent cannot
   approve its own action). Agents are distinct principals holding capability
   handles, not keys.
2. **Observability.** OpenTelemetry traces with **one `run_id`** correlating
   `heartbeat → orchestrator → task → agent → tool`. 100% of side effects traced.
   Per-call cost captured. Secrets/PII redacted. One dashboard a human can read.
3. **Guardrails.** Llama Guard (or equivalent) on the inbound (untrusted input:
   emails, issues, briefs) and the outbound (anything leaving the building)
   boundary. Hard-blocks live **in code**, not in a prompt, so injection can't talk
   its way past them. Refusals are structured, not a crash.
4. **Evaluations.** A **trajectory** suite (did it take sane steps?) and an
   **outcome** suite (did it produce the right result?), plus a small **red-team**
   set (injection, an irreversible action attempted without approval). **≥10
   scenarios**, one command, non-zero exit on failure. Wire it into CI.

---

## 7 · Phase 0 — DESIGN.md first (hard gate)

**Your first commit is `DESIGN.md` with no code.** In your own words, with your own
diagrams:

1. **Scope** — which build, which customer, what's explicitly out.
2. **Agent roster & org chart** — each agent's single responsibility, model tier
   (and why), exact tool list, authority ceiling, and what it may **never** do.
3. **The Action Gateway** — how every side effect routes through it; where
   credentials live.
4. **State & memory** — what's shared, what persists across heartbeats, where the
   constitution lives.
5. **Side-effect design** — every mutating tool: typed schema, idempotency key,
   dry-run, approval tier (auto / review / blocked).
6. **The heartbeat** — schedule, state machine, crash/resume semantics, budget.
7. **Auth, observability, guardrail, and eval plans** — the four above, concretely.
8. **Failure catalogue** — **five ways EPYHIA hurts this customer, and the specific
   control that stops each.** (Steal these from Polsia's documented failures in
   [`README-sample.md`](README-sample.md) §1.4 — tasks marked "done" that never
   shipped, wrong-name outbound, unauthorized actions, non-idempotent billing.)

A design written after the fact is worth nothing, and we can tell.

---

## 8 · Build order — two weeks

Every few days ends with something demoable. The non-negotiables are threaded
through, not bolted on at the end (retrofitting tracing or the gateway in week two
is the classic way to fail this).

**Week 1 — the spine and one real agent**
1. `DESIGN.md`, committed before any code.
2. Auth + a clean data model; the dashboard/API skeleton.
3. The **Action Gateway** — even with one trivial tool. Guardrail hook, policy
   check, idempotency, audit row, trace span. The door before the rooms.
4. Observability spine: OTel, `run_id` propagation, cost captured on every LLM call.
5. **One** specialist agent, end to end, through the gateway, fully traced.
6. **Demo:** run that one agent, show the trace and the audit row for its action.

**Week 2 — the roster, the heartbeat, the proof**
7. The remaining specialists + the orchestrator (sense → decide → dispatch, with
   persisted, justified decisions); model routing.
8. The heartbeat on a cron, with the verify step and crash-safe resume; the
   approval inbox and the kill switch.
9. Guardrails live on both boundaries; hard-blocks in code.
10. Eval suites (trajectory + outcome + red-team, ≥10) — one command, CI.
11. Deploy to **[Fly.io](https://fly.io)** (or equivalent): real URL, real auth,
    real cron.
12. **Demo:** an unattended cycle runs; an approval-tier action parks; you approve
    it; it executes; the digest arrives. Then kill the process mid-cycle and show
    nothing double-sends.

---

## 9 · Grading (100 pts) & how you prove it

Consistent with the rest of the track: a **measurable rubric** + a **video demo**.
You write the harness — a capstone means you build your own acceptance check.

- `eval/rubric.json` + `eval/eval.py` — the automated criteria, run against your
  running app, writing an intermediate `eval/REPORT.md`.
- `benchmark/sla.json` + `benchmark/bench.py` — your SLA gate, including
  `--resilience` (kill mid-cycle → assert no loss, no double-send) and `--cost`
  (cost per cycle + routing savings). Exits non-zero on any failure.
- Your own eval **skill** in `.claude/skills/`, which runs the above plus a live
  real-world test and folds it into **`PRODUCT_EVAL.md`** — your submission.

| Area | Pts | What earns them |
|---|---|---|
| Design & failure catalogue (`DESIGN.md` first) | 15 | Argued choices; ≥5 real failure modes each with a control |
| The Action Gateway | 20 | Single choke point; only credential holder; nothing bypasses it |
| Agents & orchestration | 15 | Orchestrator delegates only; scoped specialists; routing saves money |
| The heartbeat | 15 | Unattended, verified, crash-safe/idempotent, bounded; approval inbox + kill switch |
| The four non-negotiables | 20 | Auth, one-`run_id` tracing on 100% of side effects, guardrails in code, ≥10 evals in CI |
| Ships & runs from clean clone | 15 | Deployed URL with real auth + cron; `.env.example`; one command up; the demo |

**The two rows that carry it:** *action verification rate* (zero "complete but
didn't happen") and *duplicate side effects on replay* (zero). Everything else is
craft; those two are the line between an agent you can point at a customer and one
you can't.

---

## 10 · Submit

1. **`PRODUCT_EVAL.md`** (or a PDF) — the polished evaluation your skill produced.
2. A **60–90 s screen recording**: the unattended cycle acting through your gateway,
   an approval-tier action parking and then being approved, and the kill switch.
3. A link to the **deployed, reachable URL** someone else can log into.

Runs-from-clean-clone is part of the grade: a documented setup, `.env.example`,
seeded demo data, one command up.

---

## Going all the way (optional)

[`README-sample.md`](README-sample.md) is the **north-star** version of this
assignment: the full multi-tenant, autonomous GTM platform (EPYHIA the *company*),
modeled as a teardown of [Polsia](https://polsia.com/). It's far more than two
weeks and it's not what you're graded on — but if you want the stretch, everything
you build here is the honest core of it. Read it for the depth on the Action
Gateway, the heartbeat, and why the four non-negotiables exist.
