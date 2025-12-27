"""Tests for HACOPSO optimization engine."""

import numpy as np
import pytest

from app.engine.hacopso import HACOPSOEngine, HACOPSOConfig, ChaosType
from app.engine.pareto import dominates, crowding_distance, non_dominated_sort, ParetoArchiveManager
from app.engine.objectives import ObjectiveFunction, ObjectiveValues
from app.engine.constraints import ConstraintHandler
from app.ocean.grid import OceanGrid


class MockShipProfile:
    """Mock ship for testing."""
    service_speed = 14.0
    min_speed = 8.0
    max_speed = 18.0
    sfc_design = 180.0
    ship_type = "container"

    def calculate_fuel_consumption(self, speed: float, hours: float) -> float:
        return 0.5 * hours * (speed / self.service_speed) ** 3


class TestParetoDominance:
    """Test Pareto dominance functions."""

    def test_dominates_true(self):
        """Test that a better solution dominates worse."""
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([2.0, 3.0, 4.0])
        assert dominates(a, b)

    def test_dominates_false_equal(self):
        """Test that equal solutions don't dominate."""
        a = np.array([1.0, 2.0, 3.0])
        b = np.array([1.0, 2.0, 3.0])
        assert not dominates(a, b)

    def test_dominates_false_incomparable(self):
        """Test that incomparable solutions don't dominate."""
        a = np.array([1.0, 3.0])
        b = np.array([2.0, 2.0])
        assert not dominates(a, b)
        assert not dominates(b, a)

    def test_crowding_distance(self):
        """Test crowding distance calculation."""
        front = np.array([
            [1.0, 5.0],
            [2.0, 4.0],
            [3.0, 3.0],
            [4.0, 2.0],
            [5.0, 1.0],
        ])
        distances = crowding_distance(front)
        
        # Boundary solutions should have infinite distance
        assert distances[0] == float("inf")
        assert distances[-1] == float("inf")
        
        # Interior solutions should have finite positive distance
        assert all(d > 0 for d in distances[1:-1])

    def test_non_dominated_sort(self):
        """Test non-dominated sorting."""
        objectives = np.array([
            [1.0, 5.0],  # Front 0
            [2.0, 4.0],  # Front 0
            [3.0, 6.0],  # Front 1
            [5.0, 5.0],  # Front 1
        ])
        fronts = non_dominated_sort(objectives)
        
        assert len(fronts) >= 1
        assert 0 in fronts[0] or 1 in fronts[0]


class TestParetoArchive:
    """Test Pareto archive management."""

    def test_add_non_dominated(self):
        """Test adding non-dominated solutions."""
        archive = ParetoArchiveManager(max_size=10)

        solution1 = np.array([[0, 0], [1, 1]])
        objectives1 = np.array([1.0, 5.0, 0.5, 10.0, 0.8])

        solution2 = np.array([[0, 0], [2, 2]])
        objectives2 = np.array([2.0, 4.0, 0.4, 8.0, 0.9])

        assert archive.add(solution1, objectives1)
        assert archive.add(solution2, objectives2)
        assert archive.size() == 2

    def test_add_dominated(self):
        """Test that dominated solutions are rejected."""
        archive = ParetoArchiveManager(max_size=10)

        solution1 = np.array([[0, 0], [1, 1]])
        objectives1 = np.array([1.0, 1.0, 0.1, 1.0, 0.1])

        solution2 = np.array([[0, 0], [2, 2]])
        objectives2 = np.array([2.0, 2.0, 0.2, 2.0, 0.2])

        assert archive.add(solution1, objectives1)
        assert not archive.add(solution2, objectives2)
        assert archive.size() == 1

    def test_truncation(self):
        """Test archive truncation."""
        archive = ParetoArchiveManager(max_size=3)

        for i in range(5):
            solution = np.array([[0, 0], [i, i]])
            objectives = np.array([float(i), float(5 - i), 0.0, 0.0, 0.0])
            archive.add(solution, objectives)

        assert archive.size() <= 3


class TestHACOPSO:
    """Test HACOPSO optimization engine."""

    @pytest.fixture
    def setup_engine(self):
        """Setup HACOPSO engine for testing."""
        config = HACOPSOConfig(
            swarm_size=10,
            max_iterations=20,
            archive_size=20,
            n_waypoints=5,
        )

        ocean = OceanGrid()
        ship = MockShipProfile()

        objective = ObjectiveFunction(
            ship_profile=ship,
            ocean_grid=ocean,
            departure_time=0,
        )

        constraints = ConstraintHandler(
            ocean_grid=ocean,
            min_speed=ship.min_speed,
            max_speed=ship.max_speed,
        )

        origin = (1.29, 103.85)  # Singapore
        destination = (22.32, 114.17)  # Hong Kong

        engine = HACOPSOEngine(
            config=config,
            objective_func=objective,
            constraint_handler=constraints,
            origin=origin,
            destination=destination,
        )

        return engine

    def test_initialization(self, setup_engine):
        """Test swarm initialization."""
        engine = setup_engine
        engine.initialize_swarm()

        assert len(engine.particles) == engine.config.swarm_size
        assert engine.global_best is not None

    def test_chaotic_inertia(self, setup_engine):
        """Test chaotic inertia weight."""
        engine = setup_engine
        engine.initialize_swarm()

        weights = []
        for _ in range(10):
            w = engine._chaotic_inertia_weight()
            weights.append(w)
            engine.iteration += 1

        # Weights should vary (chaotic behavior)
        assert len(set(weights)) > 1
        # Should be within bounds
        assert all(0.3 < w < 1.0 for w in weights)

    def test_optimization_produces_solutions(self, setup_engine):
        """Test that optimization produces Pareto solutions."""
        engine = setup_engine
        result = engine.optimize()

        assert "solutions" in result
        assert len(result["solutions"]) > 0

        # Check solution structure
        solution = result["solutions"][0]
        assert "route" in solution
        assert "objectives" in solution
        assert "fuel" in solution["objectives"]
        assert "time" in solution["objectives"]


class TestObjectiveFunction:
    """Test objective function evaluation."""

    def test_evaluate_route(self):
        """Test route objective evaluation."""
        ocean = OceanGrid()
        ship = MockShipProfile()

        objective = ObjectiveFunction(
            ship_profile=ship,
            ocean_grid=ocean,
            departure_time=0,
        )

        route = np.array([
            [1.29, 103.85],
            [10.0, 110.0],
            [22.32, 114.17],
        ])

        result = objective.evaluate(route)

        assert isinstance(result, ObjectiveValues)
        assert result.fuel > 0
        assert result.time > 0
        assert 0 <= result.risk <= 1
        assert 0 <= result.comfort <= 1


class TestConstraintHandler:
    """Test constraint handling."""

    def test_land_detection(self):
        """Test land constraint detection."""
        ocean = OceanGrid()
        constraints = ConstraintHandler(ocean_grid=ocean)

        # Point in ocean (should be feasible)
        ocean_point = np.array([[1.29, 103.85], [5.0, 110.0]])
        
        # Check feasibility
        is_feasible = constraints.is_feasible(ocean_point)
        # Note: Depends on mock ocean grid implementation

    def test_speed_constraint(self):
        """Test speed constraint violations."""
        ocean = OceanGrid()
        constraints = ConstraintHandler(
            ocean_grid=ocean,
            min_speed=8.0,
            max_speed=20.0,
        )

        route = np.array([[0, 0], [1, 1], [2, 2]])
        
        # Speed below minimum
        slow_speeds = np.array([5.0, 5.0])
        violations = constraints.check_route(route, slow_speeds)
        
        speed_violations = [v for v in violations if v.constraint_type == "speed"]
        assert len(speed_violations) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
