"""
Pydantic response models for health endpoints.
"""

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """
    Pydantic model representing the response for GET /health.
    """
    status: str = Field(default="ok", description="Operational status of the API")
