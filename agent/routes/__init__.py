"""API route modules.

Each sub-module defines a FastAPI APIRouter that is mounted by server.py:
  - health:  GET /health
  - chat:    POST /api/chat (SSE streaming)
  - threads: CRUD /api/threads
  - context: GET /api/context (LLM-generated sample questions)
  - charts:  GET /api/charts/{filename}
"""
