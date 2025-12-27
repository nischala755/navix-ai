"""
CRUD Service

Database operations for all models.
"""

from datetime import datetime
from typing import Sequence
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    Port, ShipProfile, OptimizationJob, RouteSolution,
    RouteWaypoint, ParetoArchive, ExplainabilityLog, JobStatus,
    OceanCell, StormZone, PiracyZone,
)


class CRUDService:
    """Database CRUD operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    # === Ports ===
    async def get_port_by_locode(self, locode: str) -> Port | None:
        result = await self.session.execute(
            select(Port).where(Port.locode == locode.upper())
        )
        return result.scalar_one_or_none()

    async def get_all_ports(self) -> Sequence[Port]:
        result = await self.session.execute(select(Port))
        return result.scalars().all()

    async def create_port(self, **kwargs) -> Port:
        port = Port(id=str(uuid4()), **kwargs)
        self.session.add(port)
        await self.session.flush()
        return port

    # === Ships ===
    async def get_ship_by_id(self, ship_id: str) -> ShipProfile | None:
        result = await self.session.execute(
            select(ShipProfile).where(ShipProfile.id == ship_id)
        )
        return result.scalar_one_or_none()

    async def get_all_ships(self) -> Sequence[ShipProfile]:
        result = await self.session.execute(select(ShipProfile))
        return result.scalars().all()

    async def create_ship(self, **kwargs) -> ShipProfile:
        ship = ShipProfile(id=str(uuid4()), **kwargs)
        self.session.add(ship)
        await self.session.flush()
        return ship

    # === Jobs ===
    async def create_job(
        self,
        origin_id: str,
        destination_id: str,
        ship_id: str,
        departure_time: datetime,
        algorithm: str = "hacopso",
        **kwargs,
    ) -> OptimizationJob:
        job = OptimizationJob(
            id=str(uuid4()),
            origin_id=origin_id,
            destination_id=destination_id,
            ship_id=ship_id,
            departure_time=departure_time,
            algorithm=algorithm,
            status=JobStatus.PENDING.value,
            **kwargs,
        )
        self.session.add(job)
        await self.session.flush()
        return job

    async def get_job(self, job_id: str) -> OptimizationJob | None:
        result = await self.session.execute(
            select(OptimizationJob).where(OptimizationJob.id == job_id)
        )
        return result.scalar_one_or_none()

    async def update_job_status(
        self,
        job_id: str,
        status: str,
        **kwargs,
    ) -> None:
        await self.session.execute(
            update(OptimizationJob)
            .where(OptimizationJob.id == job_id)
            .values(status=status, **kwargs)
        )

    async def get_jobs(
        self,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
    ) -> tuple[Sequence[OptimizationJob], int]:
        query = select(OptimizationJob)
        if status:
            query = query.where(OptimizationJob.status == status)
        query = query.order_by(OptimizationJob.created_at.desc())
        
        # Count
        from sqlalchemy import func
        count_result = await self.session.execute(
            select(func.count()).select_from(OptimizationJob)
        )
        total = count_result.scalar() or 0
        
        # Paginate
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return result.scalars().all(), total

    # === Routes ===
    async def create_route_solution(
        self,
        job_id: str,
        rank: int,
        fuel: float,
        time: float,
        risk: float,
        emissions: float,
        comfort: float,
        distance: float,
        waypoints: list[dict],
        **kwargs,
    ) -> RouteSolution:
        route = RouteSolution(
            id=str(uuid4()),
            job_id=job_id,
            rank=rank,
            fuel_consumption=fuel,
            travel_time=time,
            risk_score=risk,
            co2_emissions=emissions,
            comfort_score=comfort,
            total_distance_nm=distance,
            waypoint_count=len(waypoints),
            **kwargs,
        )
        self.session.add(route)
        await self.session.flush()

        # Add waypoints
        for i, wp in enumerate(waypoints):
            waypoint = RouteWaypoint(
                id=str(uuid4()),
                route_id=route.id,
                sequence=i,
                latitude=wp["lat"],
                longitude=wp["lon"],
                leg_distance_nm=wp.get("distance"),
                leg_speed=wp.get("speed"),
                leg_fuel=wp.get("fuel"),
            )
            self.session.add(waypoint)

        await self.session.flush()
        return route

    async def get_routes_for_job(self, job_id: str) -> Sequence[RouteSolution]:
        result = await self.session.execute(
            select(RouteSolution)
            .where(RouteSolution.job_id == job_id)
            .order_by(RouteSolution.rank)
        )
        return result.scalars().all()

    async def get_route(self, route_id: str) -> RouteSolution | None:
        result = await self.session.execute(
            select(RouteSolution).where(RouteSolution.id == route_id)
        )
        return result.scalar_one_or_none()

    async def get_waypoints(self, route_id: str) -> Sequence[RouteWaypoint]:
        result = await self.session.execute(
            select(RouteWaypoint)
            .where(RouteWaypoint.route_id == route_id)
            .order_by(RouteWaypoint.sequence)
        )
        return result.scalars().all()

    # === Explainability ===
    async def create_explain_log(
        self,
        route_id: str,
        decision_type: str,
        description: str,
        **kwargs,
    ) -> ExplainabilityLog:
        log = ExplainabilityLog(
            id=str(uuid4()),
            route_id=route_id,
            decision_type=decision_type,
            description=description,
            **kwargs,
        )
        self.session.add(log)
        await self.session.flush()
        return log

    async def get_explain_logs(self, route_id: str) -> Sequence[ExplainabilityLog]:
        result = await self.session.execute(
            select(ExplainabilityLog)
            .where(ExplainabilityLog.route_id == route_id)
        )
        return result.scalars().all()

    # === Ocean Data ===
    async def get_storm_zones(self, active_only: bool = True) -> Sequence[StormZone]:
        query = select(StormZone)
        if active_only:
            query = query.where(StormZone.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_piracy_zones(self, active_only: bool = True) -> Sequence[PiracyZone]:
        query = select(PiracyZone)
        if active_only:
            query = query.where(PiracyZone.is_active == True)
        result = await self.session.execute(query)
        return result.scalars().all()
