"""
Constraint Handling

Manages route constraints including land avoidance, restricted zones,
storm regions, and vessel operational limits.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from app.ocean.grid import OceanGrid


@dataclass
class ConstraintViolation:
    """Details of a constraint violation."""

    constraint_type: str  # land, storm, piracy, depth, speed, fuel
    waypoint_index: int | None
    severity: float  # 0.0 - 1.0
    description: str


class ConstraintHandler:
    """
    Handles route feasibility constraints.
    
    Checks and penalizes routes that violate:
    - Land mass constraints
    - Storm zone avoidance
    - Piracy zone risk
    - Minimum depth requirements
    - Vessel speed limits
    - Fuel capacity constraints
    """

    # Penalty weights for constraint violations
    LAND_PENALTY = 1e6
    STORM_PENALTY = 1e4
    PIRACY_PENALTY = 1e3
    DEPTH_PENALTY = 1e5
    SPEED_PENALTY = 1e2
    FUEL_PENALTY = 1e4

    def __init__(
        self,
        ocean_grid: "OceanGrid",
        min_depth: float = 15.0,  # meters
        min_speed: float = 5.0,  # knots
        max_speed: float = 25.0,  # knots
        max_fuel: float | None = None,  # tonnes
    ):
        """
        Initialize constraint handler.
        
        Args:
            ocean_grid: Ocean environment for spatial queries.
            min_depth: Minimum allowed water depth (meters).
            min_speed: Minimum allowed speed (knots).
            max_speed: Maximum allowed speed (knots).
            max_fuel: Maximum fuel budget (tonnes), None = unlimited.
        """
        self.ocean = ocean_grid
        self.min_depth = min_depth
        self.min_speed = min_speed
        self.max_speed = max_speed
        self.max_fuel = max_fuel

    def check_route(
        self,
        route: NDArray[np.float64],
        speeds: NDArray[np.float64] | None = None,
        time: float | None = None,
        fuel_consumption: float | None = None,
    ) -> list[ConstraintViolation]:
        """
        Check all constraints for a route.
        
        Args:
            route: Route waypoints as (N, 2) array of [lat, lon].
            speeds: Optional speed profile per leg.
            time: Current time as Unix timestamp for time-varying checks.
            fuel_consumption: Total fuel consumption for fuel constraint check.
            
        Returns:
            List of constraint violations.
        """
        violations: list[ConstraintViolation] = []
        time = time or datetime.now().timestamp()

        # Check each waypoint
        for i, (lat, lon) in enumerate(route):
            # Land constraint
            if self.ocean.is_land(lat, lon):
                violations.append(ConstraintViolation(
                    constraint_type="land",
                    waypoint_index=i,
                    severity=1.0,
                    description=f"Waypoint {i} crosses land at ({lat:.4f}, {lon:.4f})",
                ))

            # Depth constraint
            depth = self.ocean.get_depth(lat, lon)
            if depth is not None and depth < self.min_depth:
                violations.append(ConstraintViolation(
                    constraint_type="depth",
                    waypoint_index=i,
                    severity=min(1.0, (self.min_depth - depth) / self.min_depth),
                    description=f"Insufficient depth ({depth:.1f}m) at waypoint {i}",
                ))

            # Storm zone constraint
            storm_risk = self.ocean.get_storm_risk(lat, lon, time)
            if storm_risk > 0.8:  # High risk threshold
                violations.append(ConstraintViolation(
                    constraint_type="storm",
                    waypoint_index=i,
                    severity=storm_risk,
                    description=f"High storm risk ({storm_risk:.2f}) at waypoint {i}",
                ))

            # Piracy zone constraint
            piracy_risk = self.ocean.get_piracy_risk(lat, lon)
            if piracy_risk > 0.7:  # High risk threshold
                violations.append(ConstraintViolation(
                    constraint_type="piracy",
                    waypoint_index=i,
                    severity=piracy_risk,
                    description=f"High piracy risk ({piracy_risk:.2f}) at waypoint {i}",
                ))

        # Check speed constraints
        if speeds is not None:
            for i, speed in enumerate(speeds):
                if speed < self.min_speed:
                    violations.append(ConstraintViolation(
                        constraint_type="speed",
                        waypoint_index=i,
                        severity=min(1.0, (self.min_speed - speed) / self.min_speed),
                        description=f"Speed {speed:.1f}kt below minimum at leg {i}",
                    ))
                elif speed > self.max_speed:
                    violations.append(ConstraintViolation(
                        constraint_type="speed",
                        waypoint_index=i,
                        severity=min(1.0, (speed - self.max_speed) / self.max_speed),
                        description=f"Speed {speed:.1f}kt exceeds maximum at leg {i}",
                    ))

        # Check fuel constraint
        if self.max_fuel is not None and fuel_consumption is not None:
            if fuel_consumption > self.max_fuel:
                violations.append(ConstraintViolation(
                    constraint_type="fuel",
                    waypoint_index=None,
                    severity=min(1.0, (fuel_consumption - self.max_fuel) / self.max_fuel),
                    description=f"Fuel consumption ({fuel_consumption:.1f}t) exceeds limit ({self.max_fuel:.1f}t)",
                ))

        return violations

    def calculate_penalty(
        self,
        violations: list[ConstraintViolation],
    ) -> float:
        """
        Calculate total penalty for constraint violations.
        
        Args:
            violations: List of constraint violations.
            
        Returns:
            Total penalty value.
        """
        total_penalty = 0.0

        for v in violations:
            if v.constraint_type == "land":
                total_penalty += self.LAND_PENALTY * v.severity
            elif v.constraint_type == "depth":
                total_penalty += self.DEPTH_PENALTY * v.severity
            elif v.constraint_type == "storm":
                total_penalty += self.STORM_PENALTY * v.severity
            elif v.constraint_type == "piracy":
                total_penalty += self.PIRACY_PENALTY * v.severity
            elif v.constraint_type == "speed":
                total_penalty += self.SPEED_PENALTY * v.severity
            elif v.constraint_type == "fuel":
                total_penalty += self.FUEL_PENALTY * v.severity

        return total_penalty

    def is_feasible(
        self,
        route: NDArray[np.float64],
        speeds: NDArray[np.float64] | None = None,
        time: float | None = None,
        fuel_consumption: float | None = None,
    ) -> bool:
        """
        Check if route is feasible (no hard constraint violations).
        
        Args:
            route: Route waypoints.
            speeds: Optional speeds.
            time: Current time.
            fuel_consumption: Total fuel.
            
        Returns:
            True if route has no land violations.
        """
        violations = self.check_route(route, speeds, time, fuel_consumption)
        # Only land violations are hard constraints
        return not any(v.constraint_type == "land" for v in violations)

    def repair_route(
        self,
        route: NDArray[np.float64],
        max_iterations: int = 10,
    ) -> NDArray[np.float64]:
        """
        Attempt to repair a route with constraint violations.
        
        Uses perturbation to move waypoints away from violations.
        
        Args:
            route: Route to repair.
            max_iterations: Maximum repair attempts.
            
        Returns:
            Repaired route (may still have violations if unresolvable).
        """
        repaired = route.copy()

        for _ in range(max_iterations):
            violations = self.check_route(repaired)
            land_violations = [v for v in violations if v.constraint_type == "land"]

            if not land_violations:
                break

            for v in land_violations:
                if v.waypoint_index is None:
                    continue

                idx = v.waypoint_index
                if idx == 0 or idx == len(repaired) - 1:
                    continue  # Can't move origin/destination

                # Perturb waypoint toward safe water
                for delta in [0.1, 0.2, 0.5, 1.0]:  # Degrees
                    for direction in [(1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (-1, -1)]:
                        new_lat = repaired[idx, 0] + delta * direction[0]
                        new_lon = repaired[idx, 1] + delta * direction[1]

                        if not self.ocean.is_land(new_lat, new_lon):
                            repaired[idx] = [new_lat, new_lon]
                            break
                    else:
                        continue
                    break

        return repaired

    def interpolate_route(
        self,
        route: NDArray[np.float64],
        resolution_nm: float = 50.0,
    ) -> NDArray[np.float64]:
        """
        Interpolate additional waypoints for finer constraint checking.
        
        Args:
            route: Original route waypoints.
            resolution_nm: Maximum nautical miles between waypoints.
            
        Returns:
            Interpolated route with more waypoints.
        """
        if len(route) < 2:
            return route

        interpolated = [route[0]]

        for i in range(len(route) - 1):
            lat1, lon1 = route[i]
            lat2, lon2 = route[i + 1]

            # Calculate distance
            distance = self._haversine_nm(lat1, lon1, lat2, lon2)
            n_segments = max(1, int(np.ceil(distance / resolution_nm)))

            # Interpolate
            for j in range(1, n_segments):
                t = j / n_segments
                lat = lat1 + t * (lat2 - lat1)
                lon = lon1 + t * (lon2 - lon1)
                interpolated.append([lat, lon])

            interpolated.append(route[i + 1])

        return np.array(interpolated)

    @staticmethod
    def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great circle distance in nautical miles."""
        R = 3440.065
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)

        a = np.sin(dlat / 2) ** 2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c
