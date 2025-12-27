"""Job status schemas."""

from datetime import datetime
from pydantic import BaseModel


class JobStatusResponse(BaseModel):
    """Optimization job status."""
    job_id: str
    status: str  # pending, queued, running, completed, failed, cancelled
    algorithm: str
    origin: str
    destination: str
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    iterations_completed: int = 0
    solutions_count: int = 0
    error_message: str | None = None
    progress_pct: float = 0.0


class JobListResponse(BaseModel):
    """List of jobs with pagination."""
    jobs: list[JobStatusResponse]
    total: int
    page: int
    page_size: int
