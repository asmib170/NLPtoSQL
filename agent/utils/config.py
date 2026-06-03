"""Central configuration for the NLP-to-SQL agent.

Loads values from the active ConfigProvider:
  - Dev: reads from config/dev.json
  - Prod: reads from AWS AppConfig (via AwsConfigProvider)

All modules import from here. To change a value:
  - Dev: edit config/dev.json
  - Prod: update the AWS AppConfig document
"""

import os
from pathlib import Path

from .config_provider import get_config_provider

# ------------------------------------------------------------------ #
# Load config from the active provider
# ------------------------------------------------------------------ #
_provider = get_config_provider()

# ------------------------------------------------------------------ #
# Base paths (always derived from filesystem, not config file)
# ------------------------------------------------------------------ #
AGENT_DIR = Path(os.path.dirname(__file__)).parent  # utils/ -> agent/
PROJECT_ROOT = AGENT_DIR.parent

# ------------------------------------------------------------------ #
# Database
# ------------------------------------------------------------------ #
_db_path_config = _provider.get("DB_PATH", "")
if _db_path_config and os.path.isabs(_db_path_config):
    DB_PATH = _db_path_config
elif _db_path_config:
    # Relative path — resolve from project root
    DB_PATH = str(PROJECT_ROOT / _db_path_config)
else:
    # Default fallback
    DB_PATH = str(PROJECT_ROOT / "prereq" / "DemoECommerceDB.db")

# ------------------------------------------------------------------ #
# Data directories (configurable — relative to project root or absolute)
# ------------------------------------------------------------------ #
DATA_DIR = AGENT_DIR / "data"

_sessions_dir = _provider.get("SESSIONS_DIR", "")
SESSIONS_DIR = str(PROJECT_ROOT / _sessions_dir) if _sessions_dir and not os.path.isabs(_sessions_dir) else (_sessions_dir or str(DATA_DIR / "sessions"))

_threads_dir = _provider.get("THREADS_DIR", "")
THREADS_DIR = str(PROJECT_ROOT / _threads_dir) if _threads_dir and not os.path.isabs(_threads_dir) else (_threads_dir or str(DATA_DIR / "threads"))

_charts_dir = _provider.get("CHARTS_DIR", "")
CHARTS_DIR = str(PROJECT_ROOT / _charts_dir) if _charts_dir and not os.path.isabs(_charts_dir) else (_charts_dir or str(DATA_DIR / "charts"))

# Ensure directories exist
for d in [SESSIONS_DIR, THREADS_DIR, CHARTS_DIR]:
    os.makedirs(d, exist_ok=True)

# ------------------------------------------------------------------ #
# Model configuration
# ------------------------------------------------------------------ #
MODEL_ID = _provider.get("MODEL_ID", "us.anthropic.claude-sonnet-4-5-20250929-v1:0")
MODEL_MAX_TOKENS = int(_provider.get("MODEL_MAX_TOKENS", 8192))
THINKING_BUDGET_TOKENS = int(_provider.get("THINKING_BUDGET_TOKENS", 4096))

# ------------------------------------------------------------------ #
# Session management
# ------------------------------------------------------------------ #
SESSION_BACKEND = _provider.get("SESSION_BACKEND", "file")
AGENTCORE_MEMORY_ID = _provider.get("AGENTCORE_MEMORY_ID", "")
AWS_REGION = _provider.get("AWS_REGION", "us-west-2")
CONVERSATION_WINDOW_SIZE = int(_provider.get("CONVERSATION_WINDOW_SIZE", 5))

# ------------------------------------------------------------------ #
# SQL tool
# ------------------------------------------------------------------ #
MAX_DISPLAY_ROWS = int(_provider.get("MAX_DISPLAY_ROWS", 50))

# ------------------------------------------------------------------ #
# Chart tool
# ------------------------------------------------------------------ #
CHART_MODEL_ID = _provider.get("CHART_MODEL_ID", MODEL_ID)
CHART_MODEL_MAX_TOKENS = int(_provider.get("CHART_MODEL_MAX_TOKENS", 4096))
CHART_BG_COLOR = _provider.get("CHART_BG_COLOR", "#1a2332")
CHART_TEXT_COLOR = _provider.get("CHART_TEXT_COLOR", "#ecf0f1")
CHART_COLOR_PALETTE = _provider.get("CHART_COLOR_PALETTE", ["#818cf8", "#f472b6", "#34d399", "#fbbf24", "#a78bfa", "#22d3ee"])
CHART_DPI = int(_provider.get("CHART_DPI", 100))
CHART_SUBPROCESS_TIMEOUT = int(_provider.get("CHART_SUBPROCESS_TIMEOUT", 30))
CHART_MIN_ROWS = int(_provider.get("CHART_MIN_ROWS", 2))

# ------------------------------------------------------------------ #
# Thread title generation
# ------------------------------------------------------------------ #
TITLE_MAX_WORDS = int(_provider.get("TITLE_MAX_WORDS", 6))
SUMMARY_MAX_WORDS = int(_provider.get("SUMMARY_MAX_WORDS", 25))
TITLE_GEN_MAX_TOKENS = int(_provider.get("TITLE_GEN_MAX_TOKENS", 256))

# ------------------------------------------------------------------ #
# Context/sample questions
# ------------------------------------------------------------------ #
SAMPLE_QUESTIONS_COUNT = int(_provider.get("SAMPLE_QUESTIONS_COUNT", 6))
CONTEXT_GEN_MAX_TOKENS = int(_provider.get("CONTEXT_GEN_MAX_TOKENS", 1024))

# ------------------------------------------------------------------ #
# Pricing (per-token, USD)
# ------------------------------------------------------------------ #
PRICING_INPUT_PER_TOKEN = float(_provider.get("PRICING_INPUT_PER_TOKEN", 0.000003))
PRICING_OUTPUT_PER_TOKEN = float(_provider.get("PRICING_OUTPUT_PER_TOKEN", 0.000015))

# ------------------------------------------------------------------ #
# TTL cleanup
# ------------------------------------------------------------------ #
DATA_TTL_DAYS = int(_provider.get("DATA_TTL_DAYS", 30))

# ------------------------------------------------------------------ #
# Server
# ------------------------------------------------------------------ #
SERVER_HOST = _provider.get("SERVER_HOST", "0.0.0.0")
SERVER_PORT = int(_provider.get("SERVER_PORT", 8000))
_cors = _provider.get("CORS_ORIGINS", "*")
CORS_ORIGINS = _cors if isinstance(_cors, list) else _cors.split(",")

# ------------------------------------------------------------------ #
# Python executable (for chart subprocess on Windows)
# ------------------------------------------------------------------ #
VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "Scripts" / "python.exe")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = str(PROJECT_ROOT / ".venv" / "bin" / "python")
if not os.path.exists(VENV_PYTHON):
    VENV_PYTHON = "python"
