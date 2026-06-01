"""SQL Tools for the NLP-to-SQL agent.

Provides four Strands @tool functions:
  1. verify_question   — checks if the DB schema can answer the user's question
  2. generate_sql      — converts a natural-language question to a SQL statement
  3. execute_sql       — executes a SQL statement and returns the results
  4. summarize_results — analyses the results and surfaces highlights and trends
"""

import json
import sqlite3
import os

from strands import tool

from .db_inspector import (
    DEFAULT_DB_PATH as DB_PATH,
    get_schema_as_text,
    get_table_names,
)

from utils import MAX_DISPLAY_ROWS


# ------------------------------------------------------------------ #
# Tool 1: verify_question
# ------------------------------------------------------------------ #
@tool
def verify_question(question: str) -> str:
    """
    Verify whether the SQLite database schema contains enough information
    to answer the user's natural language question.

    The tool inspects the database schema (table names, columns, relationships)
    and returns a JSON object with:
      - "answerable": true/false
      - "reason": explanation of why the question can or cannot be answered
      - "relevant_tables": list of tables that are relevant to the question

    Args:
        question (str): The user's question in natural language.

    Returns:
        str: JSON string with keys "answerable", "reason", and "relevant_tables".
    """
    question_lower = question.lower()

    # Build keyword->table map dynamically from actual table names
    tables = get_table_names()
    keyword_table_map: dict[str, str] = {}
    for table in tables:
        # map the table name itself and common synonyms
        keyword_table_map[table.rstrip("s")] = table   # e.g. "order" -> "orders"
        keyword_table_map[table] = table                # exact match

    # Extra domain synonyms
    extra_synonyms = {
        "customer": "users",
        "purchase": "orders",
        "buy": "orders",
        "bought": "orders",
        "item": "order_items",
        "line": "order_items",
        "ship": "shipping",
        "deliver": "shipping",
        "track": "shipping",
        "rating": "reviews",
        "categor": "categories",
        "discount": "coupons",
        "promo": "coupons",
    }
    keyword_table_map.update(extra_synonyms)

    relevant_tables = []
    for keyword, table in keyword_table_map.items():
        if keyword in question_lower and table not in relevant_tables:
            relevant_tables.append(table)

    # If no specific tables matched, check if the question is generic
    if not relevant_tables:
        generic_keywords = ["total", "count", "how many", "list", "show", "find",
                            "top", "best", "most", "average", "revenue", "sales"]
        if any(kw in question_lower for kw in generic_keywords):
            relevant_tables = ["orders", "order_items", "products", "users"]

    answerable = len(relevant_tables) > 0

    result = {
        "answerable": answerable,
        "reason": (
            f"The database contains the following relevant tables: {', '.join(relevant_tables)}. "
            "The schema has sufficient data to answer this question."
            if answerable else
            "No relevant tables were found in the schema for this question. "
            "The database may not contain the required data."
        ),
        "relevant_tables": relevant_tables,
        "schema_summary": f"Tables available: {', '.join(get_table_names())}",
    }
    return json.dumps(result, indent=2)


# ------------------------------------------------------------------ #
# Tool 2: generate_sql
# ------------------------------------------------------------------ #
@tool
def generate_sql(question: str, relevant_tables: str = "") -> str:
    """
    Convert a natural language question into a valid SQLite SQL SELECT statement
    based on the DemoECommerceDB schema.

    The tool returns a JSON object with:
      - "sql": the generated SQL statement (or empty string if not possible)
      - "explanation": plain-English explanation of what the SQL does
      - "error": error message if SQL could not be generated

    Args:
        question (str): The user's question in natural language.
        relevant_tables (str): Optional comma-separated list of relevant table names
                               (from verify_question output) to focus the generation.

    Returns:
        str: JSON string with keys "sql", "explanation", and optionally "error".
    """
    schema = get_schema_as_text()

    # Build a prompt that the agent (LLM) will use to generate SQL.
    # The tool itself returns the schema + question so the agent can
    # produce the SQL in its reasoning step.
    prompt_context = {
        "instruction": (
            "Generate a valid SQLite SELECT statement that answers the question below. "
            "Use only the tables and columns defined in the schema. "
            "Always use table aliases. Limit results to 100 rows unless the question asks for all. "
            "Return ONLY the SQL — no markdown, no explanation in the sql field."
        ),
        "question": question,
        "relevant_tables": relevant_tables,
        "schema": schema,
        "output_format": {
            "sql": "<the SQL SELECT statement>",
            "explanation": "<plain English explanation of what the query does>",
        },
    }

    return json.dumps(prompt_context, indent=2)


# ------------------------------------------------------------------ #
# Tool 3: execute_sql
# ------------------------------------------------------------------ #
@tool
def execute_sql(sql: str) -> str:
    """
    Execute a SQL SELECT statement against the DemoECommerceDB SQLite database
    and return the results as a JSON string.

    Only SELECT statements are permitted for safety.
    Returns at most MAX_DISPLAY_ROWS rows along with the total row count.

    Args:
        sql (str): A valid SQLite SELECT statement to execute.

    Returns:
        str: JSON string with keys "total_row_count", "displayed_rows", "columns", and "rows".
             Returns an error message string if execution fails.
    """
    sql = sql.strip()

    # Safety: only allow SELECT statements
    if not sql.upper().startswith("SELECT"):
        return json.dumps({"error": "Only SELECT statements are permitted."})

    if not os.path.exists(DB_PATH):
        return json.dumps({"error": f"Database not found at: {DB_PATH}"})

    try:
        # Open in read-only mode for safety
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()

        # Get total count without loading all rows
        count_sql = f"SELECT COUNT(*) FROM ({sql})"
        try:
            cur.execute(count_sql)
            total_count = cur.fetchone()[0]
        except sqlite3.Error:
            total_count = -1  # Count failed, still return data

        # Fetch only the display rows
        limited_sql = f"{sql} LIMIT {MAX_DISPLAY_ROWS}"
        # Only add LIMIT if not already present
        if "LIMIT" in sql.upper():
            limited_sql = sql
        cur.execute(limited_sql)
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description] if cur.description else []
        conn.close()

        results = [dict(zip(columns, row)) for row in rows]
        if total_count < 0:
            total_count = len(results)

        output = {
            "total_row_count": total_count,
            "displayed_rows": len(results),
            "columns": columns,
            "rows": results,
        }
        return json.dumps(output, indent=2, default=str)

    except sqlite3.Error as e:
        return json.dumps({"error": f"SQL error: {str(e)}"})


# ------------------------------------------------------------------ #
# Tool 4: summarize_results
# ------------------------------------------------------------------ #
@tool
def summarize_results(question: str, sql: str, results_json: str) -> str:
    """
    Analyse the results of a SQL query and produce a plain-English summary
    that highlights key findings, interesting trends, outliers, and patterns.

    The tool receives the original question, the SQL that was run, and the
    raw query results, then returns a structured analysis containing:
      - "headline"    : one-sentence answer to the question
      - "highlights"  : top 3-5 most important findings as bullet points
      - "trends"      : any patterns, growth/decline, or correlations noticed
      - "outliers"    : unusual values or anomalies worth calling out
      - "suggestions" : follow-up questions the user might want to ask next

    Args:
        question (str): The original natural language question the user asked.
        sql (str): The SQL statement that was executed to get the results.
        results_json (str): The JSON string returned by execute_sql, containing
                            "total_row_count", "displayed_rows", "columns", and "rows".

    Returns:
        str: JSON string with keys "headline", "highlights", "trends",
             "outliers", and "suggestions".
    """
    # Parse the results so we can do basic statistical analysis
    try:
        data = json.loads(results_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Could not parse results JSON."})

    rows = data.get("rows", [])
    columns = data.get("columns", [])
    row_count = data.get("row_count", 0)

    if row_count == 0:
        return json.dumps({
            "headline": "No data was returned for this query.",
            "highlights": ["The query returned 0 rows."],
            "trends": [],
            "outliers": [],
            "suggestions": [
                "Try broadening the filter criteria.",
                "Check if the relevant tables have been populated.",
            ],
        })

    # ---- Basic numeric analysis ----------------------------------------
    numeric_stats: dict[str, dict] = {}
    for col in columns:
        values = []
        for row in rows:
            val = row.get(col)
            if val is not None:
                try:
                    values.append(float(val))
                except (ValueError, TypeError):
                    pass
        if values:
            numeric_stats[col] = {
                "min":  round(min(values), 2),
                "max":  round(max(values), 2),
                "avg":  round(sum(values) / len(values), 2),
                "sum":  round(sum(values), 2),
                "count": len(values),
            }

    # ---- Categorical frequency analysis -----------------------------------
    categorical_stats: dict[str, dict] = {}
    for col in columns:
        if col in numeric_stats:
            continue
        freq: dict[str, int] = {}
        for row in rows:
            val = str(row.get(col, ""))
            freq[val] = freq.get(val, 0) + 1
        if freq:
            top = sorted(freq.items(), key=lambda x: x[1], reverse=True)[:5]
            categorical_stats[col] = {
                "unique_values": len(freq),
                "top_values": [{"value": v, "count": c} for v, c in top],
            }

    # ---- Build the analysis payload for the LLM to reason over -----------
    analysis_context = {
        "instruction": (
            "You are a data analyst. Based on the query results below, produce a "
            "concise but insightful analysis. Fill in each field of the output_format. "
            "Be specific — use actual numbers and values from the data. "
            "Keep highlights as short bullet points. "
            "Suggest 2-3 smart follow-up questions."
        ),
        "original_question": question,
        "sql_executed": sql,
        "result_summary": {
            "total_rows_returned": row_count,
            "columns": columns,
            "numeric_statistics": numeric_stats,
            "categorical_statistics": categorical_stats,
            "sample_rows": rows[:5],  # first 5 rows as examples
        },
        "output_format": {
            "headline": "<one sentence direct answer to the question>",
            "highlights": [
                "<key finding 1>",
                "<key finding 2>",
                "<key finding 3>",
            ],
            "trends": "<patterns, growth/decline, correlations noticed in the data>",
            "outliers": "<unusual values, anomalies, or surprising results>",
            "suggestions": [
                "<follow-up question 1>",
                "<follow-up question 2>",
            ],
        },
    }

    return json.dumps(analysis_context, indent=2, default=str)


