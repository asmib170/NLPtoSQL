"""PostgreSQL implementation of the DatabaseAdapter interface.

Uses psycopg2 for connectivity. Supports standard PostgreSQL and
AWS RDS PostgreSQL (same wire protocol).

Config keys:
    host     - hostname or IP (default: "localhost")
    port     - port number (default: 5432)
    database - database name (required)
    user     - username (required)
    password - password (required)
    schema   - schema to introspect (default: "public")
"""

from typing import Any

from .base import DatabaseAdapter


class PostgresAdapter(DatabaseAdapter):
    """PostgreSQL database adapter.

    Config keys:
        host, port, database, user, password, schema (optional, default "public").
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._host: str = config.get("host", "localhost")
        self._port: int = int(config.get("port", 5432))
        self._database: str = config["database"]
        self._user: str = config["user"]
        self._password: str = config["password"]
        self._schema: str = config.get("schema", "public")
        self._conn = None
        self._dict_cursor_factory = None  # Set during connect()

    # -------------------------------------------------------------- #
    # Connection lifecycle
    # -------------------------------------------------------------- #

    def connect(self) -> None:
        """Open a connection to PostgreSQL."""
        try:
            import psycopg2  # noqa: E401
            import psycopg2.extras  # noqa: E401
        except ImportError as e:
            raise ImportError(
                "psycopg2 is required for PostgreSQL support. "
                "Install it with: uv add psycopg2-binary"
            ) from e

        self._dict_cursor_factory = psycopg2.extras.RealDictCursor

        self._conn = psycopg2.connect(
            host=self._host,
            port=self._port,
            dbname=self._database,
            user=self._user,
            password=self._password,
        )
        # Use autocommit for read-only queries
        self._conn.set_session(readonly=True, autocommit=True)

    def close(self) -> None:
        """Close the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_conn(self):
        """Return active connection, opening one if needed."""
        if self._conn is None or self._conn.closed:
            self.connect()
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
        with conn.cursor(cursor_factory=self._dict_cursor_factory) as cur:
            try:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [dict(row) for row in cur.fetchall()]
                return columns, rows
            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"SQL error: {e}") from e

    def execute_query_with_count(
        self, sql: str, limit: int, params: tuple = ()
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Execute query returning total count + limited rows."""
        sql = sql.strip()
        if not sql.upper().startswith("SELECT"):
            raise PermissionError("Only SELECT statements are permitted.")

        conn = self._get_conn()
        with conn.cursor(cursor_factory=self._dict_cursor_factory) as cur:
            try:
                # Get total count
                count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql}) AS _count_subq"
                try:
                    cur.execute(count_sql, params)
                    total_count = cur.fetchone()["cnt"]
                except Exception:
                    conn.rollback()
                    total_count = -1

                # Fetch limited rows
                if "LIMIT" in sql.upper():
                    limited_sql = sql
                else:
                    limited_sql = f"{sql} LIMIT {limit}"

                cur.execute(limited_sql, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [dict(row) for row in cur.fetchall()]

                if total_count < 0:
                    total_count = len(rows)

                return total_count, columns, rows
            except Exception as e:
                conn.rollback()
                raise RuntimeError(f"SQL error: {e}") from e

    # -------------------------------------------------------------- #
    # Schema introspection
    # -------------------------------------------------------------- #

    def get_table_names(self) -> list[str]:
        """Return all user-defined table names in the configured schema."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (self._schema,))
            return [row[0] for row in cur.fetchall()]

    def get_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Return column metadata from information_schema."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            # Get primary key columns
            cur.execute("""
                SELECT kcu.column_name
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                WHERE tc.constraint_type = 'PRIMARY KEY'
                  AND tc.table_schema = %s
                  AND tc.table_name = %s
            """, (self._schema, table_name))
            pk_columns = {row[0] for row in cur.fetchall()}

            # Get all columns
            cur.execute("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (self._schema, table_name))

            columns = []
            for row in cur.fetchall():
                columns.append({
                    "name": row[0],
                    "type": row[1].upper(),
                    "nullable": row[2] == "YES",
                    "default": row[3],
                    "is_pk": row[0] in pk_columns,
                })
            return columns

    def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Return FK relationships from information_schema."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    kcu.column_name AS from_column,
                    ccu.table_name AS to_table,
                    ccu.column_name AS to_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_name = kcu.constraint_name
                  AND tc.table_schema = kcu.table_schema
                JOIN information_schema.constraint_column_usage ccu
                  ON ccu.constraint_name = tc.constraint_name
                  AND ccu.table_schema = tc.table_schema
                WHERE tc.constraint_type = 'FOREIGN KEY'
                  AND tc.table_schema = %s
                  AND tc.table_name = %s
            """, (self._schema, table_name))
            return [
                {"from_column": row[0], "to_table": row[1], "to_column": row[2]}
                for row in cur.fetchall()
            ]

    def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Return index metadata from pg_indexes."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE schemaname = %s AND tablename = %s
                ORDER BY indexname
            """, (self._schema, table_name))

            indexes = []
            for row in cur.fetchall():
                idx_name = row[0]
                idx_def = row[1]
                is_unique = "UNIQUE" in idx_def.upper()
                # Extract column names from the index definition
                # Format: CREATE [UNIQUE] INDEX name ON table USING method (col1, col2)
                cols_part = idx_def.split("(", 1)[-1].rstrip(")")
                columns = [c.strip().strip('"') for c in cols_part.split(",")]
                indexes.append({
                    "name": idx_name,
                    "unique": is_unique,
                    "columns": columns,
                })
            return indexes

    def get_create_statement(self, table_name: str) -> str:
        """Generate a CREATE TABLE statement from information_schema metadata."""
        columns = self.get_columns(table_name)
        fks = self.get_foreign_keys(table_name)

        lines = []
        pk_cols = [c["name"] for c in columns if c["is_pk"]]

        for col in columns:
            parts = [f"  {col['name']} {col['type']}"]
            if not col["nullable"]:
                parts.append("NOT NULL")
            if col["default"] is not None:
                parts.append(f"DEFAULT {col['default']}")
            lines.append(" ".join(parts))

        if pk_cols:
            lines.append(f"  PRIMARY KEY ({', '.join(pk_cols)})")

        for fk in fks:
            lines.append(
                f"  FOREIGN KEY ({fk['from_column']}) "
                f"REFERENCES {fk['to_table']}({fk['to_column']})"
            )

        body = ",\n".join(lines)
        return f"CREATE TABLE {table_name} (\n{body}\n);"

    # -------------------------------------------------------------- #
    # Dialect info
    # -------------------------------------------------------------- #

    def get_sql_dialect(self) -> str:
        return "postgresql"

    def get_database_name(self) -> str:
        return self._database
