"""
Optimization Service

Business logic for route optimization.
"""

import asyncio
import time
from datetime import datetime
from typing import Any

import numpy as np
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db_context
from app.engine.hacopso import HACOPSOEngine, HACOPSOConfig, ChaosType
from app.engine.genetic import GeneticAlgorithm, GAConfig
from app.engine.objectives import ObjectiveFunction
from app.engine.constraints import ConstraintHandler
from app.models import JobStatus
from app.ocean.grid import OceanGrid
from app.memory.route_bank import RouteMemoryBank
from app.services.crud import CRUDService


class OptimizationService:
    """
    Route optimization business logic.
    
    Orchestrates the optimization engine, database operations,
    and route memory bank.
    """

    def __init__(self):
        self.ocean_grid = OceanGrid()
        self.route_bank = RouteMemoryBank()
        self._running_jobs: dict[str, asyncio.Task] = {}

    async def run_optimization(
        self,
        job_id: str,
        origin: tuple[float, float],
        destination: tuple[float, float],
        ship_profile: Any,
        departure_time: datetime,
        algorithm: str = "hacopso",
        weights: dict[str, float] | None = None,
        swarm_size: int = 50,
        max_iterations: int = 200,
        use_warm_start: bool = True,
    ) -> dict:
        """
        Execute route optimization.
        
        This runs as a background task.
        """
        async with get_db_context() as session:
            crud = CRUDService(session)

            try:
                # Update job status to running
                await crud.update_job_status(
                    job_id,
                    JobStatus.RUNNING.value,
                    started_at=datetime.now(),
                )
                await session.commit()

                # Setup objective function
                objective = ObjectiveFunction(
                    ship_profile=ship_profile,
                    ocean_grid=self.ocean_grid,
                    departure_time=departure_time.timestamp(),
                )

                # Setup constraints
                constraints = ConstraintHandler(
                    ocean_grid=self.ocean_grid,
                    min_depth=15.0,
                    min_speed=ship_profile.min_speed,
                    max_speed=ship_profile.max_speed,
                )

                # Get warm start routes
                warm_start = None
                if use_warm_start:
                    warm_start = self.route_bank.get_warm_start_routes(
                        origin, destination, ship_profile.ship_type
                    )

                # Configure and run optimization
                weight_array = np.array([
                    weights.get("fuel", 0.3),
                    weights.get("time", 0.25),
                    weights.get("risk", 0.2),
                    weights.get("emissions", 0.15),
                    weights.get("comfort", 0.1),
                ]) if weights else None

                start_time = time.time()

                if algorithm == "hacopso":
                    result = await self._run_hacopso(
                        objective, constraints, origin, destination,
                        weight_array, swarm_size, max_iterations, warm_start
                    )
                elif algorithm == "ga":
                    result = await self._run_ga(
                        objective, constraints, origin, destination,
                        swarm_size, max_iterations
                    )
                else:  # Default to HACOPSO
                    result = await self._run_hacopso(
                        objective, constraints, origin, destination,
                        weight_array, swarm_size, max_iterations, warm_start
                    )

                execution_time = time.time() - start_time

                # Store solutions
                solutions = result.get("solutions", [])
                for i, sol in enumerate(solutions):
                    route_data = sol.get("route", [])
                    objectives = sol.get("objectives", {})

                    waypoints = [
                        {"lat": wp[0], "lon": wp[1]}
                        for wp in route_data
                    ]

                    route = await crud.create_route_solution(
                        job_id=job_id,
                        rank=i,
                        fuel=objectives.get("fuel", 0),
                        time=objectives.get("time", 0),
                        risk=objectives.get("risk", 0),
                        emissions=objectives.get("emissions", 0),
                        comfort=objectives.get("comfort", 0),
                        distance=self._calculate_distance(route_data),
                        waypoints=waypoints,
                    )

                    # Store in memory bank
                    self.route_bank.store_route(
                        route_id=route.id,
                        origin=origin,
                        destination=destination,
                        waypoints=route_data,
                        objectives=objectives,
                        ship_type=ship_profile.ship_type,
                    )

                # Update job status to completed
                best = solutions[0] if solutions else {}
                await crud.update_job_status(
                    job_id,
                    JobStatus.COMPLETED.value,
                    completed_at=datetime.now(),
                    iterations_completed=result.get("iterations", max_iterations),
                    solutions_count=len(solutions),
                    best_fuel=best.get("objectives", {}).get("fuel"),
                    best_time=best.get("objectives", {}).get("time"),
                    best_risk=best.get("objectives", {}).get("risk"),
                    best_emissions=best.get("objectives", {}).get("emissions"),
                )
                await session.commit()

                return {
                    "job_id": job_id,
                    "status": "completed",
                    "execution_time": execution_time,
                    "solutions": len(solutions),
                }

            except Exception as e:
                await crud.update_job_status(
                    job_id,
                    JobStatus.FAILED.value,
                    completed_at=datetime.now(),
                    error_message=str(e),
                )
                await session.commit()
                raise

    async def _run_hacopso(
        self,
        objective: ObjectiveFunction,
        constraints: ConstraintHandler,
        origin: tuple[float, float],
        destination: tuple[float, float],
        weights: np.ndarray | None,
        swarm_size: int,
        max_iterations: int,
        warm_start: list | None,
    ) -> dict:
        """Run HACOPSO optimization."""
        config = HACOPSOConfig(
            swarm_size=swarm_size,
            max_iterations=max_iterations,
            archive_size=100,
            chaos_type=ChaosType(settings.hacopso_chaos_type),
            w_max=settings.hacopso_w_max,
            w_min=settings.hacopso_w_min,
            c1=settings.hacopso_c1,
            c2=settings.hacopso_c2,
        )

        engine = HACOPSOEngine(
            config=config,
            objective_func=objective,
            constraint_handler=constraints,
            origin=origin,
            destination=destination,
            weights=weights,
        )

        # Run in executor to not block event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            lambda: engine.optimize(warm_start=warm_start),
        )

        return result

    async def _run_ga(
        self,
        objective: ObjectiveFunction,
        constraints: ConstraintHandler,
        origin: tuple[float, float],
        destination: tuple[float, float],
        population_size: int,
        max_generations: int,
    ) -> dict:
        """Run genetic algorithm optimization."""
        config = GAConfig(
            population_size=population_size,
            max_generations=max_generations,
        )

        ga = GeneticAlgorithm(
            config=config,
            objective_func=objective,
            constraint_handler=constraints,
            origin=origin,
            destination=destination,
        )

        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, ga.optimize)

        return result

    def _calculate_distance(self, route: list) -> float:
        """Calculate total route distance in nautical miles."""
        if len(route) < 2:
            return 0.0

        total = 0.0
        for i in range(len(route) - 1):
            lat1, lon1 = route[i][0], route[i][1]
            lat2, lon2 = route[i + 1][0], route[i + 1][1]
            total += self._haversine_nm(lat1, lon1, lat2, lon2)
        return total

    @staticmethod
    def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance in nautical miles."""
        R = 3440.065
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)

        a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c


# Global service instance
optimization_service = OptimizationService()
