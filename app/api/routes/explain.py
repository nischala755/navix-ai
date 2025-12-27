"""Explainability endpoint."""

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.explain import (
    ExplainResponse,
    RouteDecisionResponse,
    DecisionImpact,
    SensitivityResponse,
)
from app.services.crud import CRUDService
from app.explain.explainer import RouteExplainer

router = APIRouter()


@router.get("/{route_id}", response_model=ExplainResponse)
async def explain_route(
    route_id: str,
    session: AsyncSession = Depends(get_db),
):
    """
    Get explanation for why a specific route was chosen.
    
    Provides trade-off analysis, key decisions, and sensitivity information.
    """
    crud = CRUDService(session)

    route = await crud.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    # Get waypoints
    waypoints = await crud.get_waypoints(route_id)
    route_array = np.array([[wp.latitude, wp.longitude] for wp in waypoints])

    # Get job for weights
    job = await crud.get_job(route.job_id)
    weights = {
        "fuel": job.weight_fuel if job else 0.3,
        "time": job.weight_time if job else 0.25,
        "risk": job.weight_risk if job else 0.2,
        "emissions": job.weight_emissions if job else 0.15,
        "comfort": job.weight_comfort if job else 0.1,
    }

    objectives = {
        "fuel": route.fuel_consumption,
        "time": route.travel_time,
        "risk": route.risk_score,
        "emissions": route.co2_emissions,
        "comfort": route.comfort_score,
    }

    # Generate explanation
    explainer = RouteExplainer()
    explanation = explainer.why_this_route(route_array, objectives, weights)

    # Get stored explanation logs
    logs = await crud.get_explain_logs(route_id)

    decisions = [
        RouteDecisionResponse(
            decision_type=d["type"],
            description=d["description"],
            waypoint_index=d.get("waypoint_index"),
            impact=DecisionImpact(
                fuel_tonnes=d["impact"].get("fuel"),
                time_hours=d["impact"].get("time"),
                risk_delta=d["impact"].get("risk"),
            ),
            trade_off=d["trade_off"],
            confidence=0.85,
        )
        for d in explanation.get("key_decisions", [])
    ]

    # Add logged decisions
    for log in logs:
        decisions.append(RouteDecisionResponse(
            decision_type=log.decision_type,
            description=log.description,
            waypoint_index=log.waypoint_sequence,
            impact=DecisionImpact(
                fuel_tonnes=log.impact_fuel,
                time_hours=log.impact_time,
                risk_delta=log.impact_risk,
            ),
            trade_off=log.trade_off or "",
            confidence=log.confidence,
        ))

    sensitivity = explanation.get("sensitivity", {})

    return ExplainResponse(
        route_id=route_id,
        summary=explanation.get("summary", "Route optimized for balanced objectives."),
        primary_optimization=explanation.get("primary_optimization", "balanced"),
        key_decisions=decisions,
        trade_offs=explanation.get("trade_offs", {}),
        sensitivity=SensitivityResponse(
            fuel_weight_sensitivity=sensitivity.get("fuel_weight", 0),
            time_weight_sensitivity=sensitivity.get("time_weight", 0),
            risk_sensitivity=sensitivity.get("risk_sensitivity", 0),
            comfort_importance=sensitivity.get("comfort_importance", 0),
        ),
        alternatives_considered=explanation.get("alternatives_considered", 0),
        confidence=explanation.get("confidence", 0.8),
    )
