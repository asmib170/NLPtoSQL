"""Database adapter factory.

Reads DB_TYPE from the config provider and instantiates the appropriate
DatabaseAdapter implementation. The factory extracts config values and
passes them into the adapter constructor — adapters themselves have no
dependency on the config system.
"""

import os
from pathlib import Path
from typing import Any

from .base import DatabaseAdapter

# Module-level singleton
_adapter: DatabaseAdapter | None = None


def get_db_adapter() -> DatabaseAdapter:
    """Return the active database adapter (created once, reused).

    Config keys used:
        DB_TYPE   - "sqlite" (default), "postgresql", "mysql"
        DB_PATH   - path to SQLite file (sqlite only)
        DB_HOST   - hostname (postgres/mysql)
        DB_PORT   - port number (postgres/mysql)
        DB_NAME   - database name (postgres/mysql)
        DB_USER   - username (postgres/mysql)
        DB_PASSWORD - password (postgres/mysql)

    Returns:
        A connected DatabaseAdapter instance.

    Raises:
        ValueError: If DB_TYPE is not supported.
    """
    global _adapter
    if _adapter is not None:
        return _adapter

    # Import here to avoid circular imports (config imports happen at module level)
    from utils.config_provider import get_config_provider

    provider = get_config_provider()
    db_type = provider.get("DB_TYPE", "sqlite").lower()

    if db_type == "sqlite":
        _adapter = _create_sqlite_adapter(provider)
    elif db_type in ("postgresql", "postgres"):
        _adapter = _create_postgres_adapter(provider)
    elif db_type == "mysql":
        _adapter = _create_mysql_adapter(provider)
    else:
        raise ValueError(
            f"Unsupported DB_TYPE: '{db_type}'. "
            f"Supported values: sqlite, postgresql, mysql"
        )

    _adapter.connect()
    return _adapter


def _resolve_db_path(raw_path: str) -> str:
    """Resolve a DB_PATH value to an absolute path."""
    agent_dir = Path(os.path.dirname(os.path.abspath(__file__))).parent
    project_root = agent_dir.parent

    if raw_path and os.path.isabs(raw_path):
        return raw_path
    elif raw_path:
        return str(project_root / raw_path)
    else:
        return str(project_root / "prereq" / "DemoECommerceDB.db")


def _create_sqlite_adapter(provider: Any) -> DatabaseAdapter:
    """Build a SqliteAdapter from config values."""
    from .sqlite_adapter import SqliteAdapter

    db_path = _resolve_db_path(provider.get("DB_PATH", ""))
    return SqliteAdapter(config={"db_path": db_path})


def _create_postgres_adapter(provider: Any) -> DatabaseAdapter:
    """Build a PostgresAdapter from config values."""
    from .postgres_adapter import PostgresAdapter

    return PostgresAdapter(config={
        "host": provider.get("DB_HOST", "localhost"),
        "port": int(provider.get("DB_PORT", 5432)),
        "database": provider.get("DB_NAME", ""),
        "user": provider.get("DB_USER", ""),
        "password": provider.get("DB_PASSWORD", ""),
        "schema": provider.get("DB_SCHEMA", "public"),
    })


def _create_mysql_adapter(provider: Any) -> DatabaseAdapter:
    """Build a MysqlAdapter from config values."""
    from .mysql_adapter import MysqlAdapter

    return MysqlAdapter(config={
        "host": provider.get("DB_HOST", "localhost"),
        "port": int(provider.get("DB_PORT", 3306)),
        "database": provider.get("DB_NAME", ""),
        "user": provider.get("DB_USER", ""),
        "password": provider.get("DB_PASSWORD", ""),
    })


def reset_adapter() -> None:
    """Close and reset the cached adapter. Useful for testing or config reload."""
    global _adapter
    if _adapter is not None:
        _adapter.close()
        _adapter = None
