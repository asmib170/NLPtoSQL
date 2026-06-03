"""DB Inspector — dynamically reads schema from sqlite_master.

Provides helper functions that sql_tools.py (and any other module) can use
to understand the database structure without hardcoding table or column names.
"""

import sqlite3
import json
from typing import Any

# Default DB path — loaded from central config
from utils import DB_PATH as DEFAULT_DB_PATH


def _get_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    """Return a read-only sqlite3 connection with row_factory set.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        A sqlite3.Connection in read-only mode with sqlite3.Row row_factory.
    """
    conn = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    conn.row_factory = sqlite3.Row
    return conn


# ------------------------------------------------------------------ #
# Table-level helpers
# ------------------------------------------------------------------ #

def get_table_names(db_path: str = DEFAULT_DB_PATH) -> list[str]:
    """Return all user-defined table names (excludes sqlite_ internals)."""
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT name FROM sqlite_master
        WHERE type = 'table'
          AND name NOT LIKE 'sqlite_%'
        ORDER BY name
    """)
    names = [row["name"] for row in cur.fetchall()]
    conn.close()
    return names


def get_create_statement(table_name: str, db_path: str = DEFAULT_DB_PATH) -> str:
    """Return the original CREATE TABLE statement for a given table."""
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute("""
        SELECT sql FROM sqlite_master
        WHERE type = 'table' AND name = ?
    """, (table_name,))
    row = cur.fetchone()
    conn.close()
    if row is None:
        raise ValueError(f"Table '{table_name}' not found in database.")
    return row["sql"]


# ------------------------------------------------------------------ #
# Column-level helpers
# ------------------------------------------------------------------ #

def get_columns(table_name: str, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """
    Return column metadata for a table using PRAGMA table_info.

    Each dict contains:
        cid        - column index
        name       - column name
        type       - declared type (e.g. INTEGER, TEXT, REAL)
        notnull    - 1 if NOT NULL constraint exists
        dflt_value - default value or None
        pk         - 1 if part of primary key
    """
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA table_info('{table_name}')")
    columns = [dict(row) for row in cur.fetchall()]
    conn.close()
    return columns


def get_column_names(table_name: str, db_path: str = DEFAULT_DB_PATH) -> list[str]:
    """Return just the column names for a table."""
    return [col["name"] for col in get_columns(table_name, db_path)]


# ------------------------------------------------------------------ #
# Foreign key helpers
# ------------------------------------------------------------------ #

def get_foreign_keys(table_name: str, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """
    Return foreign key relationships for a table using PRAGMA foreign_key_list.

    Each dict contains:
        id         - FK index
        seq        - sequence within composite FK
        table      - referenced (parent) table
        from       - column in this table
        to         - column in the referenced table
        on_update  - action on update
        on_delete  - action on delete
    """
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA foreign_key_list('{table_name}')")
    fks = [dict(row) for row in cur.fetchall()]
    conn.close()
    return fks


# ------------------------------------------------------------------ #
# Index helpers
# ------------------------------------------------------------------ #

def get_indexes(table_name: str, db_path: str = DEFAULT_DB_PATH) -> list[dict]:
    """
    Return index metadata for a table using PRAGMA index_list.

    Each dict contains:
        seq    - sequence number
        name   - index name
        unique - 1 if unique index
        origin - 'c' (CREATE INDEX), 'u' (UNIQUE constraint), 'pk' (PRIMARY KEY)
    """
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute(f"PRAGMA index_list('{table_name}')")
    indexes = [dict(row) for row in cur.fetchall()]
    conn.close()
    return indexes


# ------------------------------------------------------------------ #
# Full schema snapshot
# ------------------------------------------------------------------ #

def get_full_schema(db_path: str = DEFAULT_DB_PATH) -> dict[str, Any]:
    """
    Return a complete schema snapshot as a nested dict.

    Structure:
    {
        "tables": {
            "<table_name>": {
                "columns": [ {cid, name, type, notnull, dflt_value, pk}, ... ],
                "foreign_keys": [ {id, seq, table, from, to, ...}, ... ],
                "indexes": [ {seq, name, unique, origin}, ... ],
                "create_statement": "CREATE TABLE ..."
            },
            ...
        }
    }
    """
    tables = get_table_names(db_path)
    schema: dict[str, Any] = {"tables": {}}
    for table in tables:
        schema["tables"][table] = {
            "columns": get_columns(table, db_path),
            "foreign_keys": get_foreign_keys(table, db_path),
            "indexes": get_indexes(table, db_path),
            "create_statement": get_create_statement(table, db_path),
        }
    return schema


def get_schema_as_text(db_path: str = DEFAULT_DB_PATH) -> str:
    """
    Return a compact, human-readable text representation of the full schema.
    Useful for injecting into LLM prompts.

    Format per table:
        TABLE <name>
          <col_name> <type> [PK] [NOT NULL] [DEFAULT <val>]
          ...
          FK: <from_col> -> <parent_table>(<to_col>)
    """
    schema = get_full_schema(db_path)
    lines = []
    for table_name, info in schema["tables"].items():
        lines.append(f"TABLE {table_name}")
        for col in info["columns"]:
            parts = [f"  {col['name']}", col["type"] or ""]
            if col["pk"]:
                parts.append("PK")
            if col["notnull"]:
                parts.append("NOT NULL")
            if col["dflt_value"] is not None:
                parts.append(f"DEFAULT {col['dflt_value']}")
            lines.append(" ".join(p for p in parts if p))
        for fk in info["foreign_keys"]:
            lines.append(f"  FK: {fk['from']} -> {fk['table']}({fk['to']})")
        lines.append("")  # blank line between tables
    return "\n".join(lines)


def get_schema_as_json(db_path: str = DEFAULT_DB_PATH) -> str:
    """Return the full schema snapshot serialised as a JSON string.

    Args:
        db_path: Path to the SQLite database file.

    Returns:
        Pretty-printed JSON string of the full schema dict.
    """
    return json.dumps(get_full_schema(db_path), indent=2)


# ------------------------------------------------------------------ #
# Sample data helper (useful for few-shot prompting)
# ------------------------------------------------------------------ #

def get_sample_rows(
    table_name: str,
    n: int = 3,
    db_path: str = DEFAULT_DB_PATH,
) -> list[dict]:
    """Return up to n sample rows from a table as a list of dicts.

    Args:
        table_name: Name of the table to sample from.
        n: Maximum number of rows to return (default 3).
        db_path: Path to the SQLite database file.

    Returns:
        List of dicts, one per row, with column names as keys.
    """
    conn = _get_connection(db_path)
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM '{table_name}' LIMIT ?", (n,))
    rows = [dict(row) for row in cur.fetchall()]
    conn.close()
    return rows


# ------------------------------------------------------------------ #
# Quick self-test
# ------------------------------------------------------------------ #
if __name__ == "__main__":
    print("=== Tables ===")
    for t in get_table_names():
        print(f"  {t}")

    print("\n=== Schema (text) ===")
    print(get_schema_as_text())

    print("\n=== Sample rows: orders ===")
    for row in get_sample_rows("orders", n=3):
        print(" ", row)

