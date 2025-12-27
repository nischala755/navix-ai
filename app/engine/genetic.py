"""
Genetic Algorithm for Benchmarking

NSGA-II style multi-objective genetic algorithm for comparison with HACOPSO.
"""

from dataclasses import dataclass
import numpy as np
from numpy.typing import NDArray

from app.engine.objectives import ObjectiveFunction, ObjectiveValues
from app.engine.pareto import ParetoArchiveManager, non_dominated_sort, crowding_distance
from app.engine.constraints import ConstraintHandler


@dataclass
class GAConfig:
    population_size: int = 50
    max_generations: int = 200
    crossover_rate: float = 0.9
    mutation_rate: float = 0.1
    mutation_strength: float = 2.0
    n_waypoints: int = 10
    tournament_size: int = 3


@dataclass
class Individual:
    chromosome: NDArray[np.float64]
    speeds: NDArray[np.float64]
    objectives: NDArray[np.float64]
    rank: int = 0
    crowding: float = 0.0


class GeneticAlgorithm:
    """NSGA-II style genetic algorithm for route optimization."""

    def __init__(
        self,
        config: GAConfig,
        objective_func: ObjectiveFunction,
        constraint_handler: ConstraintHandler,
        origin: tuple[float, float],
        destination: tuple[float, float],
    ):
        self.config = config
        self.objective = objective_func
        self.constraints = constraint_handler
        self.origin = np.array(origin)
        self.destination = np.array(destination)
        self.population: list[Individual] = []
        self.archive = ParetoArchiveManager(max_size=100)
        self.generation = 0

    def _get_bounds(self) -> NDArray[np.float64]:
        return np.array([
            [min(self.origin[0], self.destination[0]) - 10, max(self.origin[0], self.destination[0]) + 10],
            [min(self.origin[1], self.destination[1]) - 10, max(self.origin[1], self.destination[1]) + 10],
        ])

    def _create_individual(self, bounds: NDArray[np.float64]) -> Individual:
        n_wp = self.config.n_waypoints
        chrom = np.zeros((n_wp + 2, 2))
        chrom[0] = self.origin
        chrom[-1] = self.destination
        for i in range(1, n_wp + 1):
            t = i / (n_wp + 1)
            base = self.origin * (1 - t) + self.destination * t
            chrom[i] = base + np.random.uniform(-5, 5, 2)
            chrom[i, 0] = np.clip(chrom[i, 0], bounds[0, 0], bounds[0, 1])
            chrom[i, 1] = np.clip(chrom[i, 1], bounds[1, 0], bounds[1, 1])
        speeds = np.full(n_wp + 1, self.objective.ship.service_speed) + np.random.uniform(-2, 2, n_wp + 1)
        speeds = np.clip(speeds, self.objective.ship.min_speed, self.objective.ship.max_speed)
        obj = self.objective.evaluate(chrom, speeds).to_array()
        return Individual(chrom, speeds, obj)

    def initialize_population(self) -> None:
        self.population.clear()
        bounds = self._get_bounds()
        for _ in range(self.config.population_size):
            self.population.append(self._create_individual(bounds))
        self._assign_fitness()

    def _assign_fitness(self) -> None:
        objectives = np.array([ind.objectives for ind in self.population])
        fronts = non_dominated_sort(objectives)
        for rank, front in enumerate(fronts):
            front_obj = objectives[front]
            distances = crowding_distance(front_obj)
            for i, idx in enumerate(front):
                self.population[idx].rank = rank
                self.population[idx].crowding = distances[i]

    def _tournament_select(self) -> Individual:
        candidates = np.random.choice(len(self.population), self.config.tournament_size, replace=False)
        best = None
        for idx in candidates:
            ind = self.population[idx]
            if best is None or ind.rank < best.rank or (ind.rank == best.rank and ind.crowding > best.crowding):
                best = ind
        return best

    def _crossover(self, p1: Individual, p2: Individual) -> tuple[Individual, Individual]:
        if np.random.random() > self.config.crossover_rate:
            return Individual(p1.chromosome.copy(), p1.speeds.copy(), p1.objectives.copy()), \
                   Individual(p2.chromosome.copy(), p2.speeds.copy(), p2.objectives.copy())
        alpha = np.random.random()
        c1_chrom = alpha * p1.chromosome + (1 - alpha) * p2.chromosome
        c2_chrom = (1 - alpha) * p1.chromosome + alpha * p2.chromosome
        c1_chrom[0], c1_chrom[-1] = self.origin, self.destination
        c2_chrom[0], c2_chrom[-1] = self.origin, self.destination
        c1_speeds = alpha * p1.speeds + (1 - alpha) * p2.speeds
        c2_speeds = (1 - alpha) * p1.speeds + alpha * p2.speeds
        c1_obj = self.objective.evaluate(c1_chrom, c1_speeds).to_array()
        c2_obj = self.objective.evaluate(c2_chrom, c2_speeds).to_array()
        return Individual(c1_chrom, c1_speeds, c1_obj), Individual(c2_chrom, c2_speeds, c2_obj)

    def _mutate(self, ind: Individual, bounds: NDArray[np.float64]) -> Individual:
        if np.random.random() > self.config.mutation_rate:
            return ind
        mutated = ind.chromosome.copy()
        for i in range(1, len(mutated) - 1):
            if np.random.random() < 0.3:
                mutated[i] += np.random.normal(0, self.config.mutation_strength, 2)
                mutated[i, 0] = np.clip(mutated[i, 0], bounds[0, 0], bounds[0, 1])
                mutated[i, 1] = np.clip(mutated[i, 1], bounds[1, 0], bounds[1, 1])
        obj = self.objective.evaluate(mutated, ind.speeds).to_array()
        return Individual(mutated, ind.speeds.copy(), obj)

    def evolve(self) -> dict:
        bounds = self._get_bounds()
        offspring: list[Individual] = []
        while len(offspring) < self.config.population_size:
            p1, p2 = self._tournament_select(), self._tournament_select()
            c1, c2 = self._crossover(p1, p2)
            offspring.extend([self._mutate(c1, bounds), self._mutate(c2, bounds)])
        combined = self.population + offspring[:self.config.population_size]
        objectives = np.array([ind.objectives for ind in combined])
        fronts = non_dominated_sort(objectives)
        new_pop: list[Individual] = []
        for front in fronts:
            if len(new_pop) + len(front) <= self.config.population_size:
                new_pop.extend([combined[i] for i in front])
            else:
                front_obj = objectives[front]
                distances = crowding_distance(front_obj)
                sorted_front = sorted(zip(front, distances), key=lambda x: -x[1])
                remaining = self.config.population_size - len(new_pop)
                new_pop.extend([combined[idx] for idx, _ in sorted_front[:remaining]])
                break
        self.population = new_pop
        self._assign_fitness()
        for ind in self.population:
            if ind.rank == 0:
                violations = self.constraints.check_route(ind.chromosome, ind.speeds)
                if not any(v.constraint_type == "land" for v in violations):
                    self.archive.add(ind.chromosome, ind.objectives, {"speeds": ind.speeds.tolist()})
        self.generation += 1
        return {"generation": self.generation, "archive_size": self.archive.size(), "front_size": sum(1 for i in self.population if i.rank == 0)}

    def optimize(self) -> dict:
        self.initialize_population()
        for _ in range(self.config.max_generations):
            self.evolve()
        return {
            "generations": self.generation,
            "archive_size": self.archive.size(),
            "solutions": [{"route": s[0].tolist(), "objectives": {"fuel": s[1][0], "time": s[1][1], "risk": s[1][2], "emissions": s[1][3], "comfort": 1 - s[1][4]}} for s in self.archive.get_all()],
        }
