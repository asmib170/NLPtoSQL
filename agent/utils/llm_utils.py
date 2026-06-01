"""Lightweight LLM utility — direct boto3 Converse API calls.

Use this for simple text completions that don't need tools, sessions,
or agent orchestration (e.g., title generation, sample questions).
"""

import json
import boto3

from .config import MODEL_ID, AWS_REGION

_client = boto3.client("bedrock-runtime", region_name=AWS_REGION)


def converse(prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> str:
    """Make a simple Converse API call and return the text response.

    Args:
        prompt: The user message.
        system_prompt: Optional system instruction.
        max_tokens: Maximum tokens in the response.

    Returns:
        The assistant's text response.
    """
    messages = [{"role": "user", "content": [{"text": prompt}]}]

    kwargs = {
        "modelId": MODEL_ID,
        "messages": messages,
        "inferenceConfig": {"maxTokens": max_tokens},
    }
    if system_prompt:
        kwargs["system"] = [{"text": system_prompt}]

    response = _client.converse(**kwargs)
    output = response.get("output", {}).get("message", {}).get("content", [])

    text_parts = [block["text"] for block in output if "text" in block]
    return "\n".join(text_parts)


def converse_json(prompt: str, system_prompt: str = "", max_tokens: int = 1024) -> dict | None:
    """Make a Converse API call and parse the response as JSON.

    Extracts the first JSON object ({...}) found in the response text.

    Args:
        prompt: The user message.
        system_prompt: Optional system instruction.
        max_tokens: Maximum tokens in the response.

    Returns:
        The parsed dict, or None if no valid JSON object is found.
    """
    text = converse(prompt, system_prompt, max_tokens)
    try:
        json_start = text.find('{')
        json_end = text.rfind('}') + 1
        if 0 <= json_start < json_end:
            return json.loads(text[json_start:json_end])
    except (json.JSONDecodeError, ValueError):
        pass
    return None
