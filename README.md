# NLP-to-SQL — AI Data Assistant

An AI-powered conversational interface that lets users query databases using natural language. Ask questions in plain English, get SQL queries, tabular results, charts, and intelligent insights, all through a modern chat UI.

## What It Does

This project is a **database-agnostic** AI assistant. While this v1 ships with a demo e-commerce SQLite database, it is designed to work with **any SQL database** (SQLite, PostgreSQL, MySQL, etc.) you connect it to. Simply update the database connection in the config and the system automatically:

- Reads the schema dynamically (tables, columns, relationships)
- Generates 6 relevant sample questions based on YOUR schema using the LLM
- Answers any natural language question about YOUR data

> **Note:** This v1 uses SQLite for the demo. To connect other SQL databases (PostgreSQL, MySQL, etc.), simply set `DB_TYPE` in your config file and provide the connection details. The `db_adapters` package provides ready-to-use adapters for SQLite, PostgreSQL, and MySQL — no code changes required.

**Core capabilities:**
- **Natural language to SQL**: Ask questions like "Which customers spent the most last quarter?". The agent verifies the question is answerable, generates SQL, executes it, and returns results with analysis
- **Automated chart generation**: Produces matplotlib visualizations alongside every query result
- **Conversation memory**: Multi-turn conversations where the agent remembers context within a session (sliding window of last 5 interactions)
- **Intelligent summaries**: Highlights trends, outliers, and suggests follow-up questions
- **Voice input**: Speak your questions using in-browser Whisper speech-to-text (no server needed)
- **Export**: Download responses or full conversations as HTML or Markdown with embedded charts
- **Sortable tables**: Click column headers to sort, download table data as CSV

### Connecting Your Own Database

1. Update `agent/utils/config_files/dev.json` with your database connection:

   **SQLite** (default):
   ```json
   {
     "DB_TYPE": "sqlite",
     "DB_PATH": "prereq/DemoECommerceDB.db"
   }
   ```

   **PostgreSQL** (including RDS / Aurora):
   ```json
   {
     "DB_TYPE": "postgresql",
     "DB_HOST": "your-host.amazonaws.com",
     "DB_PORT": 5432,
     "DB_NAME": "your_database",
     "DB_USER": "admin",
     "DB_PASSWORD": "your_password",
     "DB_SCHEMA": "public"
   }
   ```

   **MySQL** (including RDS / Aurora):
   ```json
   {
     "DB_TYPE": "mysql",
     "DB_HOST": "your-host.amazonaws.com",
     "DB_PORT": 3306,
     "DB_NAME": "your_database",
     "DB_USER": "admin",
     "DB_PASSWORD": "your_password"
   }
   ```

2. Install the required driver (only needed for Postgres/MySQL):
   ```bash
   # Option A: using pyproject.toml extras (recommended)
   uv pip install -e ".[postgres]"   # PostgreSQL
   uv pip install -e ".[mysql]"      # MySQL
   uv pip install -e ".[all-db]"     # Both

   # Option B: install directly
   uv pip install psycopg2-binary    # PostgreSQL
   uv pip install pymysql            # MySQL
   ```

3. Restart the server — the agent reads the schema at startup and adapts automatically
4. The welcome screen will show 6 LLM-generated sample questions based on your schema

## Architecture

![Architecture Diagram](docs/architecture.png)

```
React (Vite + TypeScript)  ←→  FastAPI (SSE streaming)  ←→  Strands Agent  ←→  AWS Bedrock (Claude Sonnet 4.5)
                                                                    ↓
                                                              SQL Database
```

- **Frontend**: React chat interface with dark/light mode, glassmorphism sidebar, resizable panels, streaming responses with markdown/table/chart rendering
- **Backend**: FastAPI server with Server-Sent Events for real-time token streaming
- **Agent**: Strands Agents SDK with 5 tools (verify, generate SQL, execute, summarize, chart), extended thinking, and session-based memory
- **Database**: Pluggable via `db_adapters` — SQLite demo included, PostgreSQL and MySQL ready (9 tables: users, orders, products, shipping, reviews, etc.)
- **Storage**: Pluggable interfaces for sessions (FileSessionManager → AgentCore Memory), threads (JSON → DynamoDB), charts (local → S3 + CloudFront)

## Key Features

| Feature | Implementation |
|---------|---------------|
| Multi-database support | DatabaseAdapter ABC with SQLite, PostgreSQL, MySQL implementations |
| Streaming responses | SSE with thinking/tool/metrics events |
| Extended thinking | Claude 4.5 with 4096 token reasoning budget |
| Session memory | Strands FileSessionManager + SlidingWindowConversationManager |
| Chart generation | LLM generates matplotlib code, executed via subprocess (Windows) or python_repl (Linux) |
| Voice input | Whisper tiny.en running in browser via WebGPU/WASM |
| Multi-thread chat | UUID4 session IDs, thread history with LLM-generated titles & summaries |
| Export | HTML and Markdown with embedded base64 charts |
| Sortable tables | Click-to-sort columns (numeric + date-aware) + CSV download |
| Dark/light mode | CSS variables with animated theme toggle |
| Config management | JSON config files (dev) → AWS AppConfig (prod) |
| TTL cleanup | Auto-deletes old sessions, threads, and charts |
| Input validation | Message length limits, path traversal protection, read-only DB |

## Prerequisites

Before running this project, you need the following set up on your machine:

### 1. Python 3.11+
- Download from [python.org](https://www.python.org/downloads/) or install via your package manager
- Verify: `python --version`

### 2. uv (Python package manager)
- Install: `pip install uv` or via [installation guide](https://docs.astral.sh/uv/getting-started/installation/)
- Verify: `uv --version`

### 3. Node.js 20+ and npm
- Download from [nodejs.org](https://nodejs.org/) (LTS version recommended)
- Verify: `node --version` and `npm --version`

### 4. AWS Account with Bedrock Access

This is the most important prerequisite. The AI agent uses Amazon Bedrock to access Claude Sonnet 4.5.

**Step-by-step:**

1. **Create an AWS Account** (if you don't have one): [aws.amazon.com](https://aws.amazon.com/)

2. **Enable Claude Sonnet 4.5 in Amazon Bedrock**:
   - Go to the [AWS Console](https://console.aws.amazon.com/)
   - Navigate to **Amazon Bedrock** → **Model access** (in the left menu)
   - Click **Manage model access**
   - Check **Anthropic → Claude Sonnet 4.5** (model ID: `us.anthropic.claude-sonnet-4-5-20250929-v1:0`)
   - Click **Save changes** and wait for access to be granted (usually instant)

3. **Create an IAM User with Bedrock permissions**:
   - Go to **IAM** → **Users** → **Create user**
   - Attach the policy: `AmazonBedrockFullAccess` (or a custom policy with `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`)
   - Create an **Access Key** (Security credentials → Create access key → CLI use case)
   - Save the **Access Key ID** and **Secret Access Key**

4. **Install and configure AWS CLI**:
   ```bash
   # Install AWS CLI v2: https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html
   
   # Configure with your credentials:
   aws configure
   ```
   Enter:
   - AWS Access Key ID: `<your key>`
   - AWS Secret Access Key: `<your secret>`
   - Default region: `us-west-2` (or any region where Bedrock + Claude is available)
   - Default output format: `json`

5. **Verify Bedrock access**:
   ```bash
   aws bedrock list-foundation-models --query "modelSummaries[?contains(modelId, 'claude')]" --output table
   ```
   You should see Claude models listed.

### 5. (Optional) Graphviz — for regenerating the architecture diagram
- Download from [graphviz.org](https://graphviz.org/download/)
- Only needed if you want to regenerate `docs/architecture.png`

---

## Quick Start

```bash
# 1. Clone the repo
git clone https://github.com/asmib170/NLPtoSQL.git
cd NLPtoSQL

# 2. Create virtual environment and install Python dependencies
uv venv
uv pip install -e .

# 2b. (Optional) Install a database driver for Postgres or MySQL
# uv pip install -e ".[postgres]"   # PostgreSQL / RDS / Aurora
# uv pip install -e ".[mysql]"      # MySQL / RDS / Aurora

# 3. Install frontend dependencies
cd webui && npm install && cd ..

# 4. Create and populate the demo database
python prereq/01_create_db.py
python prereq/02_populate_db.py

# 5. Run everything (or just double-click start.bat on Windows)
start.bat
```

This starts:
- **Backend** on `http://localhost:8000` (FastAPI + Strands Agent)
- **Frontend** on `http://localhost:3000` (React chat UI)
- Opens your browser automatically

## Project Structure

```
NLPtoSQL/
├── agent/                       # Python backend
│   ├── server.py                # FastAPI entry point (slim — mounts routers)
│   ├── nlp_sql_agent.py         # Agent model config + system prompt
│   ├── db_adapters/             # Database abstraction layer
│   │   ├── base.py              # DatabaseAdapter ABC (unified interface)
│   │   ├── sqlite_adapter.py    # SQLite implementation
│   │   ├── postgres_adapter.py  # PostgreSQL / RDS / Aurora implementation
│   │   ├── mysql_adapter.py     # MySQL / RDS / Aurora implementation
│   │   └── factory.py           # Creates the right adapter from config
│   ├── tools/                   # Agent tools
│   │   ├── sql_tools.py         # verify_question, generate_sql, execute_sql, summarize_results
│   │   └── chart_tool.py        # generate_chart (matplotlib via subprocess/repl)
│   ├── routes/                  # FastAPI route modules
│   │   ├── chat.py              # POST /api/chat (SSE streaming)
│   │   ├── threads.py           # /api/threads CRUD + title generation
│   │   ├── context.py           # GET /api/context (sample questions)
│   │   ├── charts.py            # GET /api/charts/{filename}
│   │   └── health.py            # GET /health
│   ├── utils/                   # Configuration and helpers
│   │   ├── config.py            # Central config (loads from provider)
│   │   ├── config_provider.py   # Interface: File / Env / AWS AppConfig
│   │   ├── config_files/        # dev.json, prod.json.example
│   │   ├── session_factory.py   # Creates session-aware agents
│   │   ├── llm_utils.py         # Direct boto3 Converse API calls
│   │   └── cleanup.py           # TTL-based data cleanup
│   ├── storage/                 # Persistence interfaces
│   │   ├── base.py              # ThreadIndexStorage interface
│   │   ├── json_file_storage.py # Local JSON implementation
│   │   └── chart_storage.py     # ChartStorage interface + LocalChartStorage
│   └── data/                    # Runtime data (gitignored)
│       ├── sessions/            # Strands FileSessionManager data
│       ├── threads/             # Thread metadata JSON files
│       └── charts/              # Generated chart PNGs
├── webui/                       # React frontend
│   ├── src/
│   │   ├── components/          # UI (ChatWindow, MessageBubble, SortableTable, etc.)
│   │   ├── hooks/               # useThreads, useSpeechToText, useTheme
│   │   ├── api/                 # agentService.ts (backend abstraction)
│   │   ├── utils/               # exportUtils.ts (HTML/MD export)
│   │   └── themes.css           # Central theme variables (light/dark)
│   ├── public/                  # favicon.svg
│   └── index.html
├── prereq/                      # Database setup scripts
│   ├── 01_create_db.py          # Creates tables
│   ├── 02_populate_db.py        # Inserts sample data
│   └── 03_verify_db.py          # Prints summary
├── docs/                        # Architecture diagram + documentation
├── start.bat                    # One-click launcher (Windows)
├── start.ps1                    # PowerShell launcher
├── pyproject.toml               # Project metadata + optional dependency groups
└── requirements.txt             # Python dependencies (alternative to pyproject.toml)
```

## Production Migration (AWS AgentCore)

The codebase is designed for a clean migration to AWS:

| Component | Local (Dev) | AWS (Prod) |
|-----------|-------------|------------|
| Server | FastAPI (localhost:8000) | AgentCore Runtime |
| Memory | FileSessionManager | AgentCoreMemorySessionManager |
| Chat history | JSON files | DynamoDB |
| Charts | Local filesystem | S3 + CloudFront |
| Config | config/dev.json | AWS AppConfig |
| Frontend | Vite dev server | S3 + CloudFront |
| Database | SQLite (local) | RDS PostgreSQL / Aurora |

Migration steps:
1. Set `APP_ENV=prod` and `SESSION_BACKEND=agentcore`
2. Uncomment AWS implementations in storage and session factory
3. Deploy agent to AgentCore Runtime
4. Build and deploy frontend to S3

## Tech Stack

- **Agent**: Strands Agents SDK, Amazon Bedrock (Claude Sonnet 4.5 with Extended Thinking)
- **Backend**: Python, FastAPI, SQLite/PostgreSQL/MySQL, boto3
- **Frontend**: React 18, TypeScript, Vite, react-markdown, Whisper.js (Hugging Face Transformers)
- **Tools**: matplotlib (charts), graphviz (architecture diagrams)
- **Storage**: Pluggable interfaces (FileSessionManager, JsonFileThreadIndex, LocalChartStorage, DatabaseAdapter)
