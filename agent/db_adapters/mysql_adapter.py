"""MySQL implementation of the DatabaseAdapter interface.

Uses pymysql for connectivity. Supports standard MySQL and
AWS RDS MySQL / Aurora MySQL (same wire protocol).

Config keys:
    host     - hostname or IP (default: "localhost")
    port     - port number (default: 3306)
    database - database name (required)
    user     - username (required)
    password - password (required)
"""

from typing import Any

from .base import DatabaseAdapter


class MysqlAdapter(DatabaseAdapter):
    """MySQL database adapter.

    Config keys:
        host, port, database, user, password.
    """

    def __init__(self, config: dict[str, Any]):
        super().__init__(config)
        self._host: str = config.get("host", "localhost")
        self._port: int = int(config.get("port", 3306))
        self._database: str = config["database"]
        self._user: str = config["user"]
        self._password: str = config["password"]
        self._conn = None

    # -------------------------------------------------------------- #
    # Connection lifecycle
    # -------------------------------------------------------------- #

    def connect(self) -> None:
        """Open a connection to MySQL."""
        try:
            import pymysql
        except ImportError as e:
            raise ImportError(
                "pymysql is required for MySQL support. "
                "Install it with: uv add pymysql"
            ) from e

        self._conn = pymysql.connect(
            host=self._host,
            port=self._port,
            database=self._database,
            user=self._user,
            password=self._password,
            cursorclass=pymysql.cursors.DictCursor,
            autocommit=True,
        )

    def close(self) -> None:
        """Close the connection."""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _get_conn(self):
        """Return active connection, reconnecting if needed."""
        if self._conn is None:
            self.connect()
        else:
            # pymysql connections can go stale; ping to verify
            self._conn.ping(reconnect=True)
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
        with conn.cursor() as cur:
            try:
                cur.execute(sql, params)
                columns = [desc[0] for desc in cur.description] if cur.description else []
                rows = [dict(row) for row in cur.fetchall()]
                return columns, rows
            except Exception as e:
                raise RuntimeError(f"SQL error: {e}") from e

    def execute_query_with_count(
        self, sql: str, limit: int, params: tuple = ()
    ) -> tuple[int, list[str], list[dict[str, Any]]]:
        """Execute query returning total count + limited rows."""
        sql = sql.strip()
        if not sql.upper().startswith("SELECT"):
            raise PermissionError("Only SELECT statements are permitted.")

        conn = self._get_conn()
        with conn.cursor() as cur:
            try:
                # Get total count
                count_sql = f"SELECT COUNT(*) AS cnt FROM ({sql}) AS _count_subq"
                try:
                    cur.execute(count_sql, params)
                    total_count = cur.fetchone()["cnt"]
                except Exception:
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
                raise RuntimeError(f"SQL error: {e}") from e

    # -------------------------------------------------------------- #
    # Schema introspection
    # -------------------------------------------------------------- #

    def get_table_names(self) -> list[str]:
        """Return all user-defined table names in the database."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                  AND table_type = 'BASE TABLE'
                ORDER BY table_name
            """, (self._database,))
            return [row["TABLE_NAME"] for row in cur.fetchall()]

    def get_columns(self, table_name: str) -> list[dict[str, Any]]:
        """Return column metadata from information_schema."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT column_name, column_type, is_nullable,
                       column_default, column_key
                FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                ORDER BY ordinal_position
            """, (self._database, table_name))

            columns = []
            for row in cur.fetchall():
                columns.append({
                    "name": row["COLUMN_NAME"],
                    "type": row["COLUMN_TYPE"].upper(),
                    "nullable": row["IS_NULLABLE"] == "YES",
                    "default": row["COLUMN_DEFAULT"],
                    "is_pk": row["COLUMN_KEY"] == "PRI",
                })
            return columns

    def get_foreign_keys(self, table_name: str) -> list[dict[str, Any]]:
        """Return FK relationships from information_schema."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    kcu.column_name AS from_column,
                    kcu.referenced_table_name AS to_table,
                    kcu.referenced_column_name AS to_column
                FROM information_schema.key_column_usage kcu
                WHERE kcu.table_schema = %s
                  AND kcu.table_name = %s
                  AND kcu.referenced_table_name IS NOT NULL
            """, (self._database, table_name))
            return [
                {
                    "from_column": row["from_column"],
                    "to_table": row["to_table"],
                    "to_column": row["to_column"],
                }
                for row in cur.fetchall()
            ]

    def get_indexes(self, table_name: str) -> list[dict[str, Any]]:
        """Return index metadata using SHOW INDEX."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute("SHOW INDEX FROM `%s`" % table_name)
            # Group columns by index name
            index_map: dict[str, dict[str, Any]] = {}
            for row in cur.fetchall():
                idx_name = row["Key_name"]
                if idx_name not in index_map:
                    index_map[idx_name] = {
                        "name": idx_name,
                        "unique": not row["Non_unique"],
                        "columns": [],
                    }
                index_map[idx_name]["columns"].append(row["Column_name"])
            return list(index_map.values())

    def get_create_statement(self, table_name: str) -> str:
        """Return the CREATE TABLE statement using SHOW CREATE TABLE."""
        conn = self._get_conn()
        with conn.cursor() as cur:
            cur.execute(f"SHOW CREATE TABLE `{table_name}`")
            row = cur.fetchone()
            # SHOW CREATE TABLE returns {"Table": ..., "Create Table": ...}
            return row.get("Create Table", row.get("Create View", ""))

    # -------------------------------------------------------------- #
    # Dialect info
    # -------------------------------------------------------------- #

    def get_sql_dialect(self) -> str:
        return "mysql"

    def get_database_name(self) -> str:
        return self._database
