"""JSON file-based implementation of ThreadIndexStorage.

Stores thread metadata as individual JSON files (one per thread).
No message content — that's handled by Strands' session manager.

File structure:
  data/threads/
    <session_id>.json   (just metadata: id, title, timestamps, message_count)
"""

import json
import os
import threading
from datetime import datetime
from typing import Optional

from .base import ThreadIndexStorage, ThreadMeta


class JsonFileThreadIndex(ThreadIndexStorage):
    """Persist thread metadata as individual JSON files."""

    def __init__(self, directory: str = ""):
        """Initialize the JSON file thread index.

        Args:
            directory: Path to the directory where thread JSON files are stored.
                       Defaults to agent/data/threads/.
        """
        if not directory:
            from utils import THREADS_DIR
            directory = THREADS_DIR
        self._directory = directory
        self._lock = threading.Lock()
        os.makedirs(self._directory, exist_ok=True)

    def _thread_path(self, thread_id: str) -> str:
        """Return the filesystem path for a thread's JSON file."""
        safe_id = "".join(c for c in thread_id if c.isalnum() or c in "-_")
        return os.path.join(self._directory, f"{safe_id}.json")

    def list_threads(self) -> list[ThreadMeta]:
        """Return all threads, ordered by most recently updated first."""
        threads = []
        with self._lock:
            for filename in os.listdir(self._directory):
                if not filename.endswith(".json"):
                    continue
                path = os.path.join(self._directory, filename)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    threads.append(ThreadMeta.from_dict(data))
                except (json.JSONDecodeError, KeyError):
                    continue
        threads.sort(key=lambda t: t.updated_at, reverse=True)
        return threads

    def get_thread(self, thread_id: str) -> Optional[ThreadMeta]:
        """Return a single thread by ID, or None if not found."""
        path = self._thread_path(thread_id)
        with self._lock:
            if not os.path.exists(path):
                return None
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return ThreadMeta.from_dict(json.load(f))
            except (json.JSONDecodeError, KeyError):
                return None

    def create_thread(self, thread: ThreadMeta) -> ThreadMeta:
        """Persist a new thread. Sets created_at/updated_at if empty."""
        now = datetime.now().isoformat()
        if not thread.created_at:
            thread.created_at = now
        if not thread.updated_at:
            thread.updated_at = now
        with self._lock:
            with open(self._thread_path(thread.id), "w", encoding="utf-8") as f:
                json.dump(thread.to_dict(), f, indent=2)
        return thread

    def update_thread(self, thread: ThreadMeta) -> ThreadMeta:
        """Update an existing thread. Refreshes updated_at timestamp."""
        thread.updated_at = datetime.now().isoformat()
        with self._lock:
            with open(self._thread_path(thread.id), "w", encoding="utf-8") as f:
                json.dump(thread.to_dict(), f, indent=2)
        return thread

    def delete_thread(self, thread_id: str) -> bool:
        """Delete a thread's JSON file. Returns True if deleted, False if not found."""
        path = self._thread_path(thread_id)
        with self._lock:
            if os.path.exists(path):
                os.remove(path)
                return True
        return False
