"""Thread management endpoints — CRUD for chat thread metadata."""

import json
import os
import shutil
import uuid

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from utils import TITLE_MAX_WORDS, SUMMARY_MAX_WORDS, SESSIONS_DIR, TITLE_GEN_MAX_TOKENS, CONVERSATION_WINDOW_SIZE
from utils import converse_json
from storage import JsonFileThreadIndex, ThreadMeta

router = APIRouter(prefix="/api")

# Thread index instance
thread_index = JsonFileThreadIndex()


# ------------------------------------------------------------------ #
# Helper: load messages from session storage
# ------------------------------------------------------------------ #
def _load_session_messages(session_id: str) -> list[dict]:
    """Load messages from Strands FileSessionManager storage.

    Reads the individual message JSON files from the session directory,
    extracts user/assistant text content, and returns them as simple dicts.

    Args:
        session_id: The UUID session/thread identifier.

    Returns:
        List of message dicts with keys: id, role, content, timestamp.
    """
    messages_dir = os.path.join(
        SESSIONS_DIR, f"session_{session_id}", "agents", "agent_default", "messages"
    )
    if not os.path.exists(messages_dir):
        return []

    message_files = []
    for filename in os.listdir(messages_dir):
        if filename.startswith("message_") and filename.endswith(".json"):
            index = int(filename[len("message_"):-5])
            message_files.append((index, filename))
    message_files.sort()

    result = []
    for index, filename in message_files:
        filepath = os.path.join(messages_dir, filename)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            msg = data.get("message", {})
            role = msg.get("role", "")
            content_blocks = msg.get("content", [])

            text_parts = []
            for block in content_blocks:
                if "text" in block:
                    text_parts.append(block["text"])

            text = "\n".join(text_parts).strip()
            if role in ("user", "assistant") and text:
                result.append({
                    "id": f"msg-{index}",
                    "role": role,
                    "content": text,
                    "timestamp": data.get("created_at", ""),
                })
        except (ValueError, json.JSONDecodeError, KeyError):
            continue

    return result


# ------------------------------------------------------------------ #
# Request models
# ------------------------------------------------------------------ #
class CreateThreadRequest(BaseModel):
    """Request body for POST /api/threads."""
    title: str = "New Chat"


class UpdateThreadRequest(BaseModel):
    """Request body for PUT /api/threads/{thread_id}."""
    title: str | None = None
    summary: str | None = None
    message_count: int | None = None


class GenerateTitleRequest(BaseModel):
    """Request body for POST /api/threads/generate-title."""
    thread_id: str


# ------------------------------------------------------------------ #
# Endpoints
# ------------------------------------------------------------------ #
@router.get("/threads")
async def list_threads() -> list[dict]:
    """Return all thread metadata for the sidebar."""
    return [t.to_dict() for t in thread_index.list_threads()]


@router.get("/threads/{thread_id}")
async def get_thread(thread_id: str) -> dict:
    """Return thread metadata plus messages from session storage."""
    thread = thread_index.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    messages = _load_session_messages(thread_id)
    result = thread.to_dict()
    result["messages"] = messages
    return result


@router.post("/threads")
async def create_thread(request: CreateThreadRequest) -> dict:
    """Create a new thread with a UUID4 session ID (36 chars)."""
    session_id = str(uuid.uuid4())
    thread = ThreadMeta(id=session_id, title=request.title, created_at="", updated_at="")
    created = thread_index.create_thread(thread)
    return created.to_dict()


@router.put("/threads/{thread_id}")
async def update_thread_endpoint(thread_id: str, request: UpdateThreadRequest) -> dict:
    """Update thread metadata (title, summary, message_count)."""
    thread = thread_index.get_thread(thread_id)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found")
    if request.title is not None:
        thread.title = request.title
    if request.summary is not None:
        thread.summary = request.summary
    if request.message_count is not None:
        thread.message_count = request.message_count
    updated = thread_index.update_thread(thread)
    return updated.to_dict()


@router.delete("/threads/{thread_id}")
async def delete_thread(thread_id: str) -> dict:
    """Delete a thread and its session data."""
    deleted = thread_index.delete_thread(thread_id)
    session_path = os.path.join(SESSIONS_DIR, f"session_{thread_id}")
    if os.path.exists(session_path):
        shutil.rmtree(session_path, ignore_errors=True)
    return {"deleted": deleted}


@router.post("/threads/generate-title")
def generate_title(request: GenerateTitleRequest) -> dict:
    """Use the LLM to generate a title and summary from the full conversation.

    Uses def (not async def) so FastAPI runs it in a threadpool.
    Uses direct boto3 Converse API — no Agent overhead needed.
    """
    messages = _load_session_messages(request.thread_id)
    if not messages:
        return {"title": "New Chat", "summary": ""}

    # Use only the last N messages (same window as the conversation manager)
    # to keep the title relevant to recent context without excessive I/O
    recent_messages = messages[-CONVERSATION_WINDOW_SIZE * 2:] if len(messages) > CONVERSATION_WINDOW_SIZE * 2 else messages

    conversation = "\n".join(
        f"{m['role'].upper()}: {m['content'][:150]}"
        for m in recent_messages
    )

    system_prompt = (
        f"You generate concise titles and summaries for chat conversations. "
        f"Title must be {TITLE_MAX_WORDS} words or fewer. "
        f"Summary must be {SUMMARY_MAX_WORDS} words or fewer. "
        f"Respond ONLY with valid JSON, no markdown."
    )

    prompt = (
        f"Based on this full conversation, generate a title and summary.\n\n"
        f"Conversation:\n{conversation[:1000]}\n\n"
        f"Respond with ONLY: "
        f'{{"title": "<{TITLE_MAX_WORDS} words max>", '
        f'"summary": "<{SUMMARY_MAX_WORDS} words max>"}}'
    )

    result = converse_json(prompt, system_prompt, max_tokens=TITLE_GEN_MAX_TOKENS)
    if result:
        return {
            "title": result.get("title", "Chat"),
            "summary": result.get("summary", ""),
        }

    # Fallback
    first_user = next((m["content"] for m in messages if m["role"] == "user"), "Chat")
    return {"title": first_user[:30], "summary": ""}


