"""
Optimization Job Model

Tracks optimization requests and their execution status.
"""

from datetime import datetime
from enum import Enum

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class JobStatus(str, Enum):
    """Optimization job status enumeration."""

    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class OptimizationJob(Base, UUIDMixin, TimestampMixin):
    """
    Route optimization job tracking.
    
    Records optimization requests, parameters, and execution status.
    """

    __tablename__ = "optimization_jobs"

    # Job status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default=JobStatus.PENDING.value,
        index=True,
    )

    # Origin and destination
    origin_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ports.id"),
        nullable=False,
    )
    destination_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ports.id"),
        nullable=False,
    )

    # Ship profile
    ship_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("ship_profiles.id"),
        nullable=False,
    )

    # Departure time (for time-varying conditions)
    departure_time: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    # Optimization parameters
    algorithm: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="hacopso",
    )  # hacopso, ga, pso
    swarm_size: Mapped[int] = mapped_column(Integer, default=50)
    max_iterations: Mapped[int] = mapped_column(Integer, default=200)

    # Objective weights (normalized to sum = 1.0)
    weight_fuel: Mapped[float] = mapped_column(Float, default=0.3)
    weight_time: Mapped[float] = mapped_column(Float, default=0.25)
    weight_risk: Mapped[float] = mapped_column(Float, default=0.2)
    weight_emissions: Mapped[float] = mapped_column(Float, default=0.15)
    weight_comfort: Mapped[float] = mapped_column(Float, default=0.1)

    # Constraints
    max_travel_time_hours: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_fuel_tonnes: Mapped[float | None] = mapped_column(Float, nullable=True)
    max_risk_threshold: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Execution tracking
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    iterations_completed: Mapped[int] = mapped_column(Integer, default=0)
    
    # Results summary
    solutions_count: Mapped[int] = mapped_column(Integer, default=0)
    best_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_risk: Mapped[float | None] = mapped_column(Float, nullable=True)
    best_emissions: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Error tracking
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Warm start reference
    warm_start_route_id: Mapped[str | None] = mapped_column(
        String(36),
        nullable=True,
    )

    # Relationships
    solutions = relationship("RouteSolution", back_populates="job", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_jobs_status_created", "status", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<OptimizationJob {self.id[:8]} ({self.status})>"

    @property
    def execution_time_seconds(self) -> float | None:
        """Calculate job execution time in seconds."""
        if self.started_at and self.completed_at:
            return (self.completed_at - self.started_at).total_seconds()
        return None

    @property
    def is_terminal(self) -> bool:
        """Check if job is in a terminal state."""
        return self.status in (
            JobStatus.COMPLETED.value,
            JobStatus.FAILED.value,
            JobStatus.CANCELLED.value,
        )
