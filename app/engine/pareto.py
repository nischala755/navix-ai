"""
Pareto Archive Management

Non-dominated sorting, crowding distance, and archive maintenance
for multi-objective optimization.
"""

import numpy as np
from numpy.typing import NDArray


def dominates(a: NDArray[np.float64], b: NDArray[np.float64]) -> bool:
    """
    Check if solution 'a' Pareto-dominates solution 'b'.
    
    A solution dominates another if it is at least as good in all
    objectives and strictly better in at least one.
    
    Args:
        a: Objective values for solution a (minimize all).
        b: Objective values for solution b.
        
    Returns:
        True if a dominates b.
    """
    return bool(np.all(a <= b) and np.any(a < b))


def crowding_distance(front: NDArray[np.float64]) -> NDArray[np.float64]:
    """
    Calculate crowding distance for a Pareto front.
    
    Crowding distance measures how close a solution is to its neighbors,
    used to maintain diversity in the archive.
    
    Args:
        front: (N, M) array of N solutions with M objectives.
        
    Returns:
        Array of crowding distances for each solution.
    """
    n = len(front)
    if n == 0:
        return np.array([])
    if n <= 2:
        return np.full(n, float("inf"))

    distances = np.zeros(n)
    n_objectives = front.shape[1]

    for m in range(n_objectives):
        # Sort by this objective
        indices = np.argsort(front[:, m])
        sorted_values = front[indices, m]

        # Boundary solutions get infinite distance
        distances[indices[0]] = float("inf")
        distances[indices[-1]] = float("inf")

        # Objective range for normalization
        obj_range = sorted_values[-1] - sorted_values[0]
        if obj_range < 1e-10:
            continue

        # Interior solutions
        for i in range(1, n - 1):
            distances[indices[i]] += (
                sorted_values[i + 1] - sorted_values[i - 1]
            ) / obj_range

    return distances


def non_dominated_sort(objectives: NDArray[np.float64]) -> list[list[int]]:
    """
    Perform non-dominated sorting (NSGA-II style).
    
    Args:
        objectives: (N, M) array of N solutions with M objectives.
        
    Returns:
        List of fronts, each containing indices of solutions in that front.
    """
    n = len(objectives)
    if n == 0:
        return []

    # Domination data
    domination_count = np.zeros(n, dtype=int)
    dominated_by: list[list[int]] = [[] for _ in range(n)]

    # Compute domination relationships
    for i in range(n):
        for j in range(i + 1, n):
            if dominates(objectives[i], objectives[j]):
                dominated_by[i].append(j)
                domination_count[j] += 1
            elif dominates(objectives[j], objectives[i]):
                dominated_by[j].append(i)
                domination_count[i] += 1

    # Build fronts
    fronts: list[list[int]] = []
    current_front = [i for i in range(n) if domination_count[i] == 0]

    while current_front:
        fronts.append(current_front)
        next_front = []

        for i in current_front:
            for j in dominated_by[i]:
                domination_count[j] -= 1
                if domination_count[j] == 0:
                    next_front.append(j)

        current_front = next_front

    return fronts


class ParetoArchiveManager:
    """
    Manages the Pareto archive for multi-objective optimization.
    
    Maintains a bounded archive of non-dominated solutions with
    diversity preservation using crowding distance.
    """

    def __init__(self, max_size: int = 100):
        """
        Initialize archive.
        
        Args:
            max_size: Maximum number of solutions to keep.
        """
        self.max_size = max_size
        self.solutions: list[NDArray[np.float64]] = []
        self.objectives: list[NDArray[np.float64]] = []
        self.metadata: list[dict] = []  # Additional info per solution

    def add(
        self,
        solution: NDArray[np.float64],
        objective_values: NDArray[np.float64],
        metadata: dict | None = None,
    ) -> bool:
        """
        Attempt to add a solution to the archive.
        
        Args:
            solution: Solution representation (e.g., route waypoints).
            objective_values: Objective function values.
            metadata: Optional metadata dictionary.
            
        Returns:
            True if solution was added, False if dominated.
        """
        # Check if new solution is dominated by any archive member
        for existing in self.objectives:
            if dominates(existing, objective_values):
                return False

        # Remove any archive members dominated by new solution
        indices_to_keep = []
        for i, existing in enumerate(self.objectives):
            if not dominates(objective_values, existing):
                indices_to_keep.append(i)

        self.solutions = [self.solutions[i] for i in indices_to_keep]
        self.objectives = [self.objectives[i] for i in indices_to_keep]
        self.metadata = [self.metadata[i] for i in indices_to_keep]

        # Add new solution
        self.solutions.append(solution.copy())
        self.objectives.append(objective_values.copy())
        self.metadata.append(metadata or {})

        # Truncate if exceeds max size
        if len(self.solutions) > self.max_size:
            self._truncate()

        return True

    def _truncate(self) -> None:
        """Truncate archive to max size using crowding distance."""
        if len(self.solutions) <= self.max_size:
            return

        objectives_array = np.array(self.objectives)
        distances = crowding_distance(objectives_array)

        # Sort by crowding distance (descending) and keep top max_size
        indices = np.argsort(-distances)[: self.max_size]

        self.solutions = [self.solutions[i] for i in indices]
        self.objectives = [self.objectives[i] for i in indices]
        self.metadata = [self.metadata[i] for i in indices]

    def get_best(self, objective_index: int = 0) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
        """
        Get solution with best value for a specific objective.
        
        Args:
            objective_index: Index of objective to optimize.
            
        Returns:
            Tuple of (solution, objectives) or None if empty.
        """
        if not self.objectives:
            return None

        objectives_array = np.array(self.objectives)
        best_idx = np.argmin(objectives_array[:, objective_index])

        return self.solutions[best_idx], self.objectives[best_idx]

    def get_compromise(self, weights: NDArray[np.float64]) -> tuple[NDArray[np.float64], NDArray[np.float64]] | None:
        """
        Get solution closest to ideal using weighted sum.
        
        Args:
            weights: Weights for each objective (should sum to 1).
            
        Returns:
            Tuple of (solution, objectives) or None if empty.
        """
        if not self.objectives:
            return None

        objectives_array = np.array(self.objectives)

        # Normalize objectives to [0, 1]
        obj_min = objectives_array.min(axis=0)
        obj_max = objectives_array.max(axis=0)
        obj_range = obj_max - obj_min
        obj_range[obj_range < 1e-10] = 1  # Avoid division by zero

        normalized = (objectives_array - obj_min) / obj_range

        # Weighted sum
        scores = np.dot(normalized, weights)
        best_idx = np.argmin(scores)

        return self.solutions[best_idx], self.objectives[best_idx]

    def get_all(self) -> list[tuple[NDArray[np.float64], NDArray[np.float64], dict]]:
        """
        Get all archived solutions.
        
        Returns:
            List of (solution, objectives, metadata) tuples.
        """
        return list(zip(self.solutions, self.objectives, self.metadata))

    def size(self) -> int:
        """Return current archive size."""
        return len(self.solutions)

    def clear(self) -> None:
        """Clear all archived solutions."""
        self.solutions.clear()
        self.objectives.clear()
        self.metadata.clear()
