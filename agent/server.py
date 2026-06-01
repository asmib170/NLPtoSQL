"""FastAPI server for the NLP-to-SQL agent.

Slim entry point — all route logic lives in the routes/ package.
"""

import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Ensure the agent folder is on the path
sys.path.insert(0, os.path.dirname(__file__))

from utils import run_cleanup  # noqa: E402
from utils import CORS_ORIGINS, SERVER_HOST, SERVER_PORT  # noqa: E402

# Run TTL cleanup on startup
_cleanup = run_cleanup()
if any(v > 0 for k, v in _cleanup.items() if k != "ttl_days"):
    print(f"[Cleanup] TTL={_cleanup['ttl_days']}d — "
          f"charts: {_cleanup['charts_deleted']}, "
          f"threads: {_cleanup['threads_deleted']}, "
          f"sessions: {_cleanup['sessions_deleted']}")

# ------------------------------------------------------------------ #
# App setup
# ------------------------------------------------------------------ #
app = FastAPI(title="NLP-to-SQL Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------------------------------------------ #
# Mount route modules
# ------------------------------------------------------------------ #
from routes.health import router as health_router  # noqa: E402
from routes.chat import router as chat_router  # noqa: E402
from routes.threads import router as threads_router  # noqa: E402
from routes.context import router as context_router  # noqa: E402
from routes.charts import router as charts_router  # noqa: E402

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(threads_router)
app.include_router(context_router)
app.include_router(charts_router)

# ------------------------------------------------------------------ #
# Entry point
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host=SERVER_HOST, port=SERVER_PORT, reload=False)
