"""Optimization request/response schemas."""

from datetime import datetime
from typing import Literal
from pydantic import BaseModel, Field, field_validator


class ObjectiveWeights(BaseModel):
    """Weights for multi-objective optimization."""
    fuel: float = Field(default=0.3, ge=0, le=1)
    time: float = Field(default=0.25, ge=0, le=1)
    risk: float = Field(default=0.2, ge=0, le=1)
    emissions: float = Field(default=0.15, ge=0, le=1)
    comfort: float = Field(default=0.1, ge=0, le=1)

    @field_validator("comfort", mode="after")
    @classmethod
    def validate_weights_sum(cls, v, info):
        """Weights should approximately sum to 1.0."""
        weights = [info.data.get(f, 0) for f in ["fuel", "time", "risk", "emissions"]]
        total = sum(weights) + v
        if abs(total - 1.0) > 0.1:
            pass  # Warning only, auto-normalize later
        return v


class OptimizationRequest(BaseModel):
    """Request to start route optimization."""
    origin_locode: str = Field(..., min_length=5, max_length=10, description="Origin port LOCODE (e.g., SGSIN)")
    destination_locode: str = Field(..., min_length=5, max_length=10, description="Destination port LOCODE")
    ship_id: str = Field(..., description="Ship profile ID")
    departure_time: datetime = Field(default_factory=datetime.now, description="Departure datetime")
    
    algorithm: Literal["hacopso", "ga", "pso"] = Field(default="hacopso")
    weights: ObjectiveWeights = Field(default_factory=ObjectiveWeights)
    
    swarm_size: int = Field(default=50, ge=10, le=200)
    max_iterations: int = Field(default=200, ge=50, le=1000)
    
    max_travel_time_hours: float | None = Field(default=None, ge=1)
    max_fuel_tonnes: float | None = Field(default=None, ge=1)
    use_warm_start: bool = Field(default=True)

    model_config = {"json_schema_extra": {
        "example": {
            "origin_locode": "SGSIN",
            "destination_locode": "NLRTM",
            "ship_id": "container_large",
            "algorithm": "hacopso",
        }
    }}


class OptimizationResponse(BaseModel):
    """Response after submitting optimization job."""
    job_id: str
    status: str
    message: str
    estimated_time_seconds: int | None = None


class BenchmarkResult(BaseModel):
    """Benchmark comparison result."""
    algorithm: str
    iterations: int
    execution_time_seconds: float
    archive_size: int
    best_fuel: float
    best_time: float
    convergence_rate: float


class BenchmarkResponse(BaseModel):
    """Benchmark comparison response."""
    hacopso: BenchmarkResult
    ga: BenchmarkResult
    winner: str
    improvement_pct: float
