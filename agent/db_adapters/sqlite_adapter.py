"""SQLite implementation of the DatabaseAdapter interface.

Connects to a local .db file in read-only mode. Lightweight — opens
and closes connections per operation (SQLite handles this efficiently).
"""

import os
import sqlite3
from typing import Any

from .base import DatabaseAdapter


class SqliteAdapter(DatabaseAdapter):
    """SQLite database adapter.

    Config keys:
        db_path: Absolute path to the .db file.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._db_path: str = config["db_path"]
        self._conn: sqlite3.Connection | None = None

    # -------------------------------------------------------------- #
    # Connection lifecycle
    # -------------------------------------------------------------- #

    def connect(self) -> None:
        """Open a read-only connection to the SQLite database."""
        if not os.path.exists(self._db_path):
            raise FileNotFoundError(f"SQLite database not found: {self._db_path}")
        self._conn = sqlite3.connect(
            f"file:{self._db_path}?mode=ro",
            uri=True,
            check_same_thread=False,
        )
        self._conn.row_factory = sqlite3.Row

    def close(self) -> None:
        """Close the active connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_conn(self) -> sqlite3.Connection:
        """Return active connection, opening one if needed."""
        if self._conn is None:
            self.connect()
        assert self._conn is not None
        return self._conn

    # -------------------------------------------------------------- #
    # Query execution
    # -------------------------------------------------------------- #

    def execute_query(self, sql: str, params: tuple = ()) -> tuple[list[str], list[dict[str, Any]]]:
        """Execute a read-only query and return (columns, rows)."""
        sql = sql.strip()
        if not sql.upper().startswith("SELECT"):
            raise PermissionError("Only SELECT statements are permitted.")

        conn = self._get_conn()
        cur = conn.cursor()
        try:
            cur.execute(sql, params)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]
            return columns, rows
        except sqlite3.Error as e:
            raise RuntimeError(f"SQL error: {e}") from e

    def execute_query_with_count(
        self, sql: str, limit: int, params: tuple = ()
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Execute query returning total count + limited rows."""
        sql = sql.strip()
        if not sql.upper().startswith("SELECT"):
            raise PermissionError("Only SELECT statements are permitted.")

        conn = self._get_conn()
        cur = conn.cursor()
        try:
            # Get total count
            count_sql = f"SELECT COUNT(*) FROM ({sql})"
            try:
                cur.execute(count_sql, params)
                total_count = cur.fetchone()[0]
            except sqlite3.Error:
                total_count = -1

            # Fetch limited rows
            if "LIMIT" in sql.upper():
                limited_sql = sql
            else:
                limited_sql = f"{sql} LIMIT {limit}"

            cur.execute(limited_sql, params)
            columns = [desc[0] for desc in cur.description] if cur.description else []
            rows = [dict(zip(columns, row)) for row in cur.fetchall()]

            if total_count < 0:
                total_count = len(rows)

            return total_count, columns, rows
        except sqlite3.Error as e:
            raise RuntimeError(f"SQL error: {e}") from e

    # -------------------------------------------------------------- #
    # Schema introspection
    # -------------------------------------------------------------- #

    def get_table_names(self) -> list[str]:
        """Return all user-defined table names."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT name FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """)
        return [row["name"] for row in cur.fetchall()]

    def get_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Return column metadata using PRAGMA table_info."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"PRAGMA table_info('{table_name}')")
        columns = []
        for row in cur.fetchall():
            columns.append({
                "name": row["name"],
                "type": row["type"] or "",
                "nullable": not bool(row["notnull"]),
                "default": row["dflt_value"],
                "is_pk": bool(row["pk"]),
            })
        return columns

    def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Return FK relationships using PRAGMA foreign_key_list."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"PRAGMA foreign_key_list('{table_name}')")
        fks = []
        for row in cur.fetchall():
            fks.append({
                "from_column": row["from"],
                "to_table": row["table"],
                "to_column": row["to"],
            })
        return fks

    def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Return index metadata using PRAGMA index_list + index_info."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(f"PRAGMA index_list('{table_name}')")
        indexes = []
        for idx_row in cur.fetchall():
            idx_name = idx_row["name"]
            # Get columns in this index
            cur2 = conn.cursor()
            cur2.execute(f"PRAGMA index_info('{idx_name}')")
            idx_columns = [col_row["name"] for col_row in cur2.fetchall()]
            indexes.append({
                "name": idx_name,
                "unique": bool(idx_row["unique"]),
                "columns": idx_columns,
            })
        return indexes

    def get_create_statement(self, table_name: str) -> str:
        """Return the original CREATE TABLE DDL."""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT sql FROM sqlite_master
            WHERE type = 'table' AND name = ?
        """, (table_name,))
        row = cur.fetchone()
        if row is None:
            raise ValueError(f"Table '{table_name}' not found in database.")
        return row["sql"]

    # -------------------------------------------------------------- #
    # Dialect info
    # -------------------------------------------------------------- #

    def get_sql_dialect(self) -> str:
        return "sqlite"

    def get_database_name(self) -> str:
        """Return the database filename without extension."""
        return os.path.basename(self._db_path).replace(".db", "")
