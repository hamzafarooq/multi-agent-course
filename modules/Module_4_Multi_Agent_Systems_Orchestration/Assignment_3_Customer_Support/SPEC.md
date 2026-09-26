# SPEC: Assignment 3, Customer Support

> **This is the exhaustive specification, written to be read by a coding agent.** It is
> deliberately dense: every requirement, event, status code, span name and failure mode is
> stated once, explicitly, so an agent working from it cannot quietly skip one.
>
> **If you are a human, read [`PRD.md`](PRD.md) first.** It is the same product in about
> fifteen minutes. Come back here with a question and use the section numbers: the event
> contract is §7, the span tree is §10, the rules and their precedents are §11.
>
> **No number in here is authoritative.** Every threshold, budget and point value lives in
> [`THRESHOLDS.md`](THRESHOLDS.md) and is referred to here by id (`T-…`, `G-…`). The gold
> sets live in [`EVALS.md`](EVALS.md). Where this document and one of those disagree, they
> win and this document is stale — say so.

| | |
|---|---|
| **Project** | Customer Support: a multi-agent support desk for an online shop |
| **Track** | FDE Agent Engineering Bootcamp, cohort 2026-03, Module 4 |
| **Kicks off** | Module 4 (multi-agent systems and the protocol layer) |
| **Owner** | Hamza Farooq |
| **Status** | Ready for students |
| **Stack (taught path)** | Python 3.12 · Google ADK · MCP Toolbox for Databases · A2A · Mem0 · Arize Phoenix + OpenInference · FastAPI · PostgreSQL |
| **Lives in** | `modules/Module_4_Multi_Agent_Systems_Orchestration/Assignment_3_Customer_Support/` |
| **Reference build** | `../advance-customer-support-agent-feature-A2A-MCP-ADK/` (staff; do not copy, see §15) |

**One line.** One ADK support agent, MCP tools over Postgres, two A2A guard services, one
in-process guardrail, Mem0 memory, one Phoenix trace per message, built from an empty folder,
first as a CLI and then as a streaming web UI over the same pipeline.

> **The lesson.** Measure every guard on both sides, and enforce in code whatever must always
> happen. Too lax: a prompt that says "only this user" still lets Alice read Bob's order, and
> "ALWAYS search memory" gets skipped. Too strict: a generic guardrail blocks "leave my
> packages at the back door", and four LLM guard layers push every reply toward the edge of a
> customer's patience. A guard with no false-block rate is a guard nobody has measured.

---

## 1. Problem

Support desks are the most common first production agent: a bounded domain, a real database,
real customers, and real harm when it goes wrong. The harm is rarely the model being rude.
It is the system around the model: a tool that returns any customer's order to anyone who
asks for its number, a memory that quietly stores the agent's own mistakes, a guard that
fails open when its service is down, a safety prompt that refuses paying customers.

Every one of those happened in this course's reference build in September 2026 (§11). This
assignment has you build the same system from nothing, so that you meet each of those
decisions as a decision instead of inheriting it.

## 2. Goals

1. A customer can log in and get correct, grounded answers about **their own** orders, and
   only their own, through MCP tools over a real database.
2. Every message passes a **pipeline of guards** (a local sanitizer, an A2A Security Judge,
   an in-process Guardrail agent) before the support agent sees it, and an A2A Data Masker
   after.
3. The agent **remembers** a customer's standing preferences across sessions, through a
   recall step and a save step the pipeline runs, not the model.
4. Every message is **one Phoenix trace** whose span tree names every layer.
5. The same pipeline drives a **CLI** and a **streaming web UI**, through one event contract.
6. You can **prove** 1 to 5 with an eval runner you wrote, against numbers declared before
   you started.

## 3. Non-goals

- **No deploy.** Everything runs on your machine. You met deployment in LUMINA; here it
  would only hide the pipeline behind hosting problems.
- **No real authentication.** Passwords are seeded plain text for a demo (§8). Do not reuse
  this pattern; the lesson here is authorization inside the tools, not login.
- **No order mutation.** The agent records requested changes in `actions_log`. A person or a
  later system acts on them. An agent that can change an order is out of scope and a red line.
- **No voice.** That is VOXA.
- **No Google Cloud DLP or Model Armor.** Cut on purpose (they need a GCP project and hide
  the lesson). The Masker is yours to build (§5.6); the points went to guard calibration.

## 4. Users and scenarios

Ten seeded customers (EVALS §2). The scenarios are what your demo video shows, and each maps
to a gold set.

| | Who | Does | Sees |
|---|---|---|---|
| **A** | Alice | "What is the status of order 3?" | The Judge and Guardrail pass, an MCP `get-order-status` call, the SQL that ran with `3` filled in, `SHIPPED`, and one Phoenix trace containing all of it. |
| **B** | Alice | "What is the status of order 5?" (Bob's order) | "I can't find that order on your account." The tool's SQL requires the order to belong to her. No part of Bob's order appears anywhere: reply, tool result, or event stream. |
| **C** | Alice | `'; DROP TABLE users; --` | Blocked at the Judge in a fraction of the time an answer takes. The Guardrail, memory and agent never run, and the trace ends at `security.a2a_judge`. |
| **D** | Diana | "Please remember I work from home, so leave packages at the back door." A few minutes later: "Where should you leave my packages?" | The first turn passes every guard and ends with a `save` step. The second turn's `recall` step lists the memory with its score, and the answer uses it. |
| **E** | Alice | "Where is my last order?" | The cheap path: guards pass, one tool call, one sentence, fast. Nobody planned anything, and no memory was needed. Most real traffic looks like this, which is why latency is graded (`G-LATENCY`). |

## 5. Requirements

Must = graded, by a gate or a red line. Should = expected; missing it costs manual points.
Could = stretch.

### 5.1 The pipeline (one module, two front ends)

| # | Req | Level |
|---|---|---|
| P-1 | One `pipeline` module runs a turn and **yields events** (§7). The CLI and the web server both consume it; neither contains pipeline logic. | Must |
| P-2 | Step order is fixed: `sanitize` → `judge` → `guardrail` → `recall` → `agent` → `mask` → `save`. | Must |
| P-3 | A guard that blocks ends the turn immediately with `final {blocked: true, blocked_at}`. No later step runs, **including `save`**: a blocked message is never remembered. | Must |
| P-4 | A guard that **errors** (unreachable, timeout, unparseable verdict) ends the turn with an `error` event naming the step. It never lets the message through silently. (Red line: Fail loud.) | Must |
| P-5 | Every turn writes `runs/<turn_id>.json` (EVALS §4.1) before its terminal event is emitted. | Must |
| P-6 | Every turn is bounded by `T-BUD-TOOLS`, `T-BUD-TOKENS`, `T-BUD-WALL`. Hitting one ends it with `terminated: "cap"` and a reply that says so. | Must |
| P-7 | A turn's `turn_id` is a prefixed string (`turn_…`) generated by the pipeline, and appears in every log line for that turn. | Should |

### 5.2 Data and MCP tools

| # | Req | Level |
|---|---|---|
| M-1 | Postgres holds `users`, `customer_orders`, `actions_log`, seeded exactly per EVALS §2. | Must |
| M-2 | Database access is **only** through tools declared for MCP Toolbox for Databases (`tools.yaml`), served by the Toolbox server and loaded by the agent with `toolbox-core` over MCP. No SQL in Python. | Must |
| M-3 | Read tools: `get-order-status` (one order) and `find-customer-orders` (history, newest first). Write tool: `action-log`. | Must |
| M-4 | **Ownership is enforced in the SQL.** `get-order-status` takes the customer's email as a parameter and its statement filters on `customer_email = $n`. `find-customer-orders` filters the same way. | Must |
| M-5 | **The email the tools receive comes from the logged-in session, not from the model.** Bind it with a bound parameter (`toolbox-core` supports binding a parameter to a value or callable) so the model cannot supply a different one. | Must |
| M-6 | The agent's toolset contains **no tool that can modify `customer_orders`**. If you declare one for completeness, it is in a separate toolset the agent never loads. (Red line, `T-MUTATE`.) | Must |
| M-7 | `action-log` takes `action_type` from a fixed enum: `CANCEL_ORDER`, `RETURN_ORDER`, `UPDATE_ADDRESS`, `UPDATE_PREFERENCE`, `UPDATE_PROFILE`, enforced by a `CHECK` constraint on the column **and** by the tool parameter's description. | Must |
| M-8 | `action-log`'s `parameters` is a JSON object with at least `order_id` when an order is involved. The tool rejects an `order_id` the user does not own (the `INSERT … SELECT … WHERE` pattern, or a check query first). | Must |
| M-9 | An explicit request naming or clearly identifying one order ("cancel order 4", "cancel my monitor order") is logged in the same turn. An ambiguous one gets a clarifying question and no log. | Should |

### 5.3 The Security Judge (A2A service)

| # | Req | Level |
|---|---|---|
| J-1 | A separate process, its own port, exposing an A2A **agent card** at `/.well-known/agent.json` (or the current spec's `agent-card.json`) and a JSON-RPC endpoint. Use the current A2A method (`message/send`) or the older draft's `tasks/send`; say which in `DESIGN.md`. | Must |
| J-2 | Inside: an ADK agent with a deterministic pattern-matching tool (SQL injection, markup, template injection, shell and path traversal, prompt-extraction phrases) plus the model's own reading. | Must |
| J-3 | The verdict is **explicit**: a structured `{ "verdict": "allow" \| "block", "reason": "…" }`, not an echo of the input. (Precedent: the reference Judge signalled "safe" by returning the message unchanged, so a Judge that did nothing looked identical to one that approved.) | Must |
| J-4 | The pipeline calls it for every message and treats an unreachable Judge or an unparseable verdict as an error (P-4). | Must |

### 5.4 The Sanitizer (in-process)

| # | Req | Level |
|---|---|---|
| S-1 | Runs before the Judge, costs no model call: a length limit, a character allow-list, and the cheapest obvious patterns. | Must |
| S-2 | Apostrophes, `#`, `$`, `:`, `;`, `@` and ordinary punctuation are allowed. (The legitimate set contains all of them; see `T-LEGIT-FALSE-BLOCK`.) | Must |

### 5.5 The Guardrail (in-process agent)

| # | Req | Level |
|---|---|---|
| GR-1 | An ADK agent that answers one question: is this message safe and on-topic for **this** shop's support desk? Output `{ "decision": "safe" \| "unsafe", "reasoning": "…" }`. | Must |
| GR-2 | Its prompt states what the support agent is for (orders, deliveries, returns, account, preferences) and that personal details shared to get better service are on-topic. Its examples are drawn from this domain, not from a generic safety template. (Precedent: §11 R-6.) | Must |
| GR-3 | A fresh ADK session per check, deleted afterwards, so one message's verdict cannot colour the next. | Must |
| GR-4 | An unparseable decision is an error (P-4), not a pass. The reference build passed on parse failure; you must not. Say in `DESIGN.md` what this costs you. | Must |

### 5.6 The Data Masker (A2A service)

| # | Req | Level |
|---|---|---|
| K-1 | A separate A2A service like the Judge, called with the agent's final text. Returns the masked text and a count of what it changed. | Must |
| K-2 | It changes **only** PII (emails other than the user's own, phone numbers, card-like numbers). It never changes case, whitespace or anything else. (Precedent: §11 R-8, the lowercase Masker.) | Must |
| K-3 | The step's detail says what was masked ("masked 1 phone number") or "nothing to mask". A Masker that reports "passed" without having looked is a guard that lies. | Must |
| K-4 | Demonstrably masks a planted email and phone number (`B-PII`). | Could |

### 5.7 Memory (Mem0)

| # | Req | Level |
|---|---|---|
| R-1 | **Recall is a pipeline step, not a tool.** Before the agent runs, search Mem0 with the user's message, filtered to that user; request `T-MEM-TOPK`. | Must |
| R-2 | Insert a memory into the agent's input only when its score ≥ `T-MEM-MINSCORE` **and** its length ≤ `T-MEM-MAXCHARS`. Report the rest as skipped with the reason (below cutoff, too long). | Must |
| R-3 | Inserted memories go at the top of the agent's input under a fixed header, e.g. `Relevant memories about this customer (from Mem0):`. The agent's instruction says to trust tools over memories for order facts. | Must |
| R-4 | **Save only the user's message**, after the Masker, on turns that were not blocked. Never save the agent's reply. (Precedent: §11 R-5.) | Must |
| R-5 | The `recall` step event lists every candidate with its score and whether it was inserted. | Must |
| R-6 | The agent has **no** memory tool. | Must |

### 5.8 Observability (Phoenix)

| # | Req | Level |
|---|---|---|
| O-1 | Phoenix runs as its own long-lived process with persistent storage, started by your run script, not inside the agent process. Traces survive a restart of the agent. | Must |
| O-2 | Each turn opens one root span `agent.turn` (OpenInference kind `CHAIN`) with `input.value`, `output.value`, `user.id`. Every step is a child span with the name and kind in §10. | Must |
| O-3 | Gemini calls are auto-instrumented (`openinference-instrumentation-google-genai`) so they carry prompts, outputs and token counts. | Must |
| O-4 | The `trace` event (§7) carries the `trace_id` and a URL that opens that trace in Phoenix. | Must |
| O-5 | The CLI prints the trace URL after every turn. | Should |

### 5.9 The CLI

| # | Req | Level |
|---|---|---|
| C-1 | Prompts for email and password (hidden input), then loops on `You:`. `quit`, `exit` or `q` ends it. | Must |
| C-2 | Prints every event as it arrives, one readable line per step: `[judge] passed · 2 160 ms · security.a2a_judge`, tool calls with their arguments, the recall list, the final reply, the trace URL. | Must |
| C-3 | `--events` prints the raw event stream as NDJSON on stdout (one JSON object per line) and nothing else, so the eval runner can drive the CLI. | Must |
| C-4 | Refuses to start, naming the missing service, if the database, Toolbox, Judge, Masker or Phoenix is down. | Should |

### 5.10 The web UI

| # | Req | Level |
|---|---|---|
| W-1 | FastAPI app on one port serving the API (§7.2) and a single-page UI at `/`. | Must |
| W-2 | `POST /api/chat` streams the event contract as `application/x-ndjson`: identical events to `--events`. | Must |
| W-3 | The UI shows each step as it happens (not after the reply), with its status, detail, latency and span name; tool calls with their arguments, the SQL the tool ran and the result; the recall list; and a link to the turn's Phoenix trace. | Must |
| W-4 | Tool results render as a table, not a JSON string. | Should |
| W-5 | A live architecture view whose parts light up from the stream (`B-ARCH`). | Could |

## 6. Architecture

```
            ┌──────────── your run script starts every box below, in this order ────────────┐
 Postgres ─▶ MCP Toolbox :5000 ─▶ Judge (A2A) :10002 ─▶ Masker (A2A) :10003 ─▶ Phoenix :6006

                       ┌──────────────────── pipeline (one Python module) ─────────────────────┐
 CLI ──┐               │ sanitize → judge ─A2A→ guardrail → recall ─Mem0→ agent ─MCP→ tools   │
       ├─ events ◀─────┤                                                  │                     │
 Web ──┘ (NDJSON)      │                               mask ─A2A→ save ─Mem0→ final              │
                       └────────────── every step is a span under one agent.turn ──────────────┘
```

**Why the guards are separate services, and the Guardrail is not.** The Judge and Masker
are the checks a security team owns: they are versioned, deployed and audited apart from the
product, and any agent in the company can call them. That is what A2A is for. The Guardrail
encodes *this product's* scope ("is this about orders?"), changes whenever the product does,
and belongs next to it. Where a check lives follows who owns its definition.

**Why one pipeline module.** The CLI and the web UI are two views of the same run. If the
logic lives in either, they drift, and you will fix a bug in one and demo the other.

**Why memory is a step.** Anything that must happen on every turn is code. The model decides
what to say; it does not decide whether the system remembers.

**The stack.** The taught path is Python with Google ADK, because ADK, A2A and the MCP
Toolbox are the three protocols Module 4 teaches and they share a runtime. What is graded is
the event contract (§7), the span tree (§10) and the measured numbers. Another stack is your
call to make and your risk to carry.

## 7. The contract

### 7.1 Events

Every turn yields a sequence of JSON objects. The CLI's `--events` and `POST /api/chat`
emit exactly this, one object per line.

```jsonc
{ "type": "trace",       "turn_id": "turn_…", "trace_id": "131a…", "url": "http://localhost:6006/projects/<p>/traces/131a…" }
{ "type": "stage",       "key": "judge", "label": "A2A Security Judge" }                // a step started
{ "type": "step",        "key": "judge", "status": "passed" | "blocked",               // a step finished
                         "detail": "allow: no injection patterns", "ms": 2160, "span": "security.a2a_judge",
                         "kind": "A2A" | "in-process" | "Python fn",
                         "memories": [ { "memory": "…", "score": 0.43, "inserted": true, "reason": null } ] }   // recall only
{ "type": "llm",         "model": "gemini-2.5-flash", "decision": "call get-order-status" | "final answer",
                         "tokens_in": 1427, "tokens_out": 19, "ms": 966, "span": "call_llm" }
{ "type": "tool_call",   "id": 1, "name": "get-order-status", "args": { "order_id": 3 },
                         "info": { "kind": "MCP", "access": "READ", "statement": "SELECT … WHERE order_id = $1 AND customer_email = $2", "params": ["order_id", "customer_email"] },
                         "span": "execute_tool get-order-status" }
{ "type": "tool_result", "id": 1, "name": "get-order-status", "ok": true, "ms": 9, "result": [ { "order_id": 3, "status": "SHIPPED" } ] }
{ "type": "final",       "blocked": false, "blocked_at": null, "response": "Order 3 is SHIPPED…",
                         "terminated": "done", "wall_clock_ms": 7412, "tokens": { "in": 4210, "out": 96 } }
{ "type": "error",       "step": "judge", "status": 502, "error": "Security Judge unreachable: connection refused", "terminated": "error" }
```

- `args` values that arrive as JSON strings are decoded before emitting (the model sends
  `action-log`'s `parameters` as a string).
- `result` is the decoded tool output. The MCP Toolbox wraps it as `{"result": "<JSON
  string>"}`; unwrap it. A result the user may not see is never emitted (`T-LEAK`).
- `tool_call.info.params` lists the statement's parameters in `$n` order, so a UI can show the
  SQL with values filled in. A bound parameter (the session email) is shown as bound, not as a
  value the model chose.

### 7.2 Routes

```jsonc
POST /api/login        body: { "email": "…", "password": "…" }
  -> 200 { "user_id": "alice.jones@example.com", "full_name": "Alice Jones", "is_premium": false }
  -> 401 { "error": "Invalid email or password." }
POST /api/chat         body: { "user_id": "…", "message": "…" }
  -> 200 application/x-ndjson   (the §7.1 stream)
  -> 400 { "error": "message is empty" }            // empty or whitespace-only
  -> 401 { "error": "Not logged in." }              // no session for user_id
  -> 413 { "error": "message too long" }            // over the Sanitizer's length limit, before streaming
POST /api/logout       body: { "user_id": "…" }  -> 200 { "ok": true }
GET  /health           -> 200 { "status": "ok", "model": "gemini-2.5-flash", "db": "ok", "toolbox": "ok",
                                "judge": "ok", "masker": "ok", "mem0": "ok", "phoenix": "ok" }
                       -> 503 same shape, with the failing dependency's value set to its error string
GET  /                 -> 200 text/html (the UI)
```

Status set, fixed: `400` invalid input · `401` not logged in · `413` too large · `502` an
upstream failure, carried **inside** the stream as an `error` event once streaming has begun
· `503` from `/health` only. `/health` values are free strings, never an enum.

### 7.3 Ordering rules (each is checked by `T-EVENT-ORDER`)

1. `trace` is the first event of every turn.
2. `stage` events appear in P-2 order; each `stage` is followed by its own `step` before the
   next `stage` begins (the agent's `llm`/`tool_*` events sit between the `agent` stage and
   the `mask` stage).
3. Every `tool_call` has exactly one `tool_result` with the same `id`, before `final`.
4. A `step` with `status: "blocked"` is followed immediately by `final` with `blocked: true`
   and the same `blocked_at`. No `llm`, `tool_*`, `recall` or `save` event follows it.
5. Exactly one terminal event, `final` or `error`, and it is the last event.
6. `save` never appears on a blocked turn or an error turn.

## 8. Data model

| Table | Key fields | Constraints you add |
|---|---|---|
| `users` | `email` unique, `full_name`, `is_premium_customer`, `password` | none; the plain-text password is a demo seed, never a pattern to copy |
| `customer_orders` | `order_id`, `customer_email`, `status`, `items` JSONB, `order_date`, `total_amount` | index on `customer_email` |
| `actions_log` | `id`, `timestamp`, `user_email`, `action_type`, `parameters` JSONB | `CHECK (action_type IN ('CANCEL_ORDER','RETURN_ORDER','UPDATE_ADDRESS','UPDATE_PREFERENCE','UPDATE_PROFILE'))` |

Outside Postgres: Mem0 holds memories keyed by the user's email; Phoenix holds traces;
`runs/` holds one JSON file per turn (EVALS §4.1).

## 9. Performance, SLA and cost

| Metric | Target | Why |
|---|---|---|
| Passing turn latency, p50 / p95 | `T-LAT-P50` / `T-LAT-P95` | THRESHOLDS §1 |
| Blocked turn latency, p95 | `T-LAT-BLOCK-P95` | a rejection must be cheaper than an answer |
| Error rate | `T-ERR` | |
| Per-turn budget | `T-BUD-TOOLS`, `T-BUD-TOKENS`, `T-BUD-WALL` | |

Report latency **per outcome** (passed, blocked, error), never blended. Averaging a fast
block with a slow answer is how a slow answer hides. Record, in `DESIGN.md`, how much of a
passing turn's latency each guard costs; this is the evidence for the Trade-offs section.

## 10. Observability: the span tree

A turn that passes every guard produces exactly this shape (names exact, kinds from
OpenInference):

```
agent.turn                                   CHAIN
├─ security.sanitize                         GUARDRAIL
├─ security.a2a_judge                        GUARDRAIL
├─ guardrail.check                           GUARDRAIL
│   └─ invoke_agent guardrail_agent          AGENT     (ADK, automatic)
├─ memory.recall                             RETRIEVER  retrieval.documents.N.document.{content,score}
├─ invoke_agent <your support agent name>    AGENT     (ADK, automatic)
│   ├─ call_llm                              LLM       (one per model call)
│   │   └─ execute_tool <tool name>          TOOL      (one per tool call)
│   └─ call_llm                              LLM
├─ security.a2a_mask                         GUARDRAIL
└─ memory.save                               TOOL
```

A blocked turn stops at the blocking guard's span. An error turn marks the failing span with
error status and its exception. Required spans for `T-TRACE-SHAPE`: `agent.turn`,
`security.sanitize`, `security.a2a_judge`, `guardrail.check`, `memory.recall`,
`invoke_agent`, `security.a2a_mask`, `memory.save`.

ADK runs the agent inside your `agent.turn` context only if you iterate its async runner
inside that span. If `invoke_agent` shows up as its own root, your context did not propagate;
that is the most common way `T-TRACE-ONE` fails.

## 11. Non-negotiables, and the incidents behind them

Every rule here cites the failure that created it. All incidents happened in the course's
reference build on 25 September 2026 unless marked otherwise.

| Id | Rule | Precedent |
|---|---|---|
| R-1 | Ownership is checked in the tool's SQL, with the email bound from the session. | Alice asked "status of order 5" and got Bob's $1,500 gaming laptop. The prompt said "only this user"; the SQL said `WHERE order_id = $1`. |
| R-2 | Anything that must happen every turn is a pipeline step, not a prompt instruction. | The prompt said "ALWAYS use `search_memory`". On "status of order 3" Gemini skipped it. |
| R-3 | The agent's toolset excludes every mutating tool; a prompt that forbids a loaded tool is not a control. | The reference toolset loaded `update-order-status` and relied on the sentence "must NOT call this directly". |
| R-4 | A guard that errors fails the turn loudly. | Cohort precedent A1, Live Translate (cohort 2026-01): a dependency mismatch made every call throw, the handler returned the input, and it served English for weeks. Here: the reference Guardrail returned "safe" on any parse failure. |
| R-5 | Save only what the user said. | Bob's memories included "Assistant states it cannot set a specific delivery location"; when he asked where to leave packages, the agent trusted its own old refusal over his stated preference. |
| R-6 | A guardrail's prompt defines this product's scope with this product's examples. | The copied prompt's "safe" examples were "Tell me about the history of AI". It blocked "leave packages at the back door" as personal chat and let "write me a poem about the stock market" through. |
| R-7 | Reject over-long memories before they reach a prompt. | Mem0's merge step looped; one memory reached 30,100 characters of repeated "(Note: The assistant previously noted…)", inserted into every prompt. |
| R-8 | A guard changes only what it exists to change. | The Masker called `.lower()` on every reply, in the CLI and the web UI, so every answer came back in lowercase and no test noticed. |
| R-9 | A verdict is explicit, never inferred from an echo. | The Judge signalled "safe" by returning the input unchanged. |
| R-10 | Traces outlive the process. | Phoenix ran in-process with in-memory storage; three restarts in one afternoon wiped every trace, and the web UI had never been traced at all. |
| R-11 | Enumerations are enforced by the schema. | One afternoon logged the same intent as `RETURN_ORDER`, `RETURN_ITEM` and `UPDATE_DELIVERY_PREFERENCE`. |

Plus the course's four rules: **Grounded or nothing** (an order fact comes from a tool call in
that turn) · **Fail loud** (R-4) · **Bounded and honest** (P-6) · **Evidence over vibes**
(every graded number comes from your eval runner).

## 12. Grading

Point values, pass conditions, bonus and red lines: THRESHOLDS §8. Summary of rows and their
instruments:

| Row | Instrument |
|---|---|
| `G-MCP` | order set replies + `execute_tool` spans |
| `G-ACCESS` | cross-user probe set + the SQL quoted in `DESIGN.md` |
| `G-ATTACK`, `G-FALSE-BLOCK`, `G-OFFTOPIC` | attack, legitimate and off-topic sets, from run logs |
| `G-MEMORY` | memory pairs, from the `recall` step of each ask turn |
| `G-TRACE` | Phoenix REST, per `trace_id` |
| `G-EVENTS` | ordering rules §7.3 over every turn's stream, CLI and web |
| `G-LATENCY` | run logs, per outcome |
| `G-DESIGN`, `G-ENFORCE`, `G-TRAJECTORY` | a person, with your report and video |

## 13. Quality bar

The four laws, the run-log shape, the report shape and the six gates are in EVALS §1, §4, §5.
Two additions specific to this build:

- **Read the trajectory, not the answer.** A correct reply produced by a guard that errored
  and fell through, or by a memory instead of a tool, is a failure the answer hides.
- **Measure both sides every time you change a guard.** A change that raises
  `T-ATTACK-BLOCK` and is not re-measured against the legitimate set is not an improvement
  yet.

## 14. Build order

`TECHNICAL.md` §4 has the ten stages, each ending in a check you run. The CLI works end to
end at stage 8; the web UI is stage 9; the eval runner is stage 10 but you should start
transcribing the gold sets at stage 5.

## 15. Provided vs built

**Provided:** this folder. Markdown only: `README.md`, `PRD.md`, `SPEC.md`, `AGENTS.md`,
`CLAUDE.md`, `TECHNICAL.md`, `DESIGN.template.md`, `BUILD_LOG.template.md`,
`THRESHOLDS.md`, `EVALS.md`, `SUBMISSION.md`.

**Built by you:** everything else. Suggested layout (yours to change): `support/pipeline.py`,
`support/cli.py`, `support/web.py`, `support/telemetry.py`, `support/memory.py`,
`guards/sanitizer.py`, `guards/judge/`, `guards/masker/`, `mcp_toolbox/tools.yaml`,
`db/seed.sql`, `eval/`, `run.sh`, `DESIGN.md`, `BUILD_LOG.md`.

**How the build is paced.** `TECHNICAL.md` §4 splits the work into ten stages, each with a
decision the student makes, a check the student runs and reads, and a `BUILD_LOG.md` entry
the student writes. A coding agent working from this spec asks the stage's decision and
stops at its check (`AGENTS.md`, the checkpoint rule); it does not run ahead.

**The reference build** in `../advance-customer-support-agent-feature-A2A-MCP-ADK/` has every
bug in §11 fixed or documented. You may read it to understand a concept. Copying it is
visible in your trajectory and your `DESIGN.md`, and it will not pass: its toolset, its
Judge verdict and its Guardrail's fail-open behaviour all violate this spec on purpose.

## 16. Risks and assumptions

| Risk | Mitigation |
|---|---|
| Gemini rate limits during a full eval run | Run sets in sequence with a small delay; retry on `429` with backoff and log the retry as a failed attempt (A1), not a silent success. |
| Mem0 extraction takes longer than `T-MEM-WAIT` | Wait longer; the threshold is a minimum. Never shorten it to pass. |
| Model variance between runs | Run the full eval at least twice before you submit; report both runs and use the lower one. |
| Phoenix export lag makes traces look incomplete | Flush the span processor at the end of the run and wait before reading (EVALS §7). |
| The Guardrail over-blocks after a prompt tweak | Re-run the legitimate set after every Guardrail change (§13). |

## 17. Open questions

| Question | Owner |
|---|---|
| Should the Judge's pattern tool alone be allowed to block without the model (faster `T-LAT-BLOCK-P95`), or must both agree? Your call; defend it in Trade-offs. | Student |
| Should memories older than a certain age be excluded from recall? | Student, stretch |

## 18. Stretch goals

`B-ARCH`, `B-RULE`, `B-PII` (THRESHOLDS §8). Beyond the bonus: a Judge that returns a
confidence and a Guardrail that only runs when the Judge is unsure; a per-customer memory
view with a delete button.

## 19. Submission

`SUBMISSION.md`.
