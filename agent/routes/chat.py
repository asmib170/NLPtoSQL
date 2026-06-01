"""Chat endpoint — SSE streaming of agent responses."""

import json
import time
from typing import AsyncIterator

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from utils.session_factory import get_agent_for_session

router = APIRouter(prefix="/api")


class ChatRequest(BaseModel):
    """Request body for the /api/chat endpoint."""
    message: str
    thread_id: str = ""


@router.post("/chat")
async def chat(request: ChatRequest) -> StreamingResponse:
    """Stream the agent response for the given message as SSE."""
    return StreamingResponse(
        _sse_generator(request.message, request.thread_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


async def _sse_generator(message: str, thread_id: str) -> AsyncIterator[str]:
    """Stream agent response tokens as Server-Sent Events.

    Emits the following SSE event types:
      - [THINKING]: reasoning/thinking content from the model
      - [TOOL]: name of a tool being invoked
      - data: visible text chunks of the final response
      - [METRICS]: JSON object with latency, token usage, and cost
      - [DONE]: signals end of stream
      - [ERROR]: error message if something goes wrong

    Args:
        message: The user's chat message.
        thread_id: The session/thread UUID (or "default").
    """
    start_time = time.time()
    first_token_time = None
    last_tool_name = None
    first_tool = True

    session_agent = get_agent_for_session(thread_id or "default")

    try:
        async for event in session_agent.stream_async(message):
            # Reasoning/thinking content
            if "reasoningText" in event:
                text = event["reasoningText"]
                if text:
                    safe = text.replace("\n", "\\n")
                    yield f"data: [THINKING] {safe}\n\n"

            # Tool starting — only emit if it's a new tool
            if "current_tool_use" in event:
                tool_info = event["current_tool_use"]
                tool_name = tool_info.get("name", "")
                if tool_name and tool_name != last_tool_name:
                    yield f"data: [TOOL] {tool_name}\n\n"
                    prefix = "\\n" if first_tool else ""
                    yield f"data: [THINKING] {prefix}⚙️ Calling {tool_name}...\\n\n\n"
                    last_tool_name = tool_name
                    first_tool = False

            # Tool result received
            if "tool_result" in event:
                last_tool_name = None

            # Visible text chunks
            if "data" in event:
                if first_token_time is None:
                    first_token_time = time.time()
                text = event["data"]
                if text:
                    safe = text.replace("\n", "\\n")
                    yield f"data: {safe}\n\n"

        # Send metrics after stream completes
        total_time = time.time() - start_time
        ttft = (first_token_time - start_time) if first_token_time else None

        metrics_data = {
            "model": "us.anthropic.claude-sonnet-4-5-20250929-v1:0",
            "ttft_ms": round(ttft * 1000) if ttft else None,
            "latency_ms": round(total_time * 1000),
        }

        if hasattr(session_agent, "event_loop_metrics") and session_agent.event_loop_metrics:
            usage = session_agent.event_loop_metrics.accumulated_usage
            metrics_data["input_tokens"] = usage.get("inputTokens", 0)
            metrics_data["output_tokens"] = usage.get("outputTokens", 0)
            metrics_data["total_tokens"] = usage.get("totalTokens", 0)
            metrics_data["cache_read_tokens"] = usage.get("cacheReadInputTokens", 0)
            metrics_data["cache_write_tokens"] = usage.get("cacheWriteInputTokens", 0)

            input_cost = metrics_data["input_tokens"] * 0.000003
            output_cost = metrics_data["output_tokens"] * 0.000015
            metrics_data["estimated_cost_usd"] = round(input_cost + output_cost, 6)

        yield f"data: [METRICS] {json.dumps(metrics_data)}\n\n"
        yield "data: [DONE]\n\n"

    except Exception as exc:  # noqa: BLE001
        error_msg = str(exc).replace("\n", " ")
        yield f"data: [ERROR] {error_msg}\n\n"
