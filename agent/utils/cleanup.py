"""TTL-based cleanup for charts and thread data.

Deletes files older than the configured TTL (default 30 days).
Can be run standalone or called from server startup.
"""

import os
import shutil
import time
from pathlib import Path

from .config import DATA_TTL_DAYS, CHARTS_DIR, THREADS_DIR, SESSIONS_DIR

TTL_DAYS = DATA_TTL_DAYS


def _cleanup_charts(ttl_days: int = TTL_DAYS) -> int:
    """Delete chart PNG files older than ttl_days. Returns count of deleted files."""
    charts_path = Path(CHARTS_DIR)
    if not charts_path.exists():
        return 0
    deleted = 0
    cutoff = time.time() - (ttl_days * 86400)
    for f in charts_path.iterdir():
        if f.is_file() and f.suffix == ".png" and os.path.getmtime(f) < cutoff:
            f.unlink()
            deleted += 1
    return deleted


def _cleanup_threads(ttl_days: int = TTL_DAYS) -> int:
    """Delete thread metadata JSON files older than ttl_days. Returns count deleted."""
    threads_path = Path(THREADS_DIR)
    if not threads_path.exists():
        return 0
    deleted = 0
    cutoff = time.time() - (ttl_days * 86400)
    for f in threads_path.iterdir():
        if f.is_file() and f.suffix == ".json" and os.path.getmtime(f) < cutoff:
            f.unlink()
            deleted += 1
    return deleted


def _cleanup_sessions(ttl_days: int = TTL_DAYS) -> int:
    """Delete session directories older than ttl_days. Returns count deleted."""
    sessions_path = Path(SESSIONS_DIR)
    if not sessions_path.exists():
        return 0
    deleted = 0
    cutoff = time.time() - (ttl_days * 86400)
    for d in sessions_path.iterdir():
        if d.is_dir() and os.path.getmtime(d) < cutoff:
            shutil.rmtree(d, ignore_errors=True)
            deleted += 1
    return deleted


def run_cleanup(ttl_days: int = TTL_DAYS) -> dict:
    """Run all cleanup tasks (charts, threads, sessions).

    Args:
        ttl_days: Files older than this many days are deleted.

    Returns:
        Dict with keys: ttl_days, charts_deleted, threads_deleted, sessions_deleted.
    """
    results = {
        "ttl_days": ttl_days,
        "charts_deleted": _cleanup_charts(ttl_days),
        "threads_deleted": _cleanup_threads(ttl_days),
        "sessions_deleted": _cleanup_sessions(ttl_days),
    }
    return results


if __name__ == "__main__":
    print(f"Running cleanup (TTL = {TTL_DAYS} days)...")
    results = run_cleanup()
    print(f"  Charts deleted:   {results['charts_deleted']}")
    print(f"  Threads deleted:  {results['threads_deleted']}")
    print(f"  Sessions deleted: {results['sessions_deleted']}")
    print("Done.")

