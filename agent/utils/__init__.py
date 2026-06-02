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
    MAX_DISPLAY_ROWS,
    CHART_MODEL_ID, CHART_MODEL_MAX_TOKENS, CHART_BG_COLOR, CHART_TEXT_COLOR,
    CHART_COLOR_PALETTE, CHART_DPI, CHART_SUBPROCESS_TIMEOUT, CHART_MIN_ROWS,
    TITLE_MAX_WORDS, SUMMARY_MAX_WORDS, TITLE_GEN_MAX_TOKENS,
    SAMPLE_QUESTIONS_COUNT, CONTEXT_GEN_MAX_TOKENS,
    PRICING_INPUT_PER_TOKEN, PRICING_OUTPUT_PER_TOKEN,
    DATA_TTL_DAYS, SERVER_HOST, SERVER_PORT, CORS_ORIGINS,
    VENV_PYTHON,
)
from .llm_utils import converse, converse_json
from .cleanup import run_cleanup
from .session_factory import get_agent_for_session, create_session_manager
