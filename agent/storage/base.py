"""Abstract base class for thread index storage.

This stores only thread metadata (id, title, timestamps) for the UI sidebar.
Actual conversation messages are managed by Strands' session manager.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class ThreadMeta:
    """Metadata for a chat thread (no messages — those live in session manager)."""

    id: str           # Same as session_id (UUID4, 36 chars)
    title: str        # LLM-generated title (7-8 words)
    created_at: str   # ISO format
    updated_at: str   # ISO format
    message_count: int = 0
    summary: str = ""  # LLM-generated summary (20 words max)

    def to_dict(self) -> dict:
        """Serialize thread metadata to a plain dict for JSON storage."""
        return {
            "id": self.id,
            "title": self.title,
            "summary": self.summary,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "message_count": self.message_count,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "ThreadMeta":
        """Deserialize a ThreadMeta instance from a dict."""
        return cls(
            id=data["id"],
            title=data["title"],
            created_at=data.get("created_at", ""),
            updated_at=data.get("updated_at", ""),
            message_count=data.get("message_count", 0),
            summary=data.get("summary", ""),
        )


class ThreadIndexStorage(ABC):
    """Abstract interface for persisting thread metadata.

    This is lightweight — only stores the sidebar list (id, title, timestamps).
    Conversation content is handled by Strands' session manager (FileSessionManager
    or AgentCoreMemorySessionManager).

    Implementations:
      - JsonFileThreadIndex: local JSON file (development)
      - DynamoDBThreadIndex: AWS DynamoDB (production) — to be implemented later
    """

    @abstractmethod
    def list_threads(self) -> list[ThreadMeta]:
        """Return all threads, ordered by most recently updated first."""
        ...

    @abstractmethod
    def get_thread(self, thread_id: str) -> Optional[ThreadMeta]:
        """Return a single thread by ID, or None if not found."""
        ...

    @abstractmethod
    def create_thread(self, thread: ThreadMeta) -> ThreadMeta:
        """Persist a new thread. Returns the created thread."""
        ...

    @abstractmethod
    def update_thread(self, thread: ThreadMeta) -> ThreadMeta:
        """Update an existing thread. Returns the updated thread."""
        ...

    @abstractmethod
    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread by ID. Returns True if deleted, False if not found."""
        ...
