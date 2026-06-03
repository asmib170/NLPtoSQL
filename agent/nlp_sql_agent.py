"""NLP-to-SQL Agent.

Workflow enforced via system prompt:
  1. verify_question   — confirm the DB can answer the question
  2. generate_sql      — produce a SQL SELECT statement (dialect-aware)
  3. execute_sql       — run the statement and return results
  4. summarize_results — analyse results and surface insights
  5. generate_chart    — create a matplotlib visualization of the results

Steps 4 and 5 are invoked in parallel after execute_sql succeeds.
"""

import sys
import os

# Make sure imports resolve when running from any working directory
sys.path.insert(0, os.path.dirname(__file__))

from strands import Agent
from strands.models import BedrockModel

from tools.sql_tools import verify_question, generate_sql, execute_sql, summarize_results
from tools.chart_tool import generate_chart
from db_adapters import get_db_adapter
from utils import MODEL_ID, MODEL_MAX_TOKENS, THINKING_BUDGET_TOKENS, MAX_DISPLAY_ROWS

# ------------------------------------------------------------------ #
# Model
# ------------------------------------------------------------------ #
model = BedrockModel(
    model_id=MODEL_ID,
    max_tokens=MODEL_MAX_TOKENS,
    temperature=1,  # Required to be 1 when thinking is enabled
    additional_request_fields={
        "thinking": {
            "type": "enabled",
            "budget_tokens": THINKING_BUDGET_TOKENS,
        }
    },
)

# ------------------------------------------------------------------ #
# System prompt — built dynamically from the live schema
# ------------------------------------------------------------------ #
_adapter     = get_db_adapter()
_schema_text = _adapter.get_schema_as_text()
_table_list  = ", ".join(_adapter.get_table_names())
_sql_dialect = _adapter.get_sql_dialect().upper()

SYSTEM_PROMPT = f"""You are an expert NLP-to-SQL assistant for the {_adapter.get_database_name()} {_sql_dialect} database.

## Your database
Tables available: {_table_list}

## Schema
{_schema_text}

## Workflow — follow these steps IN ORDER for every user question:

1. Call `verify_question` with the user's question.
   - If "answerable": false, politely explain the database cannot answer this.
   - If "answerable": true, continue.

2. Call `generate_sql` with the question and relevant_tables.
   Then produce a valid {_sql_dialect} SELECT statement following these rules:
   - Valid {_sql_dialect} syntax only
   - Use only tables and columns from the schema above
   - Always use table aliases (e.g. o for orders, u for users)
   - JOIN tables using their foreign key relationships
   - Add ORDER BY and LIMIT {MAX_DISPLAY_ROWS} unless the user asks for all rows
   - SELECT only — never DROP, DELETE, UPDATE, INSERT

3. Call `execute_sql` with the SQL you generated.
   - If error, fix the SQL and retry once.

4. After execute_sql succeeds, you MUST call BOTH of these tools IN THE SAME RESPONSE (parallel tool use):
   - `summarize_results` with the question, SQL, and results JSON
   - `generate_chart` with the question, SQL, and results JSON
   
   IMPORTANT: These two tools have NO dependency on each other. You MUST invoke them
   together in a single response as parallel tool calls. Do NOT call one, wait for it,
   then call the other. Emit both tool_use blocks in the same assistant message.

## CRITICAL OUTPUT RULES
- Do NOT narrate your steps. Do NOT say "Step 1", "Step 2", "Verifying", "Generating SQL", etc.
- Do NOT explain what you are about to do or what tools you are calling.
- ONLY output the final response after all tools have completed.
- Your visible output should contain ONLY the final answer — nothing about your internal process.
- If a chart was generated successfully, include it in your response as: ![Chart](/api/charts/FILENAME) where FILENAME is the filename from the generate_chart result.

## Response format
- ALL responses must be in **Markdown** format.
- Structure your response with these sections:
  - A brief title/heading for the analysis
  - The SQL query in a ```sql code block
  - Results as a **markdown table**
  - The chart image (if generated): ![Chart](/api/charts/chart_XXXXX.png)
  - Key highlights and insights (bullet points)
  - Trends or outliers worth noting
  - 2-3 suggested follow-up questions
- Use **bold** for key numbers and findings.
- If the result set has more than 50 rows, the tool returns only the top 50. Mention the total row count and note that you're showing the top 50.

## Response style
- Be specific — use actual numbers from the data, not vague statements.
- Keep it concise but insightful.
- If the result set is empty, say so clearly and suggest why.
- Never make up data — only report what the database returns.
"""

# ------------------------------------------------------------------ #
# Agent creation — only for CLI use. Server creates per-session agents.
# ------------------------------------------------------------------ #
def create_agent():
    """Create an agent instance (used by CLI mode)."""
    return Agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[
            verify_question,    # Tool 1
            generate_sql,       # Tool 2
            execute_sql,        # Tool 3
            summarize_results,  # Tool 4
            generate_chart,     # Tool 5
        ],
    )


# ------------------------------------------------------------------ #
# Interactive CLI loop
# ------------------------------------------------------------------ #
def main():
    """Run an interactive CLI loop for the NLP-to-SQL agent."""
    agent = create_agent()
    print("=" * 60)
    print("  NLP-to-SQL Agent  —  DemoECommerceDB")
    print("  Type 'exit' or 'quit' to stop.")
    print("=" * 60)

    while True:
        try:
            question = input("\nYour question: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nGoodbye!")
            break

        if not question:
            continue
        if question.lower() in ("exit", "quit"):
            print("Goodbye!")
            break

        print()
        agent(question)


if __name__ == "__main__":
    main()
