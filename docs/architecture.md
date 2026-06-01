# NLP-to-SQL — Architecture

![Architecture Diagram](architecture.png)

## Overview

This application allows users to ask natural language questions about an e-commerce database and receive structured, insightful answers — complete with SQL queries, markdown tables, trend analysis, and follow-up suggestions. The system runs locally on a laptop with a single external dependency: AWS Bedrock for the LLM.

---

## Components

### 1. React Web App (localhost:3000)

The frontend is a single-page React application built with Vite and TypeScript. It provides a professional chat interface with:

- **Chat Window** — Renders the conversation with full markdown support (tables, code blocks, bold, lists). Responses stream in real-time via Server-Sent Events (SSE).
- **Input Bar** — Located in the right sidebar. Accepts the user's natural language question and sends it along with a `session_id` (UUID4, 36 characters) to the backend.
- **Sidebar** — Displays chat history as a list of threads. Each thread is identified by its first question. Users can switch between threads or start a new chat. Thread metadata is persisted so history survives page refreshes.
- **Collapsible Sections** — Agent responses are structured into "Thinking" (auto-collapses after streaming), "Results" (always visible), "SQL Query" (collapsed by default), and "Suggested Follow-Up" (clickable pills).
- **Metrics Popup** — An info icon on each response shows TTFT, latency, input/output tokens, cache usage, and estimated cost.
- **Dark/Light Mode** — Full theme support with CSS variables.

### 2. FastAPI Server (localhost:8000)

A lightweight Python server that acts as the bridge between the React frontend and the Strands Agent. It handles:

- **`POST /api/chat`** — Accepts `{message, thread_id}`. Creates a session-aware agent, streams the response back as SSE events (`data:`, `[THINKING]`, `[TOOL]`, `[METRICS]`, `[DONE]`).
- **`GET /api/threads`** — Returns thread metadata for the sidebar.
- **`GET /api/threads/{id}`** — Returns thread metadata plus conversation messages loaded from the session storage.
- **`POST /api/threads`** — Creates a new thread with a UUID4 session ID.
- **`PUT /api/threads/{id}`** — Updates thread title/message count.
- **`DELETE /api/threads/{id}`** — Deletes thread metadata and session files.
- **`GET /api/context`** — Calls the LLM with the database schema to generate 6 sample questions and a description for the welcome screen.
- **`GET /health`** — Health check.

The server uses CORS middleware to allow the React dev server to communicate with it.

### 3. Strands Agent (with Extended Thinking)

The core intelligence layer. A Strands Agents SDK `Agent` instance configured with:

- **Model**: Claude Sonnet 4.5 on Amazon Bedrock, with extended thinking enabled (4096 token budget).
- **Session Manager**: `FileSessionManager` that automatically persists and restores conversation history per session. This means the agent remembers previous questions within the same thread.
- **System Prompt**: Instructs the agent to follow a strict 4-step workflow and format responses as markdown with tables.
- **4 Custom Tools** (described below).

The agent is created fresh per request with the session history loaded, ensuring conversation continuity without keeping agents in memory permanently.

### 4. Tools

The agent has 4 tools that it calls in sequence for every question:

| Step | Tool | What it does |
|------|------|-------------|
| 1 | `verify_question` | Reads the database schema dynamically (from `sqlite_master`) and checks if the question can be answered. Returns relevant tables. |
| 2 | `generate_sql` | Provides the full schema to the LLM and asks it to produce a valid SQLite SELECT statement. |
| 3 | `execute_sql` | Runs the generated SQL against the SQLite database. Only SELECT statements are allowed (safety guard). Returns results as JSON. |
| 4 | `summarize_results` | Computes basic statistics (min, max, avg, frequency distributions) on the results and asks the LLM to produce highlights, trends, outliers, and follow-up suggestions. |

All tools read the schema dynamically via `db_inspector.py` — nothing is hardcoded. If you swap the database file, the tools adapt automatically.

### 5. SQLite Database (DemoECommerceDB)

A local SQLite database with 9 tables representing a realistic e-commerce system:

- `users` — 15 customers
- `addresses` — shipping/billing addresses
- `categories` — hierarchical product categories
- `products` — 20 products with SKUs and prices
- `orders` — 49 orders with status, totals, payment
- `order_items` — 131 line items
- `shipping` — carrier, tracking, delivery status
- `reviews` — product ratings (1-5 stars)
- `coupons` — discount codes

The database is created and populated by scripts in the `prereq/` folder.

### 6. Session Storage (FileSessionManager)

Strands' built-in `FileSessionManager` stores the full conversation state (including tool calls and results) in:

```
agent/data/sessions/session_<uuid>/agents/agent_default/messages/
```

Each message is a separate JSON file. This allows the agent to maintain context across multiple turns within the same thread. When the user asks a follow-up question, the agent has full memory of what was discussed before.

### 7. Amazon Bedrock (AWS Cloud)

The only cloud dependency. The agent calls Amazon Bedrock's Converse API to:

- Generate SQL from natural language
- Reason about whether a question is answerable
- Analyse query results and produce insights
- Generate sample questions from the schema

The model used is `us.anthropic.claude-sonnet-4-5-20250929-v1:0` with:
- Extended thinking (4096 token budget) for better reasoning
- Temperature = 1 (required when thinking is enabled)
- Max tokens = 8192
- Streaming enabled for real-time token delivery

---

## Data Flow (per question)

1. **User types a question** in the sidebar input bar
2. **React sends** `POST /api/chat {message: "...", thread_id: "uuid"}` to FastAPI
3. **FastAPI creates** a Strands Agent with `FileSessionManager(session_id=thread_id)` — this loads any previous conversation for that thread
4. **Agent calls Tool 1** (`verify_question`) — checks the schema can answer the question
5. **Agent calls Tool 2** (`generate_sql`) — LLM produces a SQL SELECT statement
6. **Agent calls Tool 3** (`execute_sql`) — runs the SQL against SQLite, gets results
7. **Agent calls Tool 4** (`summarize_results`) — LLM analyses the data and produces insights
8. **Throughout steps 4-7**, tokens stream back to FastAPI as SSE events
9. **React renders** the streaming response in real-time with markdown formatting
10. **After completion**, metrics (TTFT, tokens, cost) are sent as a final SSE event
11. **Session manager** automatically saves the full conversation to disk

---

## Future State: AWS AgentCore Runtime

When deploying to production, the architecture simplifies:

| Current (Local) | Future (AgentCore) |
|---|---|
| FastAPI server | AgentCore Runtime endpoint (no server needed) |
| FileSessionManager | AgentCoreMemorySessionManager |
| Local SQLite | Could be RDS/Aurora or keep SQLite in session storage |
| React on localhost | Hosted on S3 + CloudFront |

The migration requires:
1. Set `SESSION_BACKEND=agentcore` environment variable
2. Uncomment 6 lines in `_create_session_manager()` in `server.py`
3. Install `bedrock-agentcore[strands-agents]` package
4. Deploy the agent code to AgentCore Runtime

The React frontend only needs its `VITE_AGENT_URL` changed from `localhost:8000` to the AgentCore endpoint URL. No other frontend changes required.
