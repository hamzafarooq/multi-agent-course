#!/usr/bin/env bash
#
# One-stop runner for the Module 4 customer-support capstone.
#
#   ./run.sh setup     # one-time: install Postgres + extra deps, init DB, seed, write .env
#   ./run.sh           # start everything (Postgres -> MCP Toolbox -> A2A servers -> agent CLI)
#   ./run.sh web       # same stack, but serve the Perplexity-style web UI (http://127.0.0.1:8000)
#   ./run.sh voice     # same stack, but serve the real-time voice (speech-to-speech) UI (http://127.0.0.1:8001)
#   ./run.sh stop      # stop background services (Toolbox, A2A, Postgres)
#   ./run.sh status     # show what's running
#   ./run.sh seed       # re-seed the database from mcp_toolbox/seed.sql
#   ./run.sh logs       # tail the background service logs
#
# Requires: conda, Node.js 18+ (for npx). Fill GOOGLE_API_KEY and MEM0_API_KEY in .env.
#
# Platform support
# ----------------
#   macOS / Linux : run directly  ->  ./run.sh setup   then   ./run.sh
#   Windows       : this is a bash script; native PowerShell/cmd cannot run it.
#                   - Recommended: WSL2 (Ubuntu). Install Miniconda + Node inside WSL,
#                     then run exactly as above. Everything works unchanged.
#                   - Git Bash also works, with one caveat: it has no `lsof`, which this
#                     script uses to free ports on stop/restart. Either install it, or
#                     stop services manually (Ctrl-C in the CLI tears down what it started).
#                   Run from a WSL/Git Bash shell, not PowerShell:  bash run.sh setup
#
# Note: on Windows the Postgres "conda install" path still applies inside WSL; do NOT mix
# a native Windows Postgres install with the WSL one — pick one environment and stay in it.

set -euo pipefail

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_NAME="customer-support"
PY_VERSION="3.12"

# Load the project's .env EARLY (if present) so the ports below honor its profile.
# Skipped during first-run `setup` (no .env yet) -> the defaults apply then.
if [ -f "$PROJECT_DIR/.env" ]; then set -a; . "$PROJECT_DIR/.env"; set +a; fi

# Every port/DB value is env-overridable (defaults = the original values), so a second
# project runs on its own ports just by shipping a different .env — nothing hard-coded.
# s2s profile — defaults are this project's OWN ports/DB, distinct from cascade so both
# run at once. (No PG* in .env — hard-coded here and in cs_agent code.)
PGHOST="127.0.0.1"
PGPORT="5433"
PGDATA="${PGDATA:-$HOME/postgres_data_$PGPORT}"   # per-port so two DBs don't clobber
DB_NAME="toolbox_db"
DB_USER="toolbox_user"
DB_PASS="mysecretpassword"

TOOLBOX_PORT="5001"
TOOLBOX_PKG="@toolbox-sdk/server@1.5.0"
JUDGE_PORT="11002"
MASK_PORT="11003"
WEB_PORT="8001"
VOICE_PORT="8001"

RUN_DIR="$PROJECT_DIR/.run"
mkdir -p "$RUN_DIR"
TOOLBOX_LOG="$RUN_DIR/toolbox.log"
A2A_LOG="$RUN_DIR/a2a.log"
TOOLBOX_PID="$RUN_DIR/toolbox.pid"
A2A_PID="$RUN_DIR/a2a.pid"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
say()  { printf '\033[1;36m==>\033[0m %s\n' "$*"; }
ok()   { printf '\033[1;32m  OK\033[0m %s\n' "$*"; }
warn() { printf '\033[1;33m  ! \033[0m %s\n' "$*"; }
die()  { printf '\033[1;31mERROR:\033[0m %s\n' "$*" >&2; exit 1; }

activate_env() {
  command -v conda >/dev/null 2>&1 || die "conda not found on PATH."
  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  conda env list | grep -qE "^${ENV_NAME}\s" || die "conda env '$ENV_NAME' not found. Run: ./run.sh setup"
  conda activate "$ENV_NAME"
  # AI Studio key path: Vertex must be OFF, regardless of stray shell exports.
  unset GOOGLE_GENAI_USE_VERTEXAI || true
  export PYTHONWARNINGS="${PYTHONWARNINGS:-ignore}"
  export GRPC_VERBOSITY="${GRPC_VERBOSITY:-ERROR}"
  export GLOG_minloglevel="${GLOG_minloglevel:-2}"
}

# Regex of harmless import-time noise to strip from the CLI's stderr. PYTHONWARNINGS
# alone doesn't catch these because the google-adk import chain resets the warnings
# filter. Real errors/tracebacks don't match these patterns and still pass through.
WARN_FILTER='DeprecationWarning|PydanticDeprecated|json_encoders|warnings\.warn|warn_deprecated|pyasn1|ldap3|typeMap is deprecated|MCPServerStreamableHTTP|alembic|path_separator|migration|errors\.pydantic|AiohttpClientSession|aiohttp\.ClientSession|type: ignore'

pg_running() { pg_isready -h "$PGHOST" -p "$PGPORT" >/dev/null 2>&1; }

port_up() { curl -sf -o /dev/null --max-time 2 "$1"; }

wait_for() { # wait_for <url> <label> <tries>
  local url="$1" label="$2" tries="${3:-30}" i=0
  printf '  waiting for %s' "$label"
  while ! port_up "$url"; do
    i=$((i+1)); [ "$i" -ge "$tries" ] && { printf '\n'; return 1; }
    printf '.'; sleep 1
  done
  printf '\n'; ok "$label is up"
}

start_postgres() {
  if pg_running; then ok "PostgreSQL already running"; return; fi
  [ -d "$PGDATA" ] || die "No PG data dir at $PGDATA. Run: ./run.sh setup"
  say "Starting PostgreSQL ($PGDATA)"
  # -o "-p $PGPORT": bind THIS project's port (5433) so it doesn't clash with cascade's 5432.
  pg_ctl -D "$PGDATA" -l "$PGDATA/logfile" -o "-p $PGPORT" -w start >/dev/null
  pg_running || die "PostgreSQL failed to start (see $PGDATA/logfile)"
  ok "PostgreSQL running on $PGHOST:$PGPORT"
}

# ---------------------------------------------------------------------------
# Config generation — this script is the single source of truth for the MCP
# Toolbox config and the DB seed. They live under the gitignored mcp_toolbox/,
# so they are (re)generated here rather than committed separately.
# ---------------------------------------------------------------------------
gen_config_files() {
  mkdir -p "$PROJECT_DIR/mcp_toolbox"

  # Quoted heredoc delimiter ('YAML') keeps $1/$2/$3 literal in the SQL statements.
  cat > "$PROJECT_DIR/mcp_toolbox/tools.yaml" <<'YAML'
# MCP Toolbox configuration — exposes PostgreSQL operations as discoverable tools.
# Loaded by the MCP Toolbox server (@toolbox-sdk/server) and consumed by the agent via
# toolbox_core.ToolboxSyncClient.load_toolset("cs_agent_tools").
#
# GENERATED by run.sh (gen_config_files). Edit the heredoc in run.sh, not this file —
# `./run.sh setup` overwrites it. Credentials match cs_agent/greet.py and seed.sql.

sources:
  cs-postgres:
    kind: postgres
    host: 127.0.0.1
    port: 5433
    database: toolbox_db
    user: toolbox_user
    password: mysecretpassword

tools:
  get-order-status:
    kind: postgres-sql
    source: cs-postgres
    description: >
      Get the status and details of a single order by its numeric order ID.
      Use when a customer asks about a specific order.
    parameters:
      - name: order_id
        type: integer
        description: The numeric order ID, e.g. 5.
    statement: |
      SELECT order_id, customer_email, status, delivery_address, items, order_date, total_amount
      FROM customer_orders
      WHERE order_id = $1;

  find-customer-orders:
    kind: postgres-sql
    source: cs-postgres
    description: >
      Find all orders for a customer by email address, most recent first.
      Use when a customer asks for their full order history.
    parameters:
      - name: email
        type: string
        description: The customer's email address, e.g. alice.jones@example.com.
    statement: |
      SELECT order_id, status, delivery_address, items, order_date, total_amount
      FROM customer_orders
      WHERE customer_email = $1
      ORDER BY order_date DESC;

  update-order-status:
    kind: postgres-sql
    source: cs-postgres
    description: >
      Directly update an order's status. RESTRICTED — the support agent must NOT call this
      directly; it should record intended changes via action-log instead. Present in the
      toolset to mirror the production system.
    parameters:
      - name: order_id
        type: integer
        description: The numeric order ID.
      - name: status
        type: string
        description: New status — one of PROCESSING, SHIPPED, DELIVERED, CANCELLED, RETURNED.
    statement: |
      UPDATE customer_orders
      SET status = $2
      WHERE order_id = $1
      RETURNING order_id, status;

  action-log:
    kind: postgres-sql
    source: cs-postgres
    description: >
      Record an intended action (cancel, return, status change, address or profile update)
      for later processing, instead of mutating core business tables directly.
    parameters:
      - name: user_email
        type: string
        description: The authenticated user's email.
      - name: action_type
        type: string
        description: The action type, e.g. CANCEL_ORDER, RETURN_ORDER, UPDATE_ADDRESS, UPDATE_PROFILE.
      - name: parameters
        type: string
        description: >
          A JSON string with relevant context — order_id, previous status, requested status,
          items, or new address details.
    statement: |
      INSERT INTO actions_log (user_email, action_type, parameters)
      VALUES ($1, $2, $3::jsonb)
      RETURNING id, timestamp, action_type;

toolsets:
  cs_agent_tools:
    - get-order-status
    - find-customer-orders
    - update-order-status
    - action-log
YAML

  cat > "$PROJECT_DIR/mcp_toolbox/seed.sql" <<'SQL'
-- Seed data for the customer support capstone. GENERATED by run.sh (gen_config_files).
-- Idempotent: tables are dropped and recreated so the demo always starts from a known state.

DROP TABLE IF EXISTS actions_log;
DROP TABLE IF EXISTS customer_orders;
DROP TABLE IF EXISTS users;

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
GRANT USAGE ON SCHEMA public TO toolbox_user;
SQL

  ok "Generated mcp_toolbox/tools.yaml and mcp_toolbox/seed.sql"
}

ensure_config_files() {
  [ -f "$PROJECT_DIR/mcp_toolbox/tools.yaml" ] && [ -f "$PROJECT_DIR/mcp_toolbox/seed.sql" ] \
    || gen_config_files
}

# ---------------------------------------------------------------------------
# setup
# ---------------------------------------------------------------------------
cmd_setup() {
  command -v conda >/dev/null 2>&1 || die "conda not found on PATH."
  command -v npx   >/dev/null 2>&1 || die "Node.js/npx not found (need Node 18+)."

  # shellcheck disable=SC1091
  source "$(conda info --base)/etc/profile.d/conda.sh"
  if ! conda env list | grep -qE "^${ENV_NAME}\s"; then
    say "Creating conda env '$ENV_NAME' (Python $PY_VERSION)"
    conda create -y -n "$ENV_NAME" "python=$PY_VERSION"
  fi
  conda activate "$ENV_NAME"

  say "Installing Python requirements"
  pip install -q -r "$PROJECT_DIR/requirements.txt"

  say "Installing observability deps (Phoenix + OpenTelemetry)"
  pip install -q arize-phoenix openinference-instrumentation-google-genai \
    openinference-semantic-conventions
  # Pin the OTel family to 1.42.1 — the highest version google-adk 2.3.0 accepts
  # (it requires >=1.39,<=1.42.1). The README's 1.33.1 pin predates this ADK.
  pip install -q \
    opentelemetry-sdk==1.42.1 \
    opentelemetry-api==1.42.1 \
    opentelemetry-exporter-otlp-proto-http==1.42.1 \
    opentelemetry-semantic-conventions==0.63b1

  if ! command -v initdb >/dev/null 2>&1; then
    say "Installing PostgreSQL into the env"
    conda install -y -c conda-forge postgresql >/dev/null
  fi
  ok "PostgreSQL binaries available"

  say "Generating MCP Toolbox config + seed SQL"
  gen_config_files

  if [ ! -d "$PGDATA" ]; then
    say "Initialising PostgreSQL data dir ($PGDATA)"
    initdb -D "$PGDATA" >/dev/null
  fi
  start_postgres

  say "Creating database, user, and seeding data"
  # Create role/db if missing (connect to default 'postgres' db as the init superuser).
  psql -h "$PGHOST" -p "$PGPORT" -d postgres -tAc \
    "SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'" | grep -q 1 || \
    psql -h "$PGHOST" -p "$PGPORT" -d postgres -c \
      "CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';"
  psql -h "$PGHOST" -p "$PGPORT" -d postgres -tAc \
    "SELECT 1 FROM pg_database WHERE datname='$DB_NAME'" | grep -q 1 || \
    createdb -h "$PGHOST" -p "$PGPORT" "$DB_NAME"
  psql -h "$PGHOST" -p "$PGPORT" -d postgres -c \
    "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" >/dev/null
  cmd_seed

  if [ ! -f "$PROJECT_DIR/.env" ]; then
    say "Writing .env template"
    cat > "$PROJECT_DIR/.env" <<'ENVEOF'
# Use Google AI Studio API key (NOT Vertex). Leave GOOGLE_GENAI_USE_VERTEXAI unset.
PYTHONWARNINGS=ignore

# REQUIRED — fill these in. Do NOT put a "# comment" after the value on the same line:
# dotenv treats it as part of the key. Keep notes on their own line, like these.
# GOOGLE_API_KEY: get it from https://aistudio.google.com/apikey
GOOGLE_API_KEY=
# MEM0_API_KEY: get it from https://app.mem0.ai  (looks like m0-...)
MEM0_API_KEY=

# Optional (PII masking via Google Cloud DLP, input scan via Model Armor).
# Leave blank to run fully local — masking degrades to a no-op.
GOOGLE_CLOUD_PROJECT=
GOOGLE_CLOUD_LOCATION=
MODEL_ARMOR_TEMPLATE_ID=

# Optional (voice / speech-to-speech — used by ./run.sh voice).
# Requires a Gemini Live model your GOOGLE_API_KEY can access.
# VOICE_MODEL=gemini-3.1-flash-live-preview
# VOICE_NAME=Kore

# Observability: TELEMETRY=true launches Arize Phoenix (http://localhost:6006) and
# traces every turn (text + voice). Set false for a fully-off, zero-overhead run
# (e.g. benchmarking).
TELEMETRY=true
ENVEOF
    warn ".env created — you MUST fill GOOGLE_API_KEY and MEM0_API_KEY before ./run.sh"
  else
    ok ".env already exists (left untouched)"
  fi

  echo
  ok "Setup complete. Next: edit .env, then run  ./run.sh"
}

cmd_seed() {
  activate_env 2>/dev/null || { source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$ENV_NAME"; }
  ensure_config_files
  start_postgres
  PGPASSWORD="$DB_PASS" psql -h "$PGHOST" -p "$PGPORT" -d "$DB_NAME" \
    -v ON_ERROR_STOP=1 -f "$PROJECT_DIR/mcp_toolbox/seed.sql" >/dev/null
  ok "Database seeded from mcp_toolbox/seed.sql"
}

# ---------------------------------------------------------------------------
# start
# ---------------------------------------------------------------------------
check_env_keys() {
  set -a; # shellcheck disable=SC1091
  source "$PROJECT_DIR/.env"; set +a
  [ -n "${GOOGLE_API_KEY:-}" ] || die "GOOGLE_API_KEY is empty in .env"
  [ -n "${MEM0_API_KEY:-}" ]   || die "MEM0_API_KEY is empty in .env"
}

kill_port() { # kill whatever is listening on a TCP port (macOS-friendly)
  local pids; pids="$(lsof -ti "tcp:$1" 2>/dev/null || true)"
  [ -n "$pids" ] && kill $pids 2>/dev/null || true
}

stop_bg() {
  for pidfile in "$TOOLBOX_PID" "$A2A_PID"; do
    [ -f "$pidfile" ] || continue
    local pid; pid="$(cat "$pidfile")"
    if kill -0 "$pid" 2>/dev/null; then
      pkill -P "$pid" 2>/dev/null || true   # children (npx spawns node)
      kill "$pid" 2>/dev/null || true
    fi
    rm -f "$pidfile"
  done
  # Belt-and-suspenders: free the known ports regardless of PID bookkeeping.
  kill_port "$TOOLBOX_PORT"; kill_port "$JUDGE_PORT"; kill_port "$MASK_PORT"
}

# Bring up Postgres + MCP Toolbox + A2A servers (shared by `start` and `web`).
start_services() {
  activate_env
  [ -f "$PROJECT_DIR/.env" ] || die "No .env. Run: ./run.sh setup"
  check_env_keys
  ensure_config_files
  start_postgres

  # Clean up any stale background services from a previous run.
  stop_bg

  say "Starting MCP Toolbox on :$TOOLBOX_PORT"
  ( cd "$PROJECT_DIR" && exec npx -y "$TOOLBOX_PKG" \
      --config mcp_toolbox/tools.yaml --enable-api \
      --address 127.0.0.1 --port "$TOOLBOX_PORT" >"$TOOLBOX_LOG" 2>&1 ) &
  echo $! > "$TOOLBOX_PID"
  wait_for "http://127.0.0.1:$TOOLBOX_PORT/api/toolset/cs_agent_tools" "MCP Toolbox" 40 \
    || die "MCP Toolbox did not come up — see $TOOLBOX_LOG"

  say "Starting A2A security servers (Judge :$JUDGE_PORT, Mask :$MASK_PORT)"
  ( cd "$PROJECT_DIR" && exec python -m cs_agent.a2a.run_servers >"$A2A_LOG" 2>&1 ) &
  echo $! > "$A2A_PID"
  wait_for "http://localhost:$JUDGE_PORT/.well-known/agent.json" "Security Judge" 40 \
    || die "Judge A2A server did not come up — see $A2A_LOG"
  wait_for "http://localhost:$MASK_PORT/.well-known/agent.json" "Data Masker" 40 \
    || die "Mask A2A server did not come up — see $A2A_LOG"

  # Tear down background services when the foreground process exits.
  trap 'echo; say "Shutting down services"; stop_bg; ok "stopped"' EXIT INT TERM
}

cmd_start() {
  start_services
  echo
  say "Launching agent CLI (Phoenix UI will open at http://localhost:${PHOENIX_PORT:-6006})"
  echo "----------------------------------------------------------------------"
  # Warnings are silenced in-process (agent_cli sets warnings.showwarning to a
  # no-op). We do NOT filter stderr at the shell here: redirecting stderr makes
  # Python's input() stop using readline, which hides the interactive prompt.
  ( cd "$PROJECT_DIR/cs_agent" && exec python -u agent_cli.py )
}

cmd_web() {
  start_services
  echo
  say "Launching web UI at http://127.0.0.1:$WEB_PORT  (Phoenix at http://localhost:6007)"
  echo "----------------------------------------------------------------------"
  ( cd "$PROJECT_DIR" && WEB_PORT="$WEB_PORT" python -m cs_agent.web \
      2> >(grep --line-buffered -vE "$WARN_FILTER" >&2) )
}

cmd_voice() {
  start_services
  echo
  say "Launching VOICE UI at http://127.0.0.1:$VOICE_PORT  (real-time speech-to-speech)"
  say "Open it in a browser, sign in, then tap the mic. Requires a Gemini Live model."
  echo "----------------------------------------------------------------------"
  # The voice server IS cs_agent.web (its main() serves on VOICE_PORT, default 8001).
  # There is no cs_agent.voice_web module.
  ( cd "$PROJECT_DIR" && VOICE_PORT="$VOICE_PORT" python -m cs_agent.web \
      2> >(grep --line-buffered -vE "$WARN_FILTER" >&2) )
}

# ---------------------------------------------------------------------------
# stop / status / logs
# ---------------------------------------------------------------------------
cmd_stop() {
  say "Stopping background services"
  stop_bg
  if pg_running; then
    # shellcheck disable=SC1091
    source "$(conda info --base)/etc/profile.d/conda.sh"; conda activate "$ENV_NAME" 2>/dev/null || true
    pg_ctl -D "$PGDATA" -w stop >/dev/null 2>&1 && ok "PostgreSQL stopped" || warn "could not stop PostgreSQL"
  fi
  ok "done"
}

cmd_status() {
  activate_env >/dev/null 2>&1 || true   # put pg_isready on PATH
  pg_running && ok "PostgreSQL: up ($PGHOST:$PGPORT)" || warn "PostgreSQL: down"
  port_up "http://127.0.0.1:$TOOLBOX_PORT/api/toolset/cs_agent_tools" && ok "MCP Toolbox: up (:$TOOLBOX_PORT)" || warn "MCP Toolbox: down"
  port_up "http://localhost:$JUDGE_PORT/.well-known/agent.json" && ok "Security Judge: up (:$JUDGE_PORT)" || warn "Security Judge: down"
  port_up "http://localhost:$MASK_PORT/.well-known/agent.json"  && ok "Data Masker: up (:$MASK_PORT)"   || warn "Data Masker: down"
}

cmd_logs() { tail -n 40 -F "$TOOLBOX_LOG" "$A2A_LOG"; }

# ---------------------------------------------------------------------------
# dispatch
# ---------------------------------------------------------------------------
case "${1:-start}" in
  setup)  cmd_setup ;;
  start)  cmd_start ;;
  web)    cmd_web ;;
  voice)  cmd_voice ;;
  stop)   cmd_stop ;;
  status) cmd_status ;;
  seed)   cmd_seed ;;
  logs)   cmd_logs ;;
  *) die "Unknown command '$1'. Use: setup | start | web | voice | stop | status | seed | logs" ;;
esac
