"""Benchmark endpoint."""

import time
import numpy as np
from fastapi import APIRouter

from app.engine.hacopso import HACOPSOEngine, HACOPSOConfig
from app.engine.genetic import GeneticAlgorithm, GAConfig
from app.engine.objectives import ObjectiveFunction
from app.engine.constraints import ConstraintHandler
from app.ocean.grid import OceanGrid
from app.schemas.optimization import BenchmarkResponse, BenchmarkResult

router = APIRouter()


class MockShipProfile:
    """Mock ship profile for benchmarking."""
    service_speed = 14.0
    min_speed = 8.0
    max_speed = 18.0
    sfc_design = 180.0
    ship_type = "container"

    def calculate_fuel_consumption(self, speed: float, hours: float) -> float:
        return 0.5 * hours * (speed / self.service_speed) ** 3


@router.get("", response_model=BenchmarkResponse)
async def run_benchmark():
    """
    Run benchmark comparison between HACOPSO and GA.
    
    Uses a fixed test case for reproducible results.
    """
    # Test case: Singapore to Rotterdam
    origin = (1.29, 103.85)
    destination = (51.95, 4.48)

    # Setup environment
    ocean = OceanGrid()
    ship = MockShipProfile()

    objective = ObjectiveFunction(
        ship_profile=ship,
        ocean_grid=ocean,
        departure_time=time.time(),
    )

    constraints = ConstraintHandler(
        ocean_grid=ocean,
        min_speed=ship.min_speed,
        max_speed=ship.max_speed,
    )

    # Run HACOPSO
    hacopso_config = HACOPSOConfig(
        swarm_size=30,
        max_iterations=50,
        archive_size=50,
    )

    hacopso = HACOPSOEngine(
        config=hacopso_config,
        objective_func=objective,
        constraint_handler=constraints,
        origin=origin,
        destination=destination,
    )

    start = time.time()
    hacopso_result = hacopso.optimize()
    hacopso_time = time.time() - start

    # Run GA
    ga_config = GAConfig(
        population_size=30,
        max_generations=50,
    )

    ga = GeneticAlgorithm(
        config=ga_config,
        objective_func=objective,
        constraint_handler=constraints,
        origin=origin,
        destination=destination,
    )

    start = time.time()
    ga_result = ga.optimize()
    ga_time = time.time() - start

    # Extract best results
    hacopso_solutions = hacopso_result.get("solutions", [])
    ga_solutions = ga_result.get("solutions", [])

    hacopso_best_fuel = min([s["objectives"]["fuel"] for s in hacopso_solutions], default=float("inf"))
    hacopso_best_time = min([s["objectives"]["time"] for s in hacopso_solutions], default=float("inf"))

    ga_best_fuel = min([s["objectives"]["fuel"] for s in ga_solutions], default=float("inf"))
    ga_best_time = min([s["objectives"]["time"] for s in ga_solutions], default=float("inf"))

    # Calculate convergence rate
    hacopso_convergence = hacopso_result.get("convergence", [])
    ga_convergence = ga_result.get("convergence", []) if "convergence" in ga_result else []

    hacopso_rate = (hacopso_convergence[0] - hacopso_convergence[-1]) / max(len(hacopso_convergence), 1) if hacopso_convergence else 0
    ga_rate = 0  # GA doesn't track convergence the same way

    # Determine winner
    hacopso_score = hacopso_best_fuel + hacopso_best_time * 0.1
    ga_score = ga_best_fuel + ga_best_time * 0.1

    winner = "HACOPSO" if hacopso_score <= ga_score else "GA"
    improvement = abs(hacopso_score - ga_score) / max(ga_score, 1) * 100

    return BenchmarkResponse(
        hacopso=BenchmarkResult(
            algorithm="HACOPSO",
            iterations=hacopso_result.get("iterations", 50),
            execution_time_seconds=hacopso_time,
            archive_size=hacopso_result.get("archive_size", 0),
            best_fuel=hacopso_best_fuel,
            best_time=hacopso_best_time,
            convergence_rate=hacopso_rate,
        ),
        ga=BenchmarkResult(
            algorithm="GA (NSGA-II)",
            iterations=ga_result.get("generations", 50),
            execution_time_seconds=ga_time,
            archive_size=ga_result.get("archive_size", 0),
            best_fuel=ga_best_fuel,
            best_time=ga_best_time,
            convergence_rate=ga_rate,
        ),
        winner=winner,
        improvement_pct=improvement,
    )
