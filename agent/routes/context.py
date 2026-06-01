"""Context endpoint — LLM-generated sample questions and description."""

import os

from fastapi import APIRouter

from tools.db_inspector import get_table_names, get_schema_as_text, DEFAULT_DB_PATH
from utils import converse_json

router = APIRouter(prefix="/api")


def _generate_ui_context() -> dict:
    """Generate UI-facing content (description + 6 sample questions) from the DB schema.

    Uses direct boto3 Converse API — no Agent overhead.

    Returns:
        Dict with keys: db_name, description, tables, sample_questions.
    """
    tables = get_table_names()
    db_name = os.path.basename(DEFAULT_DB_PATH).replace(".db", "")
    schema = get_schema_as_text()

    system_prompt = "You are a helpful assistant. Respond only with valid JSON, no markdown."

    prompt = f"""Given the following SQLite database schema, generate exactly 6 sample questions 
that a business user might ask about this data. Also generate a one-line description of what 
this database contains.

Schema:
{schema}

Respond ONLY with valid JSON in this exact format:
{{
  "description": "<one line describing what this database is about>",
  "questions": [
    "<question 1>",
    "<question 2>",
    "<question 3>",
    "<question 4>",
    "<question 5>",
    "<question 6>"
  ]
}}

Rules for the questions:
- Make them diverse: mix aggregations, filters, joins, trends, and comparisons
- Use natural business language, not SQL jargon
- Make them interesting and insightful, not trivial
- They should span different tables in the schema
"""

    result = converse_json(prompt, system_prompt, max_tokens=1024)
    if result:
        description = result.get("description", f"Query the {db_name} database and explore your data.")
        questions = result.get("questions", [])[:6]
    else:
        description = f"Query the {db_name} database ({len(tables)} tables) and explore your data."
        questions = [
            "How many records are in each table?",
            f"What are the most recent entries in {tables[0] if tables else 'the database'}?",
            f"Show me a summary of {tables[1] if len(tables) > 1 else tables[0]}",
            f"What are the top values in {tables[0]}?",
            f"How are {tables[0]} and {tables[1] if len(tables) > 1 else tables[0]} related?",
            "Show me trends over time",
        ]

    return {
        "db_name": db_name,
        "description": description,
        "tables": tables,
        "sample_questions": questions,
    }


@router.get("/context")
def context() -> dict:
    """Return UI context: description and sample questions (LLM-generated).

    Uses def (not async def) so FastAPI runs it in a threadpool.
    """
    return _generate_ui_context()
