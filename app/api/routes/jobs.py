"""Jobs endpoints."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.job import JobStatusResponse, JobListResponse
from app.services.crud import CRUDService

router = APIRouter()


@router.get("/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get optimization job status."""
    crud = CRUDService(session)
    job = await crud.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    # Calculate progress
    progress = 0.0
    if job.status == "completed":
        progress = 100.0
    elif job.status == "running" and job.iterations_completed > 0:
        from app.core.config import settings
        progress = min(99.0, (job.iterations_completed / settings.hacopso_max_iterations) * 100)

    return JobStatusResponse(
        job_id=job.id,
        status=job.status,
        algorithm=job.algorithm,
        origin=job.origin_id,
        destination=job.destination_id,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        iterations_completed=job.iterations_completed,
        solutions_count=job.solutions_count,
        error_message=job.error_message,
        progress_pct=progress,
    )


@router.get("", response_model=JobListResponse)
async def list_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    session: AsyncSession = Depends(get_db),
):
    """List optimization jobs with pagination."""
    crud = CRUDService(session)
    offset = (page - 1) * page_size

    jobs, total = await crud.get_jobs(limit=page_size, offset=offset, status=status)

    return JobListResponse(
        jobs=[
            JobStatusResponse(
                job_id=j.id,
                status=j.status,
                algorithm=j.algorithm,
                origin=j.origin_id,
                destination=j.destination_id,
                created_at=j.created_at,
                started_at=j.started_at,
                completed_at=j.completed_at,
                iterations_completed=j.iterations_completed,
                solutions_count=j.solutions_count,
                error_message=j.error_message,
                progress_pct=100.0 if j.status == "completed" else 0.0,
            )
            for j in jobs
        ],
        total=total,
        page=page,
        page_size=page_size,
    )


@router.delete("/{job_id}")
async def cancel_job(
    job_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Cancel a running optimization job."""
    crud = CRUDService(session)
    job = await crud.get_job(job_id)

    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail=f"Job already {job.status}")

    await crud.update_job_status(job_id, "cancelled")
    await session.commit()

    return {"message": "Job cancelled", "job_id": job_id}
