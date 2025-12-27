"""Optimization endpoint."""

from datetime import datetime
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.core.middleware import limiter
from app.schemas.optimization import OptimizationRequest, OptimizationResponse
from app.services.crud import CRUDService
from app.services.optimization import optimization_service
from app.models.ship import ShipProfile

router = APIRouter()


@router.post("/optimize", response_model=OptimizationResponse)
@limiter.limit("10/minute")
async def create_optimization_job(
    request: OptimizationRequest,
    background_tasks: BackgroundTasks,
    session: AsyncSession = Depends(get_db),
):
    """
    Submit a new route optimization job.
    
    Returns immediately with job ID. Use GET /jobs/{job_id} to check status.
    """
    crud = CRUDService(session)

    # Validate origin port
    origin = await crud.get_port_by_locode(request.origin_locode)
    if not origin:
        raise HTTPException(status_code=404, detail=f"Origin port {request.origin_locode} not found")

    # Validate destination port
    destination = await crud.get_port_by_locode(request.destination_locode)
    if not destination:
        raise HTTPException(status_code=404, detail=f"Destination port {request.destination_locode} not found")

    # Validate ship
    ship = await crud.get_ship_by_id(request.ship_id)
    if not ship:
        raise HTTPException(status_code=404, detail=f"Ship profile {request.ship_id} not found")

    # Create job record
    job = await crud.create_job(
        origin_id=origin.id,
        destination_id=destination.id,
        ship_id=ship.id,
        departure_time=request.departure_time,
        algorithm=request.algorithm,
        swarm_size=request.swarm_size,
        max_iterations=request.max_iterations,
        weight_fuel=request.weights.fuel,
        weight_time=request.weights.time,
        weight_risk=request.weights.risk,
        weight_emissions=request.weights.emissions,
        weight_comfort=request.weights.comfort,
        max_travel_time_hours=request.max_travel_time_hours,
        max_fuel_tonnes=request.max_fuel_tonnes,
    )
    await session.commit()

    # Create a mock ship profile object for the optimization
    ship_profile = type("Ship", (), {
        "service_speed": ship.service_speed,
        "min_speed": ship.min_speed,
        "max_speed": ship.max_speed,
        "sfc_design": ship.sfc_design,
        "ship_type": ship.ship_type,
        "calculate_fuel_consumption": lambda self, speed, hours: ship.calculate_fuel_consumption(speed, hours),
    })()

    # Schedule background optimization
    background_tasks.add_task(
        optimization_service.run_optimization,
        job_id=job.id,
        origin=(origin.latitude, origin.longitude),
        destination=(destination.latitude, destination.longitude),
        ship_profile=ship_profile,
        departure_time=request.departure_time,
        algorithm=request.algorithm,
        weights={
            "fuel": request.weights.fuel,
            "time": request.weights.time,
            "risk": request.weights.risk,
            "emissions": request.weights.emissions,
            "comfort": request.weights.comfort,
        },
        swarm_size=request.swarm_size,
        max_iterations=request.max_iterations,
        use_warm_start=request.use_warm_start,
    )

    # Estimate completion time
    estimated_seconds = int(request.max_iterations * request.swarm_size * 0.01)

    return OptimizationResponse(
        job_id=job.id,
        status="pending",
        message=f"Optimization job submitted. Algorithm: {request.algorithm}",
        estimated_time_seconds=estimated_seconds,
    )
