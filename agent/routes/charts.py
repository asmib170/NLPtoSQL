"""Chart serving endpoint — serves generated PNG chart images."""

import os
from pathlib import Path

from fastapi import APIRouter
from fastapi.responses import FileResponse

from tools import chart_storage
from utils import CHARTS_DIR

router = APIRouter(prefix="/api")

_CHARTS_DIR_RESOLVED = str(Path(CHARTS_DIR).resolve())


@router.get("/charts/{filename}")
async def serve_chart(filename: str):
    """Serve a generated chart PNG file.

    Validates that the resolved path stays within the charts directory
    to prevent path traversal attacks.
    """
    # Reject filenames with path separators or traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        return {"error": "Invalid filename"}

    filepath = chart_storage.get_path(filename)
    if not filepath:
        return {"error": "Chart not found"}

    # Verify resolved path is within charts directory
    resolved = str(Path(filepath).resolve())
    if not resolved.startswith(_CHARTS_DIR_RESOLVED):
        return {"error": "Invalid filename"}

    return FileResponse(filepath, media_type="image/png")
