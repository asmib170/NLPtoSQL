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
DB_PATH = str(PROJECT_ROOT / "prereq" / "DemoECommerceDB.db")

# ------------------------------------------------------------------ #
# Data directories
# ------------------------------------------------------------------ #
DATA_DIR = AGENT_DIR / "data"
SESSIONS_DIR = str(DATA_DIR / "sessions")
THREADS_DIR = str(DATA_DIR / "threads")
CHARTS_DIR = str(DATA_DIR / "charts")

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
AWS_REGION = _provider.get("AWS_REGION", "us-east-1")

# ------------------------------------------------------------------ #
# SQL tool
# ------------------------------------------------------------------ #
MAX_DISPLAY_ROWS = int(_provider.get("MAX_DISPLAY_ROWS", 50))

# ------------------------------------------------------------------ #
# Chart tool
# ------------------------------------------------------------------ #
CHART_MODEL_MAX_TOKENS = int(_provider.get("CHART_MODEL_MAX_TOKENS", 4096))

# ------------------------------------------------------------------ #
# Thread title generation
# ------------------------------------------------------------------ #
TITLE_MAX_WORDS = int(_provider.get("TITLE_MAX_WORDS", 6))
SUMMARY_MAX_WORDS = int(_provider.get("SUMMARY_MAX_WORDS", 25))

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
