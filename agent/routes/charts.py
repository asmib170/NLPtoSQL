"""Chart serving endpoint — serves generated PNG chart images."""

from pathlib import Path

from fastapi import APIRouter, HTTPException
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

    Raises:
        HTTPException 400: If filename contains path traversal characters.
        HTTPException 404: If chart file doesn't exist.
    """
    # Reject filenames with path separators or traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    filepath = chart_storage.get_path(filename)
    if not filepath:
        raise HTTPException(status_code=404, detail="Chart not found")

    # Verify resolved path is within charts directory
    resolved = str(Path(filepath).resolve())
    if not resolved.startswith(_CHARTS_DIR_RESOLVED):
        raise HTTPException(status_code=400, detail="Invalid filename")

    return FileResponse(filepath, media_type="image/png")
