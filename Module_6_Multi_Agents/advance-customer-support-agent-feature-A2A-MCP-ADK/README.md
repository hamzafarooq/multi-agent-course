# Advance Customer Support Agent (CSA)

A sophisticated CLI-based customer support chatbot built with Google ADK (Agent Development Kit) and MCP Toolbox, featuring a multi-layer security pipeline powered by A2A (Agent-to-Agent) protocol, SecurityBlocker regex engine, Google Cloud DLP, and Google Model Armor.

## Features

- **Interactive CLI Interface** -- Natural language conversation with the customer support agent.
- **Smart Order Management** -- Lookup order status, history, and modify order statuses based on business rules.
- **Multi-Layer Security Pipeline** -- Two-layer input validation (sanitization + A2A Judge agent) plus PII masking via A2A Mask agent.
- **SecurityBlocker Engine** -- 100+ compiled regex patterns detecting SQL injection, XSS, command injection, path traversal, obfuscation attacks, and more.
- **Google Cloud DLP Integration** -- Automatic PII masking (16 info types) on agent responses before they reach the user.
- **Google Model Armor** -- Optional cloud-native prompt sanitization via Model Armor API.
- **A2A Protocol (Mandatory)** -- Security Judge and Data Masker run as independent A2A microservices; the CLI communicates with them via JSON-RPC 2.0 / HTTP.
- **Persistent Memory** -- Remembers past conversations and user preferences using Mem0.
- **Session Management** -- Maintains conversation context within a session.
- **Tool Integration** -- Seamless integration with PostgreSQL via MCP Toolbox.

## Architecture
![System Architecture Diagram](diagram.png)

### Key Technologies

1. **Google ADK (Agent Development Kit)**
   - `LlmAgent`: Defines LLM agents with Gemini 2.5 Flash model.
   - `SequentialAgent`: Chains agents into pipelines (Judge -> Mask).
   - `Runner`: Handles agent execution and event streaming.
2. **MCP Toolbox**
   - Connects to PostgreSQL and exposes database operations as MCP tools via HTTP API on `http://127.0.0.1:5000`.
3. **Mem0**
   - Persistent memory storage for long-term context-aware responses.
4. **Security Pipeline**
   - **Layer 1 -- Input Sanitization**: Character whitelisting, 300-char length limit, Google Model Armor API.
   - **Layer 2 -- SecurityBlocker**: 100+ regex patterns for SQL injection, XSS, command injection, path traversal, leetspeak/obfuscation.
   - **Output Masking**: Google Cloud DLP masks 16 types of PII in agent responses (emails, phone numbers, SSNs, credit cards, names, IPs, etc.).
5. **A2A Protocol (Agent-to-Agent) -- Required**
   - JSON-RPC 2.0 over HTTP with agent card discovery, SSE streaming, and in-memory task management.
   - The CLI calls Judge (port 10002) and Mask (port 10003) agents over the A2A protocol for every request.
   - At startup the CLI verifies both A2A servers are reachable and exits if they are not.

---

## Agent Capabilities & Business Logic

The agent is equipped with specific tools to manage the lifecycle of an order:

| Tool | Action | Description |
| :--- | :--- | :--- |
| `get-order-status` | **Query** | Retrieves current status, items, and total for a specific Order ID. |
| `find-customer-orders` | **Query** | Lists all historical orders associated with a customer email. |
| `update-order-status` | **Modify** | Updates order status based on specific customer satisfaction rules. |

---

## Prerequisites

- **Python 3.12+** -- Required Python version
- **Docker** -- For running PostgreSQL database
- **Google Cloud Project** -- For Vertex AI (Gemini), Cloud DLP, and Model Armor
- **gcloud CLI** -- Authenticated with Application Default Credentials
- **Mem0 API Key** -- For persistent memory functionality
- **MCP Toolbox** -- Tool server for database operations

## Installation

### 1. Clone the Repository

```bash
git clone <repository-url>
cd Advance-Customer-Support-Agent
```

### 2. Install Dependencies

Create and activate a virtual environment, then install dependencies:

```bash
# Create virtual environment
python -m venv .venv

# Activate virtual environment (Windows)
.venv\Scripts\activate

# Activate virtual environment (macOS/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Authenticate with Google Cloud

```bash
gcloud auth application-default login
gcloud config set project traversaal-research
```

### 4. Set Up Environment Variables

Copy the example and fill in your values:

```bash
cp .env.example .env
```

Edit `.env` with the following:

```bash
# Use Vertex AI backend (recommended) or set to 0 for AI Studio
GOOGLE_GENAI_USE_VERTEXAI=1

# Only needed if GOOGLE_GENAI_USE_VERTEXAI=0
# GOOGLE_API_KEY=your_google_api_key_here

# Google Cloud Project (required for Vertex AI, DLP masking, Model Armor)
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=us-central1

# Google Model Armor template ID (optional but recommended)
MODEL_ARMOR_TEMPLATE_ID=your-template-id

# Mem0 API Key (required for persistent memory)
MEM0_API_KEY=your_mem0_api_key_here
```

**Where to get each value:**
- **Google Cloud Project**: Your GCP project ID from [Google Cloud Console](https://console.cloud.google.com/)
- **Google API Key** (if not using Vertex AI): From [Google AI Studio](https://makersuite.google.com/app/apikey)
- **Model Armor Template ID**: Create one via `gcloud model-armor templates create` (see below)
- **Mem0 API Key**: From [Mem0 Platform](https://mem0.ai/)



### 5. Set Up PostgreSQL Database

#### Using Docker (Recommended)

```bash
docker run --name some-postgres -e POSTGRES_PASSWORD=mysecretpassword -e POSTGRES_USER=toolbox_user -e POSTGRES_DB=toolbox_db -p 5432:5432 -d postgres
```

#### Access PostgreSQL Terminal (Optional)

```bash
docker exec -it some-postgres psql -U toolbox_user -d toolbox_db
```

### 7. Create Database Schema and Sample Data

Execute the following SQL in your PostgreSQL database:

<details>
<summary><strong>Show SQL (click to expand)</strong></summary>

## User data

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
   ('hannah.m@school.edu', 'Hannah M', TRUE, 94, 'hannah'),
   ('charlie.d@webmail.com', 'Charlie D', TRUE, 88, 'charlie'),
   ('julia.child@kitchen.com', 'Julia Child', TRUE, 75, 'julia'),
   ('evan.g@bizcorp.com', 'Evan G', TRUE, 56, 'evan'),
   ('alice.jones@example.com', 'Alice Jones', FALSE, 42, 'alice'),
   ('ian.malcolm@chaos.com', 'Ian Malcolm', FALSE, 31, 'ian'),
   ('diana.prince@hero.net', 'Diana Prince', FALSE, 23, 'diana'),
   ('george.j@jungle.com', 'George J', FALSE, 19, 'george'),
   ('bob.smith@techmail.com', 'Bob Smith', FALSE, 15, 'bob'),
   ('fiona.shrek@swamp.com', 'Fiona Shrek', FALSE, 12, 'fiona');
```

## Customer Order Data

```sql
-- 📦 Create customer_orders table
CREATE TABLE customer_orders (
    order_id SERIAL PRIMARY KEY,
    customer_email VARCHAR(100) NOT NULL,
    delivery_address VARCHAR(255),
    status VARCHAR(20) CHECK (status IN ('PROCESSING', 'SHIPPED', 'DELIVERED', 'CANCELLED', 'RETURNED')),
    items JSONB,
    order_date TIMESTAMPTZ DEFAULT NOW(),
    total_amount DECIMAL(10, 2)
);

-- 🛒 Insert demo customer orders
INSERT INTO customer_orders (customer_email, delivery_address, status, items, order_date, total_amount) VALUES
('alice.jones@example.com', '123 Market St, Springfield', 'DELIVERED', '[{"product": "Ergonomic Office Chair", "qty": 1, "price": 250.00}]', NOW() - INTERVAL '6 months', 250.00),
('alice.jones@example.com', '123 Market St, Springfield', 'DELIVERED', '[{"product": "Wireless Mouse", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '3 months', 25.00),
('alice.jones@example.com', '123 Market St, Springfield', 'DELIVERED', '[{"product": "Mouse Pad", "qty": 1, "price": 10.00}]', NOW() - INTERVAL '3 months', 10.00),
('alice.jones@example.com', '123 Market St, Springfield', 'SHIPPED', '[{"product": "Mechanical Keyboard", "qty": 1, "price": 120.00}]', NOW() - INTERVAL '2 days', 120.00),
('alice.jones@example.com', '123 Market St, Springfield', 'PROCESSING', '[{"product": "USB-C Hub", "qty": 1, "price": 45.00}]', NOW() - INTERVAL '1 hour', 45.00),

('bob.smith@techmail.com', '88 Tech Ave, Seattle', 'DELIVERED', '[{"product": "Gaming Laptop 15-inch", "qty": 1, "price": 1500.00}]', NOW() - INTERVAL '1 year', 1500.00),
('bob.smith@techmail.com', '88 Tech Ave, Seattle', 'DELIVERED', '[{"product": "Laptop Stand", "qty": 1, "price": 50.00}]', NOW() - INTERVAL '1 year', 50.00),
('bob.smith@techmail.com', '88 Tech Ave, Seattle', 'CANCELLED', '[{"product": "VR Headset", "qty": 1, "price": 400.00}]', NOW() - INTERVAL '10 days', 400.00),
('bob.smith@techmail.com', '88 Tech Ave, Seattle', 'PROCESSING', '[{"product": "Curved Monitor 34-inch", "qty": 1, "price": 450.00}]', NOW() - INTERVAL '4 hours', 450.00),

('charlie.d@webmail.com', '12 Oak Rd, Denver', 'DELIVERED', '[{"product": "AA Batteries (Pack of 12)", "qty": 2, "price": 15.00}]', NOW() - INTERVAL '45 days', 30.00),
('charlie.d@webmail.com', '12 Oak Rd, Denver', 'DELIVERED', '[{"product": "HDMI Cable 6ft", "qty": 3, "price": 8.00}]', NOW() - INTERVAL '20 days', 24.00),

('diana.prince@hero.net', '5 Hero Ln, Metropolis', 'DELIVERED', '[{"product": "Smart Watch Gen 5", "qty": 1, "price": 299.00}]', NOW() - INTERVAL '60 days', 299.00),
('diana.prince@hero.net', '5 Hero Ln, Metropolis', 'RETURNED', '[{"product": "Running Shoes", "qty": 1, "price": 120.00}]', NOW() - INTERVAL '15 days', 120.00),

('evan.g@bizcorp.com', '200 Business Pkwy, Austin', 'SHIPPED', '[{"product": "Office Desk", "qty": 2, "price": 300.00}]', NOW() - INTERVAL '1 day', 600.00),
('evan.g@bizcorp.com', '200 Business Pkwy, Austin', 'SHIPPED', '[{"product": "Filing Cabinet", "qty": 2, "price": 150.00}]', NOW() - INTERVAL '1 day', 300.00),

('fiona.shrek@swamp.com', '7 Swamp Rd, Bayou', 'CANCELLED', '[{"product": "Skincare Gift Set", "qty": 1, "price": 85.00}]', NOW() - INTERVAL '5 days', 85.00),

('george.j@jungle.com', '9 Jungle Path, Amazonia', 'PROCESSING', '[{"product": "Bluetooth Speaker", "qty": 1, "price": 60.00}]', NOW() - INTERVAL '30 minutes', 60.00),

('hannah.m@school.edu', '4 Campus Dr, Boston', 'DELIVERED', '[{"product": "Notebook Pack", "qty": 5, "price": 12.00}]', NOW() - INTERVAL '4 months', 60.00),
('hannah.m@school.edu', '4 Campus Dr, Boston', 'DELIVERED', '[{"product": "Gel Pens", "qty": 2, "price": 5.00}]', NOW() - INTERVAL '4 months', 10.00),

('ian.malcolm@chaos.com', '22 Chaos Blvd, San Diego', 'DELIVERED', '[{"product": "Professional Camera Lens", "qty": 1, "price": 2200.00}]', NOW() - INTERVAL '8 months', 2200.00),

('julia.child@kitchen.com', '10 Kitchen St, Portland', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '3 months', 25.00),
('julia.child@kitchen.com', '10 Kitchen St, Portland', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '2 months', 25.00),
('julia.child@kitchen.com', '10 Kitchen St, Portland', 'DELIVERED', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '1 month', 25.00),
('julia.child@kitchen.com', '10 Kitchen St, Portland', 'PROCESSING', '[{"product": "Coffee Beans 1kg", "qty": 1, "price": 25.00}]', NOW() - INTERVAL '3 hours', 25.00),
('julia.child@kitchen.com', '10 Kitchen St, Portland', 'PROCESSING', '[{"product": "Descaling Kit", "qty": 1, "price": 15.00}]', NOW() - INTERVAL '3 hours', 15.00);
```

Actions Log

```sql

-- 🧾 Log of simulated customer support actions (no real data changes)
CREATE TABLE actions_log (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ DEFAULT NOW(),
    user_email VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    parameters JSONB NOT NULL
);
```

</details>

### 8. Configure Database Connection

Update `mcp_toolbox/tools.yaml` with your database credentials:

```yaml
sources:
  customer_db:
    kind: postgres
    host: 127.0.0.1
    port: 5432
    database: toolbox_db
    user: toolbox_user
    password: mysecretpassword  # Update this to match your Docker setup
```

### 9. Install and Configure MCP Toolbox Server

Download the MCP Toolbox binary version 0.21.0 for **your OS and architecture** from the releases page:  
[genai-toolbox](https://github.com/googleapis/genai-toolbox/releases)

Once downloaded:

```bash
# 1) Move the toolbox binary into the mcp_toolbox folder
mv toolbox* mcp_toolbox/

# 2) (Linux/macOS only) Make the toolbox binary executable
cd mcp_toolbox
chmod +x toolbox
```

On Windows, ensure the downloaded file is named `toolbox.exe` and placed inside the `mcp_toolbox` folder.

The MCP Toolbox must be running before starting the agent. In a separate terminal:

```bash
# Navigate to toolbox directory
cd mcp_toolbox

# Start the toolbox server
./toolbox.exe --tools-file tools.yaml

# Or with UI enabled [Recommended]
./toolbox.exe --tools-file tools.yaml --ui
```

The toolbox will start on `http://127.0.0.1:5000` by default.

## Usage

### Quick Start (4 terminals)

**Terminal 1 -- Start PostgreSQL** (if using Docker):

```bash
docker start some-postgres
```

**Terminal 2 -- Start MCP Toolbox**:

```bash
cd mcp_toolbox
./toolbox.exe --tools-file tools.yaml
```

**Terminal 3 -- Start A2A Servers** (Security Judge + Data Masker):

```bash
python -m cs_agent.a2a.run_servers
```

Wait until you see both servers report `Started server on ...` before proceeding.

**Terminal 4 -- Run the Customer Support CLI**:

```bash
cd cs_agent
python agent_cli.py
```

The agent will:
1. Verify both A2A agents are reachable (Judge on `:10002`, Mask on `:10003`)
2. Display the user list from PostgreSQL
3. Ask you to pick a user ID
4. Start the conversation loop with all security layers active via A2A

### Running with ADK Web Interface

For a web-based interface:

```bash
# Terminal 1: Start MCP Toolbox with UI
cd mcp_toolbox
./toolbox.exe --tools-file tools.yaml --ui

# Terminal 2: Start ADK Web interface
adk web
```

### A2A Servers (Required)

The A2A servers **must** be running before you start the CLI. They are launched in Terminal 3 above.

| Server | Port | Agent Card | Purpose |
|:-------|:-----|:-----------|:--------|
| Security Judge | `10002` | `http://localhost:10002/.well-known/agent.json` | LLM-powered input security evaluation |
| Data Masker | `10003` | `http://localhost:10003/.well-known/agent.json` | PII masking via Google Cloud DLP |

Any A2A-compatible client can also call them directly via JSON-RPC at the `/rpc` endpoint.

You can override host/port via environment variables: `A2A_JUDGE_HOST`, `A2A_JUDGE_PORT`, `A2A_MASK_HOST`, `A2A_MASK_PORT`.

### Running the Security Evaluation Suite

Test the SecurityBlocker against 95 scenarios (no servers or API keys needed):

```bash
python -m cs_agent.evaluation.evaluator
```

Runs 57 malicious attack patterns and 38 legitimate queries, printing a pass/fail summary.

## Project Structure

```
Advance-Customer-Support-Agent/
├── cs_agent/                       # Main agent package
│   ├── agent_cli.py                # CLI entry point (A2A-powered security + masking)
│   ├── memory.py                   # Mem0 memory integration
│   ├── greet.py                    # User greeting flow (PostgreSQL)
│   ├── prompts.py                  # Agent instruction prompts
│   │
│   ├── security/                   # Security pipeline components
│   │   ├── blocker.py              # SecurityBlocker -- 100+ regex patterns
│   │   ├── sanitizer.py            # Input sanitizer + Model Armor API
│   │   └── masker.py               # Google Cloud DLP PII masking (16 types)
│   │
│   ├── agents/                     # ADK agent definitions
│   │   ├── judge_agent.py          # Security Judge LlmAgent + FunctionTool
│   │   ├── mask_agent.py           # Data Masking LlmAgent + FunctionTool
│   │   └── pipeline.py             # SequentialAgent (Judge -> Mask)
│   │
│   ├── a2a/                        # A2A protocol infrastructure
│   │   ├── types.py                # 25+ Pydantic models (Task, Message, AgentCard, etc.)
│   │   ├── utils.py                # Modality compatibility helpers
│   │   ├── server.py               # A2AServer -- FastAPI JSON-RPC 2.0 server
│   │   ├── task_manager.py         # InMemory task managers (Judge + Mask)
│   │   ├── factories.py            # Server factory functions with AgentCard config
│   │   ├── client.py               # Async A2A client (sync + SSE streaming)
│   │   └── run_servers.py          # Multi-threaded A2A server launcher
│   │
│   └── evaluation/                 # Security evaluation framework
│       ├── evaluator.py            # SimpleEvaluator test harness
│       ├── test_scenarios.json     # 95 test cases (57 malicious + 38 legitimate)
│       └── test_config.json        # Evaluation configuration
│
├── mcp_toolbox/                    # MCP Toolbox configuration
│   ├── toolbox.exe                 # MCP Toolbox executable
│   └── tools.yaml                  # Database tool definitions
│
├── Examples/                       # Example conversation transcripts
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── diagram.png                     # Architecture diagram
└── README.md                       # This file
```

## How It Works

### Request Flow

```
User Input
    |
    v
[Layer 1] sanitize_input()                          (local, in-process)
    |-- Character whitelist (a-z, 0-9, basic punctuation)
    |-- 300-character length limit
    |-- Google Model Armor API (if configured)
    |
    v
[Layer 2] Security Judge A2A Agent                   (HTTP :10002)
    |-- CLI sends JSON-RPC request to Judge server
    |-- Judge LlmAgent runs 100+ regex patterns via evaluator tool
    |-- Returns original text or "BLOCKED"
    |
    v
Customer Support Agent (Gemini 2.5 Flash)            (local, in-process)
    |-- Searches Mem0 memory for past conversations
    |-- Uses MCP Toolbox tools for database queries
    |-- Generates response
    |
    v
[Output] Data Masker A2A Agent                       (HTTP :10003)
    |-- CLI sends JSON-RPC request to Mask server
    |-- Mask LlmAgent calls Google Cloud DLP via mask_text tool
    |-- Returns PII-masked text (16 info types)
    |
    v
Displayed to User
```

### Agent Configuration

- **Model**: `gemini-2.5-flash` (Google Gemini via Vertex AI)
- **Tools**: Database tools from MCP Toolbox + Mem0 memory search
- **Session Service**: `InMemorySessionService` (in-memory session storage)
- **Instructions**: Defined in `cs_agent/prompts.py`
- **Security**: 2-layer input validation (local sanitizer + A2A Judge) + A2A Mask output masking

### Tool Definitions

Tools are defined in `mcp_toolbox/tools.yaml`:

- **`get-order-status`**: Retrieves order details by numeric Order ID
  - Parameter: `order_id` (integer)
  - Returns: status, order_date, total_amount, items

- **`find-customer-orders`**: Finds all orders for a customer email
  - Parameter: `customer_email` (string)
  - Returns: List of orders sorted by date (newest first)

- **`update-order-status`**: Updates the status of an order
  - Parameters: `order_id` (integer), `new_status` (string, e.g. `CANCELLED`, `RETURNED`)
  - Returns: order_id, status, order_date, total_amount

- **`action-log`**: Writes an audit record for an action
  - Parameters: `user_email` (string), `action_type` (string), `parameters_json` (stringified JSON)
  - Returns: id, timestamp, user_email, action_type, parameters

## Agent Capabilities

The customer support agent can:

- **Order Status Queries**: "What's the status of order 5?"
- **Customer Order History**: "Show me all orders for alice@example.com"
- **Order Modifications**: Cancel pending orders, initiate returns for delivered items
- **Natural Language Processing**: Understands various phrasings
- **Context Awareness**: Remembers past conversations via Mem0
- **Professional Responses**: Friendly, clear, and helpful communication
- **Error Handling**: Gracefully handles missing data or invalid queries

The security pipeline blocks:

- **SQL Injection**: `DROP TABLE`, `UNION SELECT`, stacked queries, blind injection, time-based attacks
- **XSS Attacks**: `<script>` tags, event handlers, `javascript:` URIs
- **Command Injection**: `sudo`, `rm -rf`, `wget`, `curl`, shell chaining
- **Path Traversal**: `../../etc/passwd`, Windows system directory access
- **Obfuscation**: Leetspeak (`DR0P`), URL encoding (`%53%45%4c%45%43%54`), unicode fullwidth, double encoding
- **Prompt Injection**: "Ignore previous instructions", jailbreak attempts

## Assumptions

1. **Database Schema**: The PostgreSQL database has a `customer_orders` table with the expected schema (see SQL above)

2. **MCP Toolbox**: The MCP Toolbox server is running on `http://127.0.0.1:5000` before starting the agent

3. **API Keys**: Valid Google API key and Mem0 API key are set in `.env` file

4. **User Identification**: The agent uses a default `USER_ID` ("demo" in `agent.py`, "demo_cli" in `agent_cli.py`). In production, this should be dynamically set per user

5. **Session Management**: Sessions are stored in-memory. For production, consider using a persistent session service

6. **Order ID Format**: Order IDs are numeric integers (e.g., 1, 5, 20). The agent handles normalization automatically

7. **Customer Identification**: Customers are identified by email address, not customer ID

8. **Memory Storage**: Mem0 is used for persistent memory. Conversations are saved at the end of each session

## Troubleshooting

### Error: FATAL: A2A servers are not running

**Solution**: Start the A2A servers in a separate terminal before launching the CLI:
```bash
python -m cs_agent.a2a.run_servers
```
Wait for both `Started server on ...` messages, then start the CLI.

### Error: Connection refused to http://127.0.0.1:5000

**Solution**: Ensure MCP Toolbox is running:
```bash
cd mcp_toolbox
./toolbox.exe --tools-file tools.yaml
```

### Error: Database connection failed

**Solutions**:
- Verify PostgreSQL container is running: `docker ps`
- Check database credentials in `mcp_toolbox/tools.yaml`
- Ensure database exists: `docker exec -it some-postgres psql -U toolbox_user -d toolbox_db`

### Error: Missing API key

**Solution**: Create `.env` file with required keys (see `.env.example`):
```bash
cp .env.example .env
# Edit .env with your values
```

### Error: cannot import name 'dlp_v2' from 'google.cloud'

**Solution**: Install the DLP package:
```bash
pip install google-cloud-dlp
```

### Error: Module not found

**Solution**: Install all dependencies:
```bash
pip install -r requirements.txt
```

### Unclosed client session warnings

**Status**: These are expected warnings from the async HTTP client and can be safely ignored. They don't affect functionality.

### Agent not using tools correctly

**Solution**: 
- Check MCP Toolbox logs for tool execution errors
- Verify tool definitions in `mcp_toolbox/tools.yaml`
- Ensure database schema matches tool expectations

### Memory not persisting

**Solution**:
- Verify `MEM0_API_KEY` is set correctly
- Check Mem0 API service status
- Review `cs_agent/memory.py` for correct user_id usage

## Development

### Modifying Agent Behavior

- **Prompts**: Edit `cs_agent/prompts.py` to change agent instructions
- **Tools**: Modify `mcp_toolbox/tools.yaml` to add/change database tools
- **Memory**: Adjust memory functions in `cs_agent/memory.py`

### Adding New Tools

1. Add tool definition to `mcp_toolbox/tools.yaml`
2. Add tool to `cs_agent_tools` toolset
3. Restart MCP Toolbox server
4. The agent will automatically have access to the new tool

## Resources

- **Google ADK Documentation**: [https://google.github.io/adk-docs/](https://google.github.io/adk-docs/)
- **A2A Protocol Specification**: [https://github.com/google/A2A](https://github.com/google/A2A)
- **Google Cloud DLP**: [https://cloud.google.com/dlp/docs](https://cloud.google.com/dlp/docs)
- **Google Model Armor**: [https://cloud.google.com/security-command-center/docs/model-armor-overview](https://cloud.google.com/security-command-center/docs/model-armor-overview)
- **MCP Toolbox**: [Getting Started Guide](https://colab.research.google.com/github/googleapis/genai-toolbox/blob/main/docs/en/getting-started/colab_quickstart.ipynb)
- **Mem0 Documentation**: [https://docs.mem0.ai/](https://docs.mem0.ai/)
- **MCP Protocol**: [Model Context Protocol](https://modelcontextprotocol.io/)

