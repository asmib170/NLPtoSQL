"""Context endpoint — LLM-generated sample questions and description."""

from fastapi import APIRouter

from db_adapters import get_db_adapter
from utils import converse_json, SAMPLE_QUESTIONS_COUNT, CONTEXT_GEN_MAX_TOKENS

router = APIRouter(prefix="/api")

# Cache the context result — schema doesn't change at runtime
_cached_context: dict | None = None


def _generate_ui_context() -> dict:
    """Generate UI-facing content (description + 6 sample questions) from the DB schema.

    Uses direct boto3 Converse API — no Agent overhead.

    Returns:
        Dict with keys: db_name, description, tables, sample_questions.
    """
    adapter = get_db_adapter()
    tables = adapter.get_table_names()
    db_name = adapter.get_database_name()
    schema = adapter.get_schema_as_text()

    system_prompt = "You are a helpful assistant. Respond only with valid JSON, no markdown."

    prompt = f"""Given the following database schema, generate exactly {SAMPLE_QUESTIONS_COUNT} sample questions 
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

    result = converse_json(prompt, system_prompt, max_tokens=CONTEXT_GEN_MAX_TOKENS)
    if result:
        description = result.get("description", f"Query the {db_name} database and explore your data.")
        questions = result.get("questions", [])[:SAMPLE_QUESTIONS_COUNT]
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

    Result is cached after the first call — schema doesn't change at runtime.
    Uses def (not async def) so FastAPI runs it in a threadpool.
    """
    global _cached_context
    if _cached_context is None:
        _cached_context = _generate_ui_context()
    return _cached_context
