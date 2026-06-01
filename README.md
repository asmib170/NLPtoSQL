# NLP-to-SQL — AI Data Assistant

An AI-powered conversational interface that lets users query databases using natural language. Ask questions in plain English, get SQL queries, tabular results, charts, and intelligent insights — all through a modern chat UI.

## What It Does

- **Natural language to SQL**: Ask "Which customers spent the most last quarter?" and get the SQL, results, and analysis
- **Automated chart generation**: Produces matplotlib visualizations alongside every query result
- **Conversation memory**: Multi-turn conversations where the agent remembers context within a session
- **Intelligent summaries**: Highlights trends, outliers, and suggests follow-up questions
- **Voice input**: Speak your questions using in-browser Whisper speech-to-text (no server needed)
- **Export**: Download responses or full conversations as HTML or Markdown with embedded charts

## Architecture

```
React (Vite + TypeScript)  ←→  FastAPI (SSE streaming)  ←→  Strands Agent  ←→  AWS Bedrock (Claude Sonnet 4.5)
                                                                    ↓
                                                              SQLite Database
```

- **Frontend**: React chat interface with dark/light mode, glassmorphism sidebar, resizable panels, streaming responses with markdown/table/chart rendering
- **Backend**: FastAPI server with Server-Sent Events for real-time token streaming
- **Agent**: Strands Agents SDK with 5 tools (verify, generate SQL, execute, summarize, chart), extended thinking, and session-based memory
- **Database**: SQLite e-commerce demo (9 tables: users, orders, products, shipping, reviews, etc.)
- **Storage**: Pluggable interfaces for sessions (FileSessionManager → AgentCore Memory), threads (JSON → DynamoDB), charts (local → S3 + CloudFront)

## Key Features

| Feature | Implementation |
|---------|---------------|
| Streaming responses | SSE with thinking/tool/metrics events |
| Extended thinking | Claude 4.5 with 4096 token reasoning budget |
| Session memory | Strands FileSessionManager (AgentCore-ready) |
| Chart generation | LLM generates matplotlib code, executed via subprocess |
| Voice input | Whisper tiny.en running in browser via WebGPU/WASM |
| Multi-thread chat | UUID4 session IDs, thread history with LLM-generated titles |
| Export | HTML (with embedded base64 charts) and Markdown |
| Dark/light mode | CSS variables with theme toggle |
| Config management | JSON config files (dev) → AWS AppConfig (prod) |
| TTL cleanup | Auto-deletes old sessions, threads, and charts |

## Quick Start

```bash
# Prerequisites: Python 3.11+, Node.js 20+, AWS CLI configured

# 1. Setup
uv venv && uv pip install -r requirements.txt
cd webui && npm install && cd ..

# 2. Create the database
python prereq/01_create_db.py
python prereq/02_populate_db.py

# 3. Run (or just double-click start.bat)
start.bat
```

Opens at [http://localhost:3000](http://localhost:3000) with backend on port 8000.

## Project Structure

```
NLPtoSQL/
├── agent/                   # Python backend
│   ├── server.py            # FastAPI entry point
│   ├── nlp_sql_agent.py     # Agent model + system prompt
│   ├── tools/               # Agent tools (SQL, chart, DB inspector)
│   ├── routes/              # API endpoints (chat, threads, context, charts)
│   ├── storage/             # Persistence interfaces (threads, charts)
│   ├── utils/               # Config, LLM utils, session factory, cleanup
│   └── data/                # Runtime data (sessions, threads, charts)
├── webui/                   # React frontend
│   ├── src/components/      # UI components (ChatWindow, MessageBubble, etc.)
│   ├── src/hooks/           # State management (useThreads, useSpeechToText)
│   ├── src/api/             # Backend service layer
│   └── src/utils/           # Export utilities
├── prereq/                  # Database setup scripts
├── docs/                    # Architecture diagrams and documentation
└── start.bat               # One-click launcher
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

Migration steps:
1. Set `APP_ENV=prod` and `SESSION_BACKEND=agentcore`
2. Uncomment AWS implementations in storage and session factory
3. Deploy agent to AgentCore Runtime
4. Build and deploy frontend to S3

## Tech Stack

- **Agent**: Strands Agents SDK, Amazon Bedrock (Claude Sonnet 4.5)
- **Backend**: Python, FastAPI, SQLite, boto3
- **Frontend**: React 18, TypeScript, Vite, react-markdown, Whisper.js
- **Tools**: matplotlib (charts), graphviz (architecture diagrams)
