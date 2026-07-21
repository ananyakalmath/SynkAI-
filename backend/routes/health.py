"""
Health check route handler.
"""

from fastapi import APIRouter, HTTPException
from backend.models.health import HealthResponse
from backend.utils.logger import get_logger

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health", response_model=HealthResponse, status_code=200)
async def health_check() -> HealthResponse:
    """
    HTTP GET /health endpoint.

    Returns:
        HealthResponse: JSON response {"status": "ok"}.
    
    Raises:
        HTTPException: If an unexpected error occurs during health evaluation.
    """
    try:
        logger.info("Health check endpoint pinged.")
        return HealthResponse(status="ok")
    except Exception as exc:
        logger.error(f"Error during health check: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail="Health check failed")
