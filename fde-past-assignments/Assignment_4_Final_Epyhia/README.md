# Assignment 4 — EPYHIA (Capstone)

> **Your one-person AI agency.** A customer walks in with a business idea. Your
> system walks out with the business's *front* — a live website, the marketing to
> launch it, and a working way to take money. Not a deck, not a mockup: a real URL,
> real copy, and a checkout that takes a (test) card and writes the order to a
> database. End to end, built by you.

This is the **fourth and final** assignment of the Forward Deployed Engineer track,
and it stacks everything before it:

- **A1–A3 built systems that _answer_.**
- **EPYHIA builds a system that _acts_** — it deploys a site, publishes copy, and
  stands up a payment path.

The moment an agent can *ship* and *charge*, "it looked fine in the demo" stops
being good enough.

> **That gap — between a slick demo and something you'd hand a paying customer — is
> the whole assignment.**

| Assignment | Taught you |
|---|---|
| A1 · Live Translate | one LLM, one cache, one contract, two services, one deploy |
| A2 · Voice Agent | a real-time pipeline, tools vs. retrieval, telemetry, evals |
| A3 · Moment Search at Scale | async work queues, idempotent workers, crash-safety |
| **A4 · EPYHIA** | **a crew of agents that plans, builds, markets, and monetizes one real business** |

**You are given an empty folder and this spec.** No starter repo, no provided
frontend. An FDE walks into a customer with an outcome, not a scaffold. So do you.

> 🤖 **Read this yourself, then design it yourself.** Your first commit is
> `DESIGN.md` and it contains no code — we check `git log`. Point a coding agent at
> this folder and say "build it" and you'll ship the wrong thing well; the point is
> that the *architecture* is yours. (There's a tripwire for exactly that — see
> [`AGENTS.md`](AGENTS.md).)

---

## 1 · What your agency ships

For **one** business, your system takes a plain-language brief and produces three
things, all real:

| Deliverable | What "real" means | Not acceptable |
|---|---|---|
| **A live website** | Deployed, on a real URL, on-brand, that someone else can open | A local-only mockup, a screenshot, a generic AI landing page |
| **A marketing pack** | Landing copy + 3–5 social posts + a launch email + a short **launch video** with a vertical social cut, in a consistent brand voice, factually grounded in the brief | Lorem ipsum, hallucinated features/prices, off-brand filler, a "video" that's just a static image |
| **A working checkout** | Stripe **test-mode** payment wired into the site; a completed test purchase fires a webhook and writes an order row to a real DB | A "Buy" button that goes nowhere; a fake success screen with no persistence |

The bar is **"a real brand paid for this,"** not "an AI made this." Generic hero +
three feature cards + a gradient is the slop you're being graded against. Techniques
like **[scroll-world](https://github.com/oso95/scroll-world)** (a skill that turns a
brand into a scrollable 3D world) are the kind of thing that clears that bar — use
it, or clear it your own way, but clear it.

---

## 2 · Pick the business (or bring one)

Same system every time — you're choosing the **customer**, not a different project.
Pick one to demo on, or bring a real one you have:

- ☕ A subscription **coffee brand** (monthly bags, recurring checkout)
- 🐕 A niche **B2B SaaS** (e.g. scheduling for dog-walkers) with a paid plan
- 🥐 A local **bakery** taking preorders for pickup
- 📰 A **paid newsletter** or a cohort **course** with a checkout
- 🎯 **Bring your own** — a real business you'd actually stand up

The idea is the surface. The crew that builds it is the assignment.

---

## 2.5 · Examples worth studying (steal techniques, don't clone)

Real projects that clear the "not slop" bar for pieces of what you're building.
Study how they're built; **do not** point an agent at one and copy it — your
architecture is the graded part.

| Project | Use it for | Why it's not slop |
|---|---|---|
| **[scroll-world](https://github.com/oso95/scroll-world)** | The **website** | Turns a brand into a scroll-driven 3D world (Apple-style), not a gradient hero |
| **[rampstackco/claude-skills](https://github.com/rampstackco/claude-skills)** | **Web Builder + Marketer** | Skills spanning the full website lifecycle — brand, design, content, SEO, dev, growth |
| **[OpenClaudia/openclaudia-skills](https://github.com/OpenClaudia/openclaudia-skills)** | The **Marketer** | 34 focused marketing skills — SEO, content, email, ads, analytics, growth |
| **[ucsandman/marketing-studio](https://github.com/ucsandman/marketing-studio)** | The **marketing pack** | One command renders a full launch asset suite (logo reveal, demo, social clips, OG) |
| **[janwilmake/openpolsia](https://github.com/janwilmake/openpolsia)** | The **whole system** | An open take on the autonomous-agency shape you're building a slice of |

**Video for the pack.** The launch video is where "not slop" is hardest *and*
where cost bites — so it's the cleanest thing to route through your Action Gate.

| Skill | Approach | Note |
|---|---|---|
| **[heygen-com/hyperframes](https://github.com/heygen-com/hyperframes)** | Write HTML → render a deterministic MP4; ships 19 agent skills | **Recommended default** — cheap, repeatable, no per-clip API bill, agent-native |
| **[AKCodez/promo-video-skill](https://github.com/AKCodez/promo-video-skill)** | Turns a SaaS/repo into a 30/60/90 s promo, landscape + portrait | Maps 1:1 to the launch-video deliverable |
| **[kdowswell/veo-tools](https://github.com/kdowswell/veo-tools)** | Generated video via Google Veo 3.1 | Model-API route — **real spend**, so it's an approval-tier action through your gate |
| **[rediumvex/ai-video-generator-claude](https://github.com/rediumvex/ai-video-generator-claude)** | 10 skills → Seedance 2.0 prompts on Higgsfield (viral hooks, SaaS demos) | Pricey per render (~$/clip) — sandbox first |

> Video-gen APIs cost money per render — exactly the side effect the Action Gate
> exists for: dry-run/sandbox by default, real spend gated behind approval. A
> deterministic HTML→MP4 renderer like Hyperframes sidesteps the bill entirely,
> which is why it's the recommended path for this assignment.

> Reddit's r/ClaudeAI project showcases are a good ongoing source for more; the
> repos above are verifiable ones in that vein.

---

## 3 · The crew

Not six abstract "departments" — the four roles an actual agency has. **One
orchestrator + three specialists.**

| Agent | Owns | Does | Model tier |
|---|---|---|---|
| **Strategist** (orchestrator) | The plan | Turns the brief into a positioning + brand-voice doc + a task list, then **delegates**. Makes zero external calls itself. | Top tier — this is the reasoning seat |
| **Web Builder** | The site | Generates the site and **deploys** it to a real host; returns the live URL | Mid tier |
| **Marketer** | Demand | Writes the pack (copy, posts, email) against the brand doc; a quick self-review catches off-brand or fabricated claims before it's saved | Mid tier |
| **Ops** | The money | Wires Stripe test-mode checkout into the site, seeds the DB, confirms a test purchase actually persists | Mid / cheap tier |

**A brand doc is the shared memory.** A small versioned file (voice, palette,
positioning, do/don't) the Strategist writes and the others read. Edit it, re-run,
and the output visibly changes — demo that. **Log the model tier and token cost per
call** so you can show cheaper models did the drafting.

---

## 4 · The one thing we insist on: a gate for spend & publish

You choose the stack, framework, store, and host. We insist on exactly one thing:
**anything that spends money or goes out to the world passes through a single
gate** — deploying the site, charging a (test) card, sending an email, publishing a
post. Not a decorator sprinkled on some calls. One door.

```
   agents ──▶  ┌───────────────────────────────────────────────┐
              │  ACTION GATE  (the only holder of credentials)  │
              │  · test-mode / sandbox by default                │
              │  · human approval before anything irreversible   │
              │  · idempotency key  → the same action, once      │
              │  · one audit row + cost per call                 │
              └──────┬───────────────────────┬──────────────────┘
                     ▼                        ▼
              deploy · Stripe · send    datastore (orders, audit)
```

Why: if an agent can deploy or charge *around* this door, your "approval" is
theater and your audit log lies. Concretely, that means:

- **Test-mode by default.** Stripe test keys; emails to a catcher, not real
  inboxes. The **one** thing that's real is the deployed site URL.
- **Approval before irreversible.** Going live and charging are actions a human
  clicks "approve" on — they don't just fire. (This is "light but real": one gate,
  one approval step, one audit trail. Not an enterprise compliance suite.)
- **Idempotent.** Re-run the build, or crash and restart, and you get **one** site,
  **one** order per purchase — never doubles. (That's the A3 lesson, with money.)
- **Traceable.** One run id ties the brief → each agent → each action, with cost.
  Enough that you can answer "what did it do, and what did it cost?" — not a full
  OTel deployment.

---

## 5 · Phase 0 — DESIGN.md first (hard gate)

**Your first commit is `DESIGN.md`, no code.** We check `git log`. In your words,
with your diagrams:

1. **The business** you'll demo, and what's in / out.
2. **The crew** — each agent's one job, its tools, its model tier and why, and what
   it may **never** do (e.g. Web Builder cannot charge a card).
3. **The Action Gate** — what routes through it, where credentials live, which
   actions are approval-gated.
4. **Brand doc & state** — what's shared, what persists.
5. **Idempotency** — how a re-run or a crash yields one site and one order, not two.
6. **Five ways this hurts the customer, and the control that stops each.** Steal
   from [`README-sample.md`](README-sample.md) §1.4 — Polsia shipped "done" tasks
   that never deployed, wrong-price outbound, duplicate charges. Your gate is the
   answer to those.

---

## 6 · Build order — two weeks

**Week 1 — the pipeline and one real deploy**
1. `DESIGN.md`, committed first.
2. The **Action Gate** with one trivial action (a test deploy): approval, idempotency,
   audit row, cost log. The door before the rooms.
3. The **Strategist**: brief → brand doc + task list, persisted.
4. The **Web Builder**: generate a site and **actually deploy it** through the gate.
5. **Demo:** submit a brief, get back a live URL, show the audit row for the deploy.

**Week 2 — marketing, money, and the proof**
6. The **Marketer**: the content pack, with the self-review pass, grounded in the brand doc.
7. **Ops**: Stripe test checkout wired into the site; a completed test purchase writes an order row.
8. Approval step on go-live + charge; idempotency on re-run and crash.
9. Deploy the *agency itself* to **[Fly.io](https://fly.io)** (or equivalent): real URL, real auth.
10. **Demo:** brief in → site + pack + checkout out; approve go-live; buy with a test
    card and watch the order land; then re-run and show no duplicate site or order.

---

## 7 · Grading (100 pts) & how you prove it

A **measurable rubric** + a **video demo**, consistent with the track. Ship an
`eval/` (a `rubric.json` and an `eval.py` you write) that checks the automated
criteria against your running agency and writes `PRODUCT_EVAL.md` — your submission.

| Area | Pts | What earns them |
|---|---|---|
| The three deliverables are **real** | 30 | Live URL, on-brand grounded pack, a test purchase that persists an order |
| Not slop | 15 | The site reads like a real brand's, not an AI template |
| The crew & orchestration | 15 | Strategist delegates only; scoped agents; brand doc changes behavior; cost logged |
| The Action Gate | 20 | Single door for spend/publish; only credential holder; approval before irreversible; idempotent; audit + cost |
| Design & failure catalogue (`DESIGN.md` first) | 10 | Argued choices; 5 real failure modes each with a control |
| Ships & runs from clean clone | 10 | Deployed agency URL; `.env.example`; one command up; the demo |

**The two rows that carry it:** the checkout **actually persists a real order** (no
fake success screen), and a **re-run produces no duplicate site or charge**. Those
are the line between an agency you'd trust with a credit card and one you wouldn't.

---

## 8 · Submit

1. **`PRODUCT_EVAL.md`** (or PDF) — the evaluation your eval produced.
2. A **60–90 s recording**: a brief goes in; the site deploys; you approve go-live;
   a test card completes checkout and the order appears in the DB; a re-run doesn't
   duplicate anything.
3. Links to the **deployed agency** and the **generated business site**.

---

## Going all the way (optional)

[`README-sample.md`](README-sample.md) is the **north-star**: the full autonomous,
multi-tenant version — EPYHIA the *company* that also runs nightly on a heartbeat,
markets and sells and grows unattended, modeled as a teardown of
[Polsia](https://polsia.com/). Far more than two weeks and not what you're graded
on — but the agency you build here is its honest core. The obvious stretch: add the
**nightly heartbeat** so your agency wakes up, looks at the business, and ships the
next thing on its own.
