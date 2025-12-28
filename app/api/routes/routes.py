"""Routes endpoints."""

import json
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.schemas.route import (
    RouteSolutionResponse,
    RouteListResponse,
    RouteWaypointResponse,
    ObjectiveValuesResponse,
    ComparisonResponse,
)
from app.services.crud import CRUDService

router = APIRouter()


@router.get("/{job_id}", response_model=RouteListResponse)
async def get_routes_for_job(
    job_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get all Pareto-optimal route solutions for a job."""
    crud = CRUDService(session)

    job = await crud.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    if job.status != "completed":
        raise HTTPException(status_code=400, detail=f"Job not completed (status: {job.status})")

    routes = await crud.get_routes_for_job(job_id)

    route_responses = []
    for route in routes:
        waypoints = await crud.get_waypoints(route.id)

        wp_responses = [
            RouteWaypointResponse(
                sequence=wp.sequence,
                latitude=wp.latitude,
                longitude=wp.longitude,
                eta=wp.eta,
                leg_distance_nm=wp.leg_distance_nm,
                leg_speed_kt=wp.leg_speed,
                leg_fuel_tonnes=wp.leg_fuel,
            )
            for wp in waypoints
        ]

        # Create GeoJSON for visualization
        geojson = {
            "type": "Feature",
            "geometry": {
                "type": "LineString",
                "coordinates": [[wp.longitude, wp.latitude] for wp in waypoints],
            },
            "properties": {
                "route_id": route.id,
                "fuel": route.fuel_consumption,
                "time": route.travel_time,
            },
        }

        # Calculate estimated arrival time
        estimated_arrival = None
        if job.departure_time and route.travel_time:
            estimated_arrival = job.departure_time + timedelta(hours=route.travel_time)
        
        # Calculate fuel cost (approximate marine fuel price: ~$600/tonne)
        fuel_cost_usd = route.fuel_consumption * 600 if route.fuel_consumption else None

        route_responses.append(RouteSolutionResponse(
            route_id=route.id,
            job_id=job_id,
            rank=route.rank,
            objectives=ObjectiveValuesResponse(
                fuel_tonnes=route.fuel_consumption,
                travel_time_hours=route.travel_time,
                risk_score=route.risk_score,
                co2_emissions_tonnes=route.co2_emissions,
                comfort_score=route.comfort_score,
                fuel_cost_usd=fuel_cost_usd,
                estimated_arrival=estimated_arrival,
            ),
            total_distance_nm=route.total_distance_nm,
            waypoint_count=route.waypoint_count,
            average_speed_kt=route.average_speed,
            waypoints=wp_responses,
            comparison=ComparisonResponse(
                fuel_savings_pct=route.fuel_savings_pct,
                time_penalty_pct=route.time_penalty_pct,
                emissions_savings_pct=route.emissions_savings_pct,
            ) if route.fuel_savings_pct else None,
            geojson=geojson,
        ))

    return RouteListResponse(
        job_id=job_id,
        solutions_count=len(route_responses),
        routes=route_responses,
    )


@router.get("/solution/{route_id}", response_model=RouteSolutionResponse)
async def get_single_route(
    route_id: str,
    session: AsyncSession = Depends(get_db),
):
    """Get a single route solution by ID."""
    crud = CRUDService(session)

    route = await crud.get_route(route_id)
    if not route:
        raise HTTPException(status_code=404, detail="Route not found")

    waypoints = await crud.get_waypoints(route_id)

    wp_responses = [
        RouteWaypointResponse(
            sequence=wp.sequence,
            latitude=wp.latitude,
            longitude=wp.longitude,
            eta=wp.eta,
            leg_distance_nm=wp.leg_distance_nm,
            leg_speed_kt=wp.leg_speed,
            leg_fuel_tonnes=wp.leg_fuel,
        )
        for wp in waypoints
    ]

    geojson = {
        "type": "Feature",
        "geometry": {
            "type": "LineString",
            "coordinates": [[wp.longitude, wp.latitude] for wp in waypoints],
        },
        "properties": {"route_id": route.id},
    }

    return RouteSolutionResponse(
        route_id=route.id,
        job_id=route.job_id,
        rank=route.rank,
        objectives=ObjectiveValuesResponse(
            fuel_tonnes=route.fuel_consumption,
            travel_time_hours=route.travel_time,
            risk_score=route.risk_score,
            co2_emissions_tonnes=route.co2_emissions,
            comfort_score=route.comfort_score,
            fuel_cost_usd=route.fuel_consumption * 600 if route.fuel_consumption else None,
        ),
        total_distance_nm=route.total_distance_nm,
        waypoint_count=route.waypoint_count,
        average_speed_kt=route.average_speed,
        waypoints=wp_responses,
        geojson=geojson,
    )
