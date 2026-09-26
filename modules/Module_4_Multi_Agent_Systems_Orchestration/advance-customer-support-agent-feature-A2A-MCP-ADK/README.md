# Customer Support Agent — Quick Start

Multi-agent customer support agent built with Google ADK, MCP Toolbox, A2A security microservices, Mem0 memory, and Arize Phoenix observability. It runs as a terminal CLI or as a **web UI that streams every step live**, with a **live architecture view** and **one Phoenix trace per message**. Runs locally; no GCP credentials required.

> **Start here for class:** [`docs/build-log/index.html`](docs/build-log/index.html) explains, step by step, how the web UI, architecture view, tracing and memory were built, what's still broken on purpose, and gives a ready-made demo script.

```
User → Sanitizer → A2A Security Judge → Guardrail → Mem0 recall → Support Agent (+ MCP tools) → A2A Data Masker → Mem0 save → User
            └──────────────────────── every step is a span in one Phoenix trace ────────────────────────┘
```

## Prerequisites

| Tool | Version | Purpose |
|:-----|:--------|:--------|
| Python | 3.12+ | Runtime |
| conda | any | PostgreSQL server |
| Node.js | 18+ | MCP Toolbox via npx |

---

## 1 — Clone / Unzip

```bash
unzip advance-customer-support-agent.zip
cd advance-customer-support-agent-feature-A2A-MCP-ADK
```

---

## 2 — Environment Variables

```bash
cp .env.example .env
```

Edit `.env` and set these two keys (everything else can stay blank):

```env
GOOGLE_GENAI_USE_ENTERPRISE=false
PYTHONWARNINGS=ignore

GOOGLE_API_KEY=<your Google AI Studio key>   # aistudio.google.com/apikey
MEM0_API_KEY=<your Mem0 key>                 # mem0.ai
```

> **Note** — do not set `GOOGLE_GENAI_USE_VERTEXAI`. That variable is deprecated and will produce warnings.

---

## 3 — Python Dependencies

> **Shortcut:** `./run.sh setup` does everything in this section *and* section 4 (env, deps,
> Postgres, seed, `.env` template) in one step. The manual steps below are for reference.

Create an isolated conda environment (Python 3.12, matching the prerequisite) and install into it:

```bash
conda create -y -n customer-support python=3.12
conda activate customer-support
```

```bash
pip install -r requirements.txt

# Observability (Phoenix + OpenTelemetry)
pip install arize-phoenix openinference-instrumentation-google-genai \
    openinference-semantic-conventions

# Pin the OTel family to the version google-adk requires (>=1.39,<=1.42.1).
pip install opentelemetry-sdk==1.42.1 opentelemetry-api==1.42.1 \
    opentelemetry-exporter-otlp-proto-http==1.42.1 \
    opentelemetry-semantic-conventions==0.63b1
```

---

## 4 — PostgreSQL (via conda)

```bash
# Install postgres in your conda env (once)
conda install -c conda-forge postgresql -y

# Initialise a data directory (once)
initdb -D ~/postgres_data

# Start the server
pg_ctl -D ~/postgres_data -l ~/postgres_data/logfile start

# Create DB and user (once)
createdb toolbox_db
psql -d toolbox_db -c "CREATE USER toolbox_user WITH PASSWORD 'mysecretpassword';"
psql -d toolbox_db -c "GRANT ALL PRIVILEGES ON DATABASE toolbox_db TO toolbox_user;"
```

### Seed the database

Run the following SQL once inside `psql -U toolbox_user -d toolbox_db`:

<details>
<summary><strong>Show SQL — click to expand</strong></summary>

```sql
CREATE TABLE users (
    user_id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    full_name VARCHAR(100),
    is_premium_customer BOOLEAN DEFAULT FALSE,
    total_items_purchased INTEGER DEFAULT 0,
    password VARCHAR(255) NOT NULL
);

INSERT INTO users (email, full_name, is_premium_customer, total_items_purchased, password) VALUES
    ('hannah.m@school.edu',       'Hannah M',    TRUE,  94, 'hannah'),
    ('charlie.d@webmail.com',     'Charlie D',   TRUE,  88, 'charlie'),
    ('julia.child@kitchen.com',   'Julia Child', TRUE,  75, 'julia'),
    ('evan.g@bizcorp.com',        'Evan G',      TRUE,  56, 'evan'),
    ('alice.jones@example.com',   'Alice Jones', FALSE, 42, 'alice'),
    ('ian.malcolm@chaos.com',     'Ian Malcolm', FALSE, 31, 'ian'),
    ('diana.prince@hero.net',     'Diana Prince',FALSE, 23, 'diana'),
    ('george.j@jungle.com',       'George J',    FALSE, 19, 'george'),
    ('bob.smith@techmail.com',    'Bob Smith',   FALSE, 15, 'bob'),
    ('fiona.shrek@swamp.com',     'Fiona Shrek', FALSE, 12, 'fiona');

CREATE TABLE customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(100) NOT NULL,
    delivery_address VARCHAR(255),
    status VARCHAR(20) CHECK (status IN ('PROCESSING','SHIPPED','DELIVERED','CANCELLED','RETURNED')),
    items JSONB,
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount DECIMAL(10,2)
);

INSERT INTO customer_orders (customer_email, delivery_address, status, items, order_date, total_amount) VALUES
('alice.jones@example.com','123 Market St, Springfield','DELIVERED','[{"product":"Ergonomic Office Chair","qty":1,"price":250.00}]',NOW()-INTERVAL '6 months',250.00),
('alice.jones@example.com','123 Market St, Springfield','DELIVERED','[{"product":"Wireless Mouse","qty":1,"price":25.00}]',NOW()-INTERVAL '3 months',25.00),
('alice.jones@example.com','123 Market St, Springfield','SHIPPED','[{"product":"Mechanical Keyboard","qty":1,"price":120.00}]',NOW()-INTERVAL '2 days',120.00),
('alice.jones@example.com','123 Market St, Springfield','PROCESSING','[{"product":"USB-C Hub","qty":1,"price":45.00}]',NOW()-INTERVAL '1 hour',45.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','DELIVERED','[{"product":"Gaming Laptop 15-inch","qty":1,"price":1500.00}]',NOW()-INTERVAL '1 year',1500.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','CANCELLED','[{"product":"VR Headset","qty":1,"price":400.00}]',NOW()-INTERVAL '10 days',400.00),
('bob.smith@techmail.com','88 Tech Ave, Seattle','PROCESSING','[{"product":"Curved Monitor 34-inch","qty":1,"price":450.00}]',NOW()-INTERVAL '4 hours',450.00),
('charlie.d@webmail.com','12 Oak Rd, Denver','DELIVERED','[{"product":"AA Batteries (Pack of 12)","qty":2,"price":15.00}]',NOW()-INTERVAL '45 days',30.00),
('diana.prince@hero.net','5 Hero Ln, Metropolis','DELIVERED','[{"product":"Smart Watch Gen 5","qty":1,"price":299.00}]',NOW()-INTERVAL '60 days',299.00),
('diana.prince@hero.net','5 Hero Ln, Metropolis','RETURNED','[{"product":"Running Shoes","qty":1,"price":120.00}]',NOW()-INTERVAL '15 days',120.00),
('evan.g@bizcorp.com','200 Business Pkwy, Austin','SHIPPED','[{"product":"Office Desk","qty":2,"price":300.00}]',NOW()-INTERVAL '1 day',600.00),
('fiona.shrek@swamp.com','7 Swamp Rd, Bayou','CANCELLED','[{"product":"Skincare Gift Set","qty":1,"price":85.00}]',NOW()-INTERVAL '5 days',85.00),
('george.j@jungle.com','9 Jungle Path, Amazonia','PROCESSING','[{"product":"Bluetooth Speaker","qty":1,"price":60.00}]',NOW()-INTERVAL '30 minutes',60.00),
('hannah.m@school.edu','4 Campus Dr, Boston','DELIVERED','[{"product":"Notebook Pack","qty":5,"price":12.00}]',NOW()-INTERVAL '4 months',60.00),
('ian.malcolm@chaos.com','22 Chaos Blvd, San Diego','DELIVERED','[{"product":"Professional Camera Lens","qty":1,"price":2200.00}]',NOW()-INTERVAL '8 months',2200.00),
('julia.child@kitchen.com','10 Kitchen St, Portland','DELIVERED','[{"product":"Coffee Beans 1kg","qty":1,"price":25.00}]',NOW()-INTERVAL '3 months',25.00),
('julia.child@kitchen.com','10 Kitchen St, Portland','PROCESSING','[{"product":"Descaling Kit","qty":1,"price":15.00}]',NOW()-INTERVAL '3 hours',15.00);

CREATE TABLE actions_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL
);

GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO toolbox_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO toolbox_user;
```

</details>

---

## 5 — Run

### Option A — one command (recommended)

A helper script, [`run.sh`](run.sh), orchestrates the whole stack in dependency order and
drops you straight into the agent CLI. From the project root:

```bash
./run.sh            # PostgreSQL → MCP Toolbox → A2A servers → Phoenix → agent CLI
./run.sh web        # same stack, then the web UI at http://127.0.0.1:8000
```

It health-checks each service before launching the next, and tears the background services
down automatically when you exit the CLI (Ctrl-C). Other subcommands:

```bash
./run.sh setup      # one-time: create env, install deps + Postgres, init DB, seed, write .env
./run.sh web        # serve the web UI instead of the terminal CLI
./run.sh stop       # stop background services (Toolbox, A2A, Phoenix, Postgres)
./run.sh status     # show what's up
./run.sh seed       # re-seed the database to a known state
./run.sh logs       # tail the Toolbox + A2A logs
```

> First time on this machine? Run `./run.sh setup` once, fill `GOOGLE_API_KEY` and
> `MEM0_API_KEY` in `.env`, then `./run.sh`. See the **Platform support** note at the top of
> `run.sh` for Windows (WSL/Git Bash).

### Option B — four terminals (manual)

Open four terminal tabs from the project root.

**Terminal 1 — MCP Toolbox**
```bash
npx @toolbox-sdk/server --config mcp_toolbox/tools.yaml --enable-api --address 127.0.0.1 --port 5000
```
Starts on `http://127.0.0.1:5000`. Wait for `Server ready to serve!` before continuing.

**Terminal 2 — A2A Security Servers**
```bash
python -m cs_agent.a2a.run_servers
```
Starts Judge (`:10002`) and Mask (`:10003`). Wait for both `Uvicorn running on ...` lines.

**Terminal 3 — Agent**
```bash
cd cs_agent
python agent_cli.py
```

The CLI displays the user list, asks you to pick a user, then starts the conversation.
**Phoenix observability launches automatically** with the agent (see the *Observability*
section below) — there is no separate Phoenix step.

---

## Startup order matters

```
PostgreSQL  →  MCP Toolbox  →  A2A Servers  →  Phoenix  →  Agent (CLI or web)
```

`run.sh` enforces this for you; if you start things manually and the Toolbox or A2A servers
aren't up, the agent refuses to start.

---

## Test users & passwords

Every user's password is their first name, lowercase.

| Email | Password | Tier |
|:------|:---------|:-----|
| hannah.m@school.edu | `hannah` | Premium |
| julia.child@kitchen.com | `julia` | Premium |
| charlie.d@webmail.com | `charlie` | Premium |
| evan.g@bizcorp.com | `evan` | Premium |
| alice.jones@example.com | `alice` | Standard |
| bob.smith@techmail.com | `bob` | Standard |
| ian.malcolm@chaos.com | `ian` | Standard |
| diana.prince@hero.net | `diana` | Standard |
| george.j@jungle.com | `george` | Standard |
| fiona.shrek@swamp.com | `fiona` | Standard |

---

## Using the web UI (recommended for class)

`./run.sh web`, then open three tabs:

| URL | What it shows |
|:----|:--------------|
| http://127.0.0.1:8000 | Chat. Each answer has a **What happened** panel listing every step as it runs |
| http://127.0.0.1:8000/architecture | The architecture diagram. Each box lights up while it runs, with a live event log underneath |
| http://localhost:6006 | Phoenix. Each answer's **View trace in Phoenix ↗** link opens that exact trace |

The chat streams one JSON event per step (`POST /api/chat` returns `application/x-ndjson`), so you see each step start and finish instead of waiting for the whole answer. Each step in the **What happened** panel shows:

- a type badge: `in-process`, `A2A`, `LLM`, `MCP`, `Python fn`, plus `READ`/`WRITE` for SQL tools
- what it did in plain words, its latency, and the Phoenix span name to look for
- for MCP tools: the route the call takes (Gemini function call → ADK → toolbox-core → MCP `tools/call` → Toolbox → Postgres), the SQL that ran with the real values filled in, and the result as a table
- for Gemini calls: what it decided (which tool, or the final answer) and its token counts
- for Mem0 recall: each memory found, its relevance score, and whether it was inserted into the agent's context

The architecture page gets its events from the chat tab through `BroadcastChannel`, so both tabs must be open **in the same browser**.

### The pipeline

| # | Step | Runs as | Blocks on | Span |
|:--|:-----|:--------|:----------|:-----|
| 1 | Sanitizer | regex, in-process | length / characters / blocklist | `security.sanitize` |
| 2 | Security Judge | ADK agent over A2A (:10002) | injection (SQLi, XSS) | `security.a2a_judge` |
| 3 | Guardrail | ADK agent, in-process | unsafe or off-topic for a shop's support desk | `guardrail.check` |
| – | Mem0 recall | `mem0.search()` | – (top 5 matches, score ≥ 0.25, ≤ 500 chars) | `memory.recall` |
| – | Support Agent | ADK `LlmAgent`, gemini-2.5-flash + MCP tools | – | `invoke_agent`, `call_llm`, `execute_tool` |
| 4 | Data Masker | ADK agent over A2A (:10003) | – (removes PII from the answer) | `security.a2a_mask` |
| – | Mem0 save | `mem0.add()` | – (user message only) | `memory.save` |

Memory is a **fixed step**, not a tool the model chooses to call: the pipeline searches Mem0 before every agent call and saves the user's message after every turn. Mem0 processes saves in the background, so new facts show up in recall after **a minute or two**. The CLI still uses the older design: a `search_memory` tool, and one save when you exit.

### Demo questions

See the **Class demo script** in [`docs/build-log/index.html`](docs/build-log/index.html#demo). In short:

| As | Ask | Shows |
|:---|:----|:------|
| alice | What is the status of order 3? | MCP tool, SQL, result table, Phoenix trace |
| diana | Please remember I work from home, so leave packages at the back door, and text me instead of emailing → wait 1–2 min → Where should you leave my packages, and how should you contact me? | memory being saved, then recalled |
| alice | `'; DROP TABLE users; --` | blocked by the Security Judge |
| alice | Write me a poem about the stock market | blocked by the Guardrail |
| alice | What is the status of order 5? | **bug:** she sees Bob's order, because the tool never checks who owns it |

Run `./run.sh seed` before class to reset Postgres.

---

## Using the agent (CLI walkthrough)

1. Start the stack (`./run.sh`). The CLI prints the user table and the welcome banner.
2. At **`Enter your email:`** type a user's email (e.g. `alice.jones@example.com`).
3. At **`Enter your password:`** type their password (e.g. `alice`). Input is hidden.
4. You'll see a 4-step loader (auth → memory → orders → actions), then the `You:` prompt.
5. Chat. Each turn runs the full pipeline: **sanitize → A2A Security Judge → agent (+ MCP
   tools, Mem0 memory) → A2A Data Masker** on the response. Type `quit`, `exit`, or `q` to end
   (your conversation is saved to memory on exit).

**Sample queries**

```
What's the status of order 3?           # → MCP get-order-status
Show me all my orders                    # → MCP find-customer-orders
I prefer email contact only, remember    # → saved to Mem0 memory
Cancel order 4                           # → agent confirms, then logs via action-log
'; DROP TABLE users; --                  # → blocked by the A2A Security Judge
```

**Inspect the database** (passwords, orders, and the agent's logged actions) in another shell:

```bash
conda activate customer-support
psql -h 127.0.0.1 -p 5432 -d toolbox_db -U toolbox_user   # password: mysecretpassword

# then, inside psql:
\dt                              -- list tables
SELECT * FROM users;             -- emails + passwords + tier
SELECT * FROM customer_orders;   -- orders the agent reads
SELECT * FROM actions_log;       -- intents the agent logs (cancel/return/address changes)
```

---

## Observability — Arize Phoenix

The agent ships with **Arize Phoenix** tracing, wired up in
[`cs_agent/telemetry.py`](cs_agent/telemetry.py). Phoenix is an open-source LLM-observability
tool: it records a **trace** for every request — a tree of timed **spans** — so you can see
exactly what the agent did, not just what it said.

**How to run it:** nothing extra. `run.sh` starts `phoenix serve` as its own service on
**http://localhost:6006**, saving traces to `~/.phoenix/phoenix.db`. It keeps running when you
restart the agent, so traces survive restarts; `./run.sh stop` shuts it down. If you start the
agent without `run.sh`, `init_telemetry()` checks for a running Phoenix and, if there isn't one,
starts an in-memory instance whose traces are lost on exit.

Each message is **one trace**: a root `agent.turn` span (CHAIN), with a child span for every
guardrail layer, the Mem0 recall and save, the agent, each Gemini call and each tool call.

**What you'll see per turn:**

| Span kind | What it captures |
|:----------|:-----------------|
| `GUARDRAIL` | input sanitization, the A2A Security Judge verdict, the Guardrail decision + reasoning, and PII masking |
| `RETRIEVER` | Mem0 recall (web UI): each memory with its score |
| `CHAIN` | the overall agent turn (input → masked output) |
| `TOOL` | each MCP tool call (`get-order-status`, `find-customer-orders`, `action-log`) with its args and result |
| LLM spans | every Gemini call — prompt/output, token counts, and per-turn cost |

This makes the multi-agent flow visible: you can watch the Judge clear (or block) a message,
the MCP tools fire, and the Masker scrub the output, all on one timeline.

> **Setup note:** Phoenix and the OpenTelemetry exporters are installed by `./run.sh setup`
> (they're not in `requirements.txt`). If you set things up manually, install
> `arize-phoenix`, `openinference-instrumentation-google-genai`,
> `openinference-semantic-conventions`, and pin `opentelemetry-sdk==1.42.1` /
> `opentelemetry-exporter-otlp-proto-http==1.42.1` to match `google-adk`.

---

## Project structure

```
├── cs_agent/
│   ├── agent_cli.py          # CLI entry point
│   ├── web.py                # Web UI + streaming pipeline (FastAPI, NDJSON)
│   ├── static/
│   │   ├── architecture.svg  # the diagram (element ids are lit by events)
│   │   └── architecture.html # /architecture: live view + event log
│   ├── telemetry.py          # OpenTelemetry → Phoenix
│   ├── memory.py             # Mem0 integration
│   ├── prompts.py            # System prompts
│   ├── greet.py              # Login flow
│   ├── a2a/                  # A2A microservice infrastructure
│   ├── agents/               # Judge + Mask ADK agents
│   └── security/             # Regex blocker + sanitizer
├── mcp_toolbox/              # (gitignored) generated by run.sh
│   ├── tools.yaml            # DB tool definitions (Postgres)
│   └── seed.sql              # demo data
├── docs/build-log/           # step-by-step build log + demo script (open index.html)
├── run.sh                    # one-command orchestrator (setup/start/web/stop/status/seed/logs)
├── .env                      # Your keys (not committed)
├── .env.example              # Template
└── requirements.txt
```

---

## Troubleshooting

**A2A servers not reachable** — start Terminal 2 first and wait for both `Started server` lines before running the agent.

**MCP Toolbox connection refused** — ensure Terminal 1 shows `Serving on` before running the agent.

**PostgreSQL not running** — run `pg_ctl -D ~/postgres_data status`; if stopped, run `pg_ctl -D ~/postgres_data start`.

**Warnings in terminal** — make sure `.env` has `PYTHONWARNINGS=ignore` and does not contain `GOOGLE_GENAI_USE_VERTEXAI`. If you previously ran `export GOOGLE_GENAI_USE_VERTEXAI=false` in your shell, run `unset GOOGLE_GENAI_USE_VERTEXAI` before starting the agent.

**Phoenix shows no traces** — traces made before Phoenix became a standalone service were in memory and are gone. Check `./run.sh status` shows `Phoenix: up`, then send a message.

**A new memory doesn't show up in recall** — Mem0 processes saves in the background. Wait a minute or two, then ask again.

**Architecture page never lights up** — open it from the chat's **Architecture ↗** button, in the same browser as the chat (it listens on a `BroadcastChannel`).
