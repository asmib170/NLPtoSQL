"""Database adapters package.

Provides a unified interface (DatabaseAdapter ABC) for all SQL backends.
Use get_db_adapter() to obtain the active adapter based on config.

Implementations:
  - SqliteAdapter: local SQLite file-based database
  - PostgresAdapter: PostgreSQL / RDS / Aurora
  - MysqlAdapter: MySQL / RDS / Aurora
"""

from .base import DatabaseAdapter
from .factory import get_db_adapter

__all__ = [
    "DatabaseAdapter",
    "get_db_adapter",
]
