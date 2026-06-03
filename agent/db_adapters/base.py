"""DatabaseAdapter — abstract base class for all SQL database backends.

Each backend (SQLite, Postgres, MySQL, etc.) implements this interface.
The rest of the codebase interacts with the database exclusively through
these methods, making the DB engine swappable via config.
"""

from abc import ABC, abstractmethod
from typing import Any


class DatabaseAdapter(ABC):
    """Unified interface for SQL database backends.

    All adapters receive their configuration as a plain dict in the
    constructor. Each implementation extracts the keys it needs.

    Args:
        config: Dict of connection parameters. Keys vary by backend:
            - sqlite: {"db_path": "..."}
            - postgresql: {"host": "...", "port": 5432, "database": "...", "user": "...", "password": "..."}
            - mysql: {"host": "...", "port": 3306, "database": "...", "user": "...", "password": "..."}
    """

    def __init__(self, config: dict[str, Any]):
        self._config = config

    # -------------------------------------------------------------- #
    # Connection lifecycle
    # -------------------------------------------------------------- #

    @abstractmethod
    def connect(self) -> None:
        """Establish a connection (or connection pool) to the database."""
        ...

    @abstractmethod
    def close(self) -> None:
        """Close the connection / release pool resources."""
        ...

    # -------------------------------------------------------------- #
    # Query execution
    # -------------------------------------------------------------- #

    @abstractmethod
    def execute_query(self, sql: str, params: tuple = ()) -> tuple[list[str], list[dict[str, Any]]]:
        """Execute a read-only SQL query and return results.

        Args:
            sql: The SQL SELECT statement to execute.
            params: Optional query parameters for parameterized queries.

        Returns:
            A tuple of (column_names, rows) where rows is a list of dicts
            with column names as keys.

        Raises:
            PermissionError: If the statement is not a SELECT.
            RuntimeError: If execution fails.
        """
        ...

    @abstractmethod
    def execute_query_with_count(
        self, sql: str, limit: int, params: tuple = ()
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Execute a query, returning total count + limited rows.

        Args:
            sql: The SQL SELECT statement.
            limit: Maximum number of rows to return.
            params: Optional query parameters.

        Returns:
            A tuple of (total_row_count, column_names, rows).

        Raises:
            PermissionError: If the statement is not a SELECT.
            RuntimeError: If execution fails.
        """
        ...

    # -------------------------------------------------------------- #
    # Schema introspection
    # -------------------------------------------------------------- #

    @abstractmethod
    def get_table_names(self) -> list[str]:
        """Return all user-defined table names (excludes system tables)."""
        ...

    @abstractmethod
    def get_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Return column metadata for a table.

        Each dict should contain at minimum:
            name       - column name
            type       - declared data type
            nullable   - True if NULLs are allowed
            default    - default value or None
            is_pk      - True if part of primary key
        """
        ...

    @abstractmethod
    def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Return foreign key relationships for a table.

        Each dict should contain:
            from_column  - column in this table
            to_table     - referenced table
            to_column    - referenced column
        """
        ...

    @abstractmethod
    def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Return index metadata for a table.

        Each dict should contain:
            name   - index name
            unique - True if unique
            columns - list of column names in the index
        """
        ...

    @abstractmethod
    def get_create_statement(self, table_name: str) -> str:
        """Return the CREATE TABLE statement (or equivalent DDL) for a table."""
        ...

    # -------------------------------------------------------------- #
    # Dialect info
    # -------------------------------------------------------------- #

    @abstractmethod
    def get_sql_dialect(self) -> str:
        """Return the SQL dialect name (e.g. 'sqlite', 'postgresql', 'mysql').

        Used in prompt generation to tell the LLM which SQL variant to produce.
        """
        ...

    @abstractmethod
    def get_database_name(self) -> str:
        """Return a human-friendly database name for display purposes."""
        ...

    # -------------------------------------------------------------- #
    # Convenience helpers (implemented in terms of the above)
    # -------------------------------------------------------------- #

    def get_column_names(self, table_name: str) -> list[str]:
        """Return just the column names for a table."""
        return [col["name"] for col in self.get_columns(table_name)]

    def get_full_schema(self) -> dict[str, Any]:
        """Return a complete schema snapshot as a nested dict.

        Structure:
        {
            "tables": {
                "<table_name>": {
                    "columns": [...],
                    "foreign_keys": [...],
                    "indexes": [...],
                    "create_statement": "..."
                }
            }
        }
        """
        tables = self.get_table_names()
        schema: dict[str, Any] = {"tables": {}}
        for table in tables:
            schema["tables"][table] = {
                "columns": self.get_columns(table),
                "foreign_keys": self.get_foreign_keys(table),
                "indexes": self.get_indexes(table),
                "create_statement": self.get_create_statement(table),
            }
        return schema

    def get_schema_as_text(self) -> str:
        """Return a compact, human-readable text representation of the schema.

        Useful for injecting into LLM prompts.

        Format per table:
            TABLE <name>
              <col_name> <type> [PK] [NOT NULL] [DEFAULT <val>]
              ...
              FK: <from_col> -> <parent_table>(<to_col>)
        """
        schema = self.get_full_schema()
        lines = []
        for table_name, info in schema["tables"].items():
            lines.append(f"TABLE {table_name}")
            for col in info["columns"]:
                parts = [f"  {col['name']}", col.get("type") or ""]
                if col.get("is_pk"):
                    parts.append("PK")
                if not col.get("nullable", True):
                    parts.append("NOT NULL")
                if col.get("default") is not None:
                    parts.append(f"DEFAULT {col['default']}")
                lines.append(" ".join(p for p in parts if p))
            for fk in info["foreign_keys"]:
                lines.append(f"  FK: {fk['from_column']} -> {fk['to_table']}({fk['to_column']})")
            lines.append("")  # blank line between tables
        return "\n".join(lines)

    def get_schema_as_json(self) -> str:
        """Return the full schema serialized as a JSON string."""
        import json
        return json.dumps(self.get_full_schema(), indent=2)

    def get_sample_rows(self, table_name: str, n: int = 3) -> list[dict[str, Any]]:
        """Return up to n sample rows from a table."""
        sql = f"SELECT * FROM {table_name} LIMIT {n}"
        _, rows = self.execute_query(sql)
        return rows
