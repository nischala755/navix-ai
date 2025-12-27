"""Common schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = "healthy"
    version: str
    environment: str


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str
    detail: str | None = None
    code: str | None = None
