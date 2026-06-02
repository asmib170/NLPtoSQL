"""Chart Generation Tool — generates matplotlib visualizations from query results.

On Linux/Mac: uses Strands' built-in python_repl tool for code execution.
On Windows: uses subprocess (python_repl depends on fcntl which is Unix-only).

Charts are saved as PNG files and served via the FastAPI server.
"""

import json
import os
import platform
import subprocess
import tempfile
import time
from pathlib import Path

from strands import Agent, tool
from strands.models import BedrockModel

# Platform detection
IS_WINDOWS = platform.system() == "Windows"

# Import python_repl only on non-Windows (it uses fcntl)
python_repl = None  # type: ignore
if not IS_WINDOWS:
    try:
        from strands_tools import python_repl  # type: ignore
    except ImportError:
        pass  # Fallback to subprocess

# Directory to store generated charts — from central config
from utils import CHARTS_DIR as _CHARTS_DIR_STR, CHART_MODEL_ID, CHART_MODEL_MAX_TOKENS, VENV_PYTHON, CHART_SUBPROCESS_TIMEOUT, CHART_MIN_ROWS
CHART_DIR = Path(_CHARTS_DIR_STR)

# Chart storage instance — swap to S3ChartStorage for production
from storage import LocalChartStorage
chart_storage = LocalChartStorage(str(CHART_DIR))

# Use the same model for chart code generation
_chart_model = BedrockModel(
    model_id=CHART_MODEL_ID,
    max_tokens=CHART_MODEL_MAX_TOKENS,
)

# System prompt differs slightly based on execution method
_CHART_SYSTEM_PROMPT_REPL = """You are a chart visualization expert. When asked to create a chart:

1. Write Python code using matplotlib
2. Use the python_repl tool to execute the code
3. Save the chart to the EXACT file path specified in the user message

RULES:
- ALWAYS start code with: import matplotlib; matplotlib.use('Agg')
- Then import matplotlib.pyplot as plt
- Use dark theme: plt.rcParams['figure.facecolor'] = '#1a2332', text color '#ecf0f1'
- Colors: ['#818cf8', '#f472b6', '#34d399', '#fbbf24', '#a78bfa', '#22d3ee']
- Save with dpi=100, bbox_inches='tight'
- Embed the full data as a Python literal in the code
- Do NOT use plt.show()
- Choose the most appropriate chart type for the data
- Include proper title, axis labels, and legend
- After success, respond with ONLY: "Chart saved successfully"
"""

_CHART_SYSTEM_PROMPT_SUBPROCESS = """You are a chart visualization expert.
Output ONLY executable Python code — no explanation, no markdown fences, no commentary.

RULES:
- ALWAYS start with: import matplotlib; matplotlib.use('Agg')
- Then import matplotlib.pyplot as plt
- Use dark theme: plt.rcParams['figure.facecolor'] = '#1a2332', text color '#ecf0f1'
- Colors: ['#818cf8', '#f472b6', '#34d399', '#fbbf24', '#a78bfa', '#22d3ee']
- Save with dpi=100, bbox_inches='tight'
- Embed the full data as a Python literal in the code
- Do NOT use plt.show()
- Save to the EXACT file path specified in the user message
- Choose the most appropriate chart type for the data
- Include proper title, axis labels, and legend
- Output ONLY the Python code, nothing else
"""


@tool
def generate_chart(question: str, sql: str, results_json: str) -> str:
    """
    Generate a matplotlib chart/graph from SQL query results.

    Creates a visualization appropriate for the data (bar chart, line chart,
    pie chart, etc.) and saves it as a PNG file. Returns the filename that
    can be used to display the chart in the UI.

    Args:
        question (str): The original user question (used to determine chart type/title).
        sql (str): The SQL query that was executed (for context).
        results_json (str): The JSON string from execute_sql containing
                            "total_row_count", "displayed_rows", "columns", and "rows".

    Returns:
        str: JSON string with "success", "filename", and "message" keys.
    """
    try:
        data = json.loads(results_json)
    except json.JSONDecodeError:
        return json.dumps({"success": False, "filename": None, "message": "Could not parse results JSON."})

    rows = data.get("rows", [])
    columns = data.get("columns", [])

    # Need at least 2 rows for a meaningful chart
    if len(rows) < 2:
        return json.dumps({"success": False, "filename": None, "message": "Not enough data for a chart (need at least 2 rows)."})

    # Generate unique filename
    timestamp = int(time.time())
    filename = f"chart_{timestamp}.png"
    filepath = Path(chart_storage.get_save_path(filename))

    # Prepare data for the prompt (all rows from execute_sql, already capped at MAX_DISPLAY_ROWS)
    data_sample = json.dumps(rows, default=str)

    prompt = (
        f"Create a chart for this data and save it to '{filepath}'.\n\n"
        f"User question: {question}\n"
        f"SQL executed: {sql}\n"
        f"Columns: {columns}\n"
        f"Data ({len(rows)} rows):\n{data_sample}"
    )

    try:
        if IS_WINDOWS:
            return _execute_via_subprocess(prompt, filepath, filename)
        else:
            return _execute_via_repl(prompt, filepath, filename)

    except Exception as exc:
        return json.dumps({
            "success": False,
            "filename": None,
            "message": f"Chart generation failed: {str(exc)[:200]}",
        })


def _execute_via_repl(prompt: str, filepath: Path, filename: str) -> str:
    """Execute chart code using Strands python_repl tool (Linux/Mac).

    Falls back to subprocess if python_repl is unavailable.

    Args:
        prompt: The chart generation prompt for the LLM.
        filepath: Full path where the chart PNG should be saved.
        filename: Just the filename portion (e.g. "chart_123456.png").

    Returns:
        JSON string with "success", "filename", and "message" keys.
    """
    if python_repl is None:
        return _execute_via_subprocess(prompt, filepath, filename)

    chart_agent = Agent(
        model=_chart_model,
        system_prompt=_CHART_SYSTEM_PROMPT_REPL,
        tools=[python_repl],
        callback_handler=None,
    )
    chart_agent(prompt)

    if filepath.exists():
        return json.dumps({
            "success": True,
            "filename": filename,
            "message": "Chart generated successfully.",
        })
    return json.dumps({
        "success": False,
        "filename": None,
        "message": "Chart code executed but file was not created.",
    })


def _execute_via_subprocess(prompt: str, filepath: Path, filename: str) -> str:
    """Execute chart code via subprocess (Windows fallback).

    Uses a tool-less Agent to generate Python code, writes it to a temp file,
    and runs it with the project's venv Python interpreter.

    Args:
        prompt: The chart generation prompt for the LLM.
        filepath: Full path where the chart PNG should be saved.
        filename: Just the filename portion (e.g. "chart_123456.png").

    Returns:
        JSON string with "success", "filename", and "message" keys.
    """
    chart_agent = Agent(
        model=_chart_model,
        system_prompt=_CHART_SYSTEM_PROMPT_SUBPROCESS,
        tools=[],
        callback_handler=None,
    )
    result = str(chart_agent(prompt))

    code = _extract_python_code(result)
    if not code:
        return json.dumps({
            "success": False,
            "filename": None,
            "message": "Could not extract valid Python code from LLM response.",
        })

    # Find the venv Python executable
    python_exe = VENV_PYTHON

    # Write code to a temp file and execute
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False, encoding='utf-8'
    ) as f:
        f.write(code)
        temp_path = f.name

    try:
        proc = subprocess.run(
            [python_exe, temp_path],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
        if proc.returncode != 0:
            return json.dumps({
                "success": False,
                "filename": None,
                "message": f"Chart code execution failed: {proc.stderr[:300]}",
            })
    finally:
        os.unlink(temp_path)

    if filepath.exists():
        return json.dumps({
            "success": True,
            "filename": filename,
            "message": "Chart generated successfully.",
        })
    return json.dumps({
        "success": False,
        "filename": None,
        "message": "Chart code executed but file was not created.",
    })


def _extract_python_code(text: str) -> str | None:
    """Extract Python code from an LLM response.

    Tries multiple strategies:
      1. Look for markdown-fenced code blocks (```python ... ```)
      2. If the response starts with 'import', treat the whole thing as code
      3. Find the first line starting with 'import' or 'from' and take everything after

    Args:
        text: Raw LLM response text.

    Returns:
        Extracted Python code string, or None if no code could be found.
    """
    import re

    # Try to find code in markdown fences
    match = re.search(r"```(?:python)?\s*\n(.*?)```", text, re.DOTALL)
    if match:
        return match.group(1).strip()

    # If the response starts with import, treat the whole thing as code
    stripped = text.strip()
    if stripped.startswith("import "):
        return stripped

    # Look for lines starting with import
    lines = stripped.split('\n')
    code_start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("import ") or line.strip().startswith("from "):
            code_start = i
            break

    if code_start is not None:
        return '\n'.join(lines[code_start:]).strip()

    return None
