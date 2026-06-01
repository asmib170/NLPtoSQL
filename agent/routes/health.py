"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    """Return a simple health check response ({"status": "ok"})."""
    return {"status": "ok"}
