"""Explainability schemas."""

from pydantic import BaseModel


class DecisionImpact(BaseModel):
    """Impact of a routing decision."""
    fuel_tonnes: float | None = None
    time_hours: float | None = None
    risk_delta: float | None = None
    emissions_tonnes: float | None = None


class RouteDecisionResponse(BaseModel):
    """Individual route decision."""
    decision_type: str
    description: str
    waypoint_index: int | None = None
    impact: DecisionImpact
    trade_off: str
    confidence: float


class SensitivityResponse(BaseModel):
    """Sensitivity analysis results."""
    fuel_weight_sensitivity: float
    time_weight_sensitivity: float
    risk_sensitivity: float
    comfort_importance: float


class ExplainResponse(BaseModel):
    """Route explanation response."""
    route_id: str
    summary: str
    primary_optimization: str
    key_decisions: list[RouteDecisionResponse]
    trade_offs: dict[str, str]
    sensitivity: SensitivityResponse
    alternatives_considered: int
    confidence: float
