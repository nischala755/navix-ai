"""
HACOPSO: Hybrid Adaptive Chaotic Opposition-Based PSO

Multi-objective maritime route optimization with:
- Chaotic inertia weight (logistic/tent/sinusoidal)
- Opposition-based learning
- Pareto archive maintenance
"""

from dataclasses import dataclass
from enum import Enum
from typing import Callable
import numpy as np
from numpy.typing import NDArray

from app.engine.objectives import ObjectiveFunction, ObjectiveValues
from app.engine.pareto import ParetoArchiveManager
from app.engine.constraints import ConstraintHandler


class ChaosType(str, Enum):
    LOGISTIC = "logistic"
    TENT = "tent"
    SINUSOIDAL = "sinusoidal"


@dataclass
class HACOPSOConfig:
    swarm_size: int = 50
    max_iterations: int = 200
    archive_size: int = 100
    w_max: float = 0.9
    w_min: float = 0.4
    c1: float = 2.0
    c2: float = 2.0
    v_max_lat: float = 2.0
    v_max_lon: float = 2.0
    opposition_rate: float = 0.3
    chaos_type: ChaosType = ChaosType.LOGISTIC
    n_waypoints: int = 10
    stagnation_limit: int = 20


@dataclass
class Particle:
    position: NDArray[np.float64]
    velocity: NDArray[np.float64]
    speeds: NDArray[np.float64]
    personal_best: NDArray[np.float64]
    personal_best_obj: NDArray[np.float64]
    fitness: float


class HACOPSOEngine:
    """HACOPSO engine for multi-objective route optimization."""

    def __init__(
        self,
        config: HACOPSOConfig,
        objective_func: ObjectiveFunction,
        constraint_handler: ConstraintHandler,
        origin: tuple[float, float],
        destination: tuple[float, float],
        weights: NDArray[np.float64] | None = None,
    ):
        self.config = config
        self.objective = objective_func
        self.constraints = constraint_handler
        self.origin = np.array(origin)
        self.destination = np.array(destination)
        self.weights = weights if weights is not None else np.array([0.2, 0.2, 0.2, 0.2, 0.2])
        self.archive = ParetoArchiveManager(max_size=config.archive_size)
        self.particles: list[Particle] = []
        self.global_best: NDArray[np.float64] | None = None
        self.global_best_obj: NDArray[np.float64] | None = None
        self.chaos_value = np.random.random()
        self.iteration = 0
        self.stagnation_count = 0
        self.convergence_history: list[float] = []

    def _get_bounds(self) -> NDArray[np.float64]:
        return np.array([
            [min(self.origin[0], self.destination[0]) - 10, max(self.origin[0], self.destination[0]) + 10],
            [min(self.origin[1], self.destination[1]) - 10, max(self.origin[1], self.destination[1]) + 10],
        ])

    def _generate_random_route(self, bounds: NDArray[np.float64]) -> NDArray[np.float64]:
        n_wp = self.config.n_waypoints
        route = np.zeros((n_wp + 2, 2))
        route[0] = self.origin
        route[-1] = self.destination
        for i in range(1, n_wp + 1):
            t = i / (n_wp + 1)
            base = self.origin * (1 - t) + self.destination * t
            route[i] = base + np.random.uniform(-5, 5, 2)
            route[i, 0] = np.clip(route[i, 0], bounds[0, 0], bounds[0, 1])
            route[i, 1] = np.clip(route[i, 1], bounds[1, 0], bounds[1, 1])
        return route

    def _opposition_route(self, route: NDArray[np.float64], bounds: NDArray[np.float64]) -> NDArray[np.float64]:
        opp = route.copy()
        for i in range(1, len(route) - 1):
            opp[i, 0] = bounds[0, 0] + bounds[0, 1] - route[i, 0]
            opp[i, 1] = bounds[1, 0] + bounds[1, 1] - route[i, 1]
            opp[i, 0] = np.clip(opp[i, 0], bounds[0, 0], bounds[0, 1])
            opp[i, 1] = np.clip(opp[i, 1], bounds[1, 0], bounds[1, 1])
        return opp

    def _create_particle(self, route: NDArray[np.float64]) -> Particle:
        velocity = np.random.uniform(-self.config.v_max_lat, self.config.v_max_lat, route.shape)
        speeds = np.full(len(route) - 1, self.objective.ship.service_speed)
        speeds += np.random.uniform(-2, 2, len(speeds))
        speeds = np.clip(speeds, self.objective.ship.min_speed, self.objective.ship.max_speed)
        obj_values = self.objective.evaluate(route, speeds)
        obj_array = obj_values.to_array()
        violations = self.constraints.check_route(route, speeds)
        penalty = self.constraints.calculate_penalty(violations)
        fitness = np.dot(self.weights, obj_array) + penalty
        return Particle(route.copy(), velocity, speeds, route.copy(), obj_array, fitness)

    def _chaotic_inertia_weight(self) -> float:
        if self.config.chaos_type == ChaosType.LOGISTIC:
            self.chaos_value = 4.0 * self.chaos_value * (1 - self.chaos_value)
        elif self.config.chaos_type == ChaosType.TENT:
            self.chaos_value = 2 * self.chaos_value if self.chaos_value < 0.5 else 2 * (1 - self.chaos_value)
        else:
            self.chaos_value = np.sin(np.pi * self.chaos_value)
        self.chaos_value = np.clip(self.chaos_value, 0.01, 0.99)
        progress = self.iteration / self.config.max_iterations
        base_w = self.config.w_max - (self.config.w_max - self.config.w_min) * progress
        return base_w * (1 + 0.5 * (self.chaos_value - 0.5))

    def initialize_swarm(self, warm_start: list[NDArray[np.float64]] | None = None) -> None:
        self.particles.clear()
        bounds = self._get_bounds()
        if warm_start:
            for route in warm_start[:self.config.swarm_size // 4]:
                self.particles.append(self._create_particle(route))
        while len(self.particles) < self.config.swarm_size:
            route = self._generate_random_route(bounds)
            self.particles.append(self._create_particle(route))
            if len(self.particles) < self.config.swarm_size:
                opp = self._opposition_route(route, bounds)
                self.particles.append(self._create_particle(opp))
        self._update_global_best()

    def _update_global_best(self) -> None:
        best = min(self.particles, key=lambda p: p.fitness)
        if self.global_best is None or best.fitness < np.dot(self.weights, self.global_best_obj):
            self.global_best = best.personal_best.copy()
            self.global_best_obj = best.personal_best_obj.copy()
            self.stagnation_count = 0
        else:
            self.stagnation_count += 1

    def iterate(self) -> dict:
        bounds = self._get_bounds()
        inertia = self._chaotic_inertia_weight()
        for p in self.particles:
            r1, r2 = np.random.random(p.position.shape), np.random.random(p.position.shape)
            leader = self.archive.get_compromise(self.weights)[0] if self.archive.size() > 0 else self.global_best
            if leader is None:
                leader = p.personal_best
            cognitive = self.config.c1 * r1 * (p.personal_best - p.position)
            social = self.config.c2 * r2 * (leader - p.position)
            p.velocity = inertia * p.velocity + cognitive + social
            p.velocity = np.clip(p.velocity, -self.config.v_max_lat, self.config.v_max_lat)
            p.position[1:-1] += p.velocity[1:-1]
            p.position[:, 0] = np.clip(p.position[:, 0], bounds[0, 0], bounds[0, 1])
            p.position[:, 1] = np.clip(p.position[:, 1], bounds[1, 0], bounds[1, 1])
            p.position[0], p.position[-1] = self.origin, self.destination
            obj = self.objective.evaluate(p.position, p.speeds)
            obj_arr = obj.to_array()
            violations = self.constraints.check_route(p.position, p.speeds)
            penalty = self.constraints.calculate_penalty(violations)
            p.fitness = np.dot(self.weights, obj_arr) + penalty
            if p.fitness < np.dot(self.weights, p.personal_best_obj):
                p.personal_best, p.personal_best_obj = p.position.copy(), obj_arr.copy()
            if not any(v.constraint_type == "land" for v in violations):
                self.archive.add(p.position, obj_arr, {"speeds": p.speeds.tolist()})
        self._update_global_best()
        if self.stagnation_count >= self.config.stagnation_limit // 2 and np.random.random() < self.config.opposition_rate:
            for p in self.particles:
                opp = self._opposition_route(p.position, bounds)
                opp_obj = self.objective.evaluate(opp, p.speeds).to_array()
                opp_fit = np.dot(self.weights, opp_obj) + self.constraints.calculate_penalty(self.constraints.check_route(opp, p.speeds))
                if opp_fit < p.fitness:
                    p.position, p.fitness = opp, opp_fit
        best_fit = min(p.fitness for p in self.particles)
        self.convergence_history.append(best_fit)
        self.iteration += 1
        return {"iteration": self.iteration, "best_fitness": best_fit, "archive_size": self.archive.size()}

    def optimize(self, warm_start: list[NDArray[np.float64]] | None = None, callback: Callable[[dict], None] | None = None) -> dict:
        self.initialize_swarm(warm_start)
        for _ in range(self.config.max_iterations):
            stats = self.iterate()
            if callback:
                callback(stats)
            if self.stagnation_count >= self.config.stagnation_limit:
                break
        return {
            "iterations": self.iteration,
            "archive_size": self.archive.size(),
            "convergence": self.convergence_history,
            "solutions": [{"route": s[0].tolist(), "objectives": {"fuel": s[1][0], "time": s[1][1], "risk": s[1][2], "emissions": s[1][3], "comfort": 1 - s[1][4]}, "meta": s[2]} for s in self.archive.get_all()],
        }

    def get_best_compromise(self) -> tuple[NDArray[np.float64], ObjectiveValues] | None:
        result = self.archive.get_compromise(self.weights)
        return (result[0], ObjectiveValues.from_array(result[1])) if result else None
