"""Utility modules — config, LLM helpers, cleanup.

Modules:
  - config: Central configuration values (loaded from config provider)
  - config_provider: Interface + implementations for config sources (file, AWS)
  - llm_utils: Lightweight boto3 Converse API calls (no Agent overhead)
  - cleanup: TTL-based data cleanup
"""

from .config import (
    AGENT_DIR, PROJECT_ROOT, DB_PATH,
    SESSIONS_DIR, THREADS_DIR, CHARTS_DIR,
    MODEL_ID, MODEL_MAX_TOKENS, THINKING_BUDGET_TOKENS,
    SESSION_BACKEND, AGENTCORE_MEMORY_ID, AWS_REGION,
    MAX_DISPLAY_ROWS, CHART_MODEL_MAX_TOKENS,
    TITLE_MAX_WORDS, SUMMARY_MAX_WORDS,
    DATA_TTL_DAYS, SERVER_HOST, SERVER_PORT, CORS_ORIGINS,
    VENV_PYTHON,
)
from .llm_utils import converse, converse_json
from .cleanup import run_cleanup
from .session_factory import get_agent_for_session, create_session_manager
