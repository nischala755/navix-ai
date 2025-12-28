"""Route solution schemas."""

from datetime import datetime
from pydantic import BaseModel


class RouteWaypointResponse(BaseModel):
    """Individual waypoint in route."""
    sequence: int
    latitude: float
    longitude: float
    eta: datetime | None = None
    leg_distance_nm: float | None = None
    leg_speed_kt: float | None = None
    leg_fuel_tonnes: float | None = None


class ObjectiveValuesResponse(BaseModel):
    """Objective function values."""
    fuel_tonnes: float
    travel_time_hours: float
    risk_score: float
    co2_emissions_tonnes: float
    comfort_score: float
    fuel_cost_usd: float | None = None
    estimated_arrival: datetime | None = None


class ComparisonResponse(BaseModel):
    """Comparison with baseline route."""
    fuel_savings_pct: float | None = None
    time_penalty_pct: float | None = None
    emissions_savings_pct: float | None = None
    risk_reduction_pct: float | None = None


class RouteSolutionResponse(BaseModel):
    """Complete route solution."""
    route_id: str
    job_id: str
    rank: int
    objectives: ObjectiveValuesResponse
    total_distance_nm: float
    waypoint_count: int
    average_speed_kt: float | None = None
    waypoints: list[RouteWaypointResponse]
    comparison: ComparisonResponse | None = None
    geojson: dict | None = None


class RouteListResponse(BaseModel):
    """List of Pareto-optimal routes."""
    job_id: str
    solutions_count: int
    routes: list[RouteSolutionResponse]
