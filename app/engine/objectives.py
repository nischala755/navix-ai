"""
Objective Functions

Multi-objective fitness evaluation for maritime route optimization.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING

import numpy as np
from numpy.typing import NDArray

if TYPE_CHECKING:
    from app.models.ship import ShipProfile
    from app.ocean.grid import OceanGrid


@dataclass
class ObjectiveValues:
    """Container for multi-objective fitness values."""

    fuel: float  # Fuel consumption (tonnes)
    time: float  # Travel time (hours)
    risk: float  # Combined risk score (0-1)
    emissions: float  # CO2 emissions (tonnes)
    comfort: float  # Comfort score (0-1, higher = better)

    def to_array(self) -> NDArray[np.float64]:
        """Convert to numpy array for Pareto operations."""
        return np.array([self.fuel, self.time, self.risk, self.emissions, 1 - self.comfort])

    @classmethod
    def from_array(cls, arr: NDArray[np.float64]) -> "ObjectiveValues":
        """Create from numpy array."""
        return cls(
            fuel=float(arr[0]),
            time=float(arr[1]),
            risk=float(arr[2]),
            emissions=float(arr[3]),
            comfort=float(1 - arr[4]),
        )


class ObjectiveFunction:
    """
    Multi-objective fitness function for route evaluation.
    
    Evaluates routes based on:
    1. Fuel consumption
    2. Travel time
    3. Risk (storm + piracy)
    4. CO2 emissions
    5. Comfort (wave-based)
    """

    # Emission factor (tonnes CO2 per tonne fuel)
    CO2_FACTOR = 3.114

    def __init__(
        self,
        ship_profile: "ShipProfile",
        ocean_grid: "OceanGrid",
        departure_time: float,  # Unix timestamp
    ):
        """
        Initialize objective function.
        
        Args:
            ship_profile: Ship specifications for fuel/emission calculations.
            ocean_grid: Ocean environment data.
            departure_time: Departure time as Unix timestamp.
        """
        self.ship = ship_profile
        self.ocean = ocean_grid
        self.departure_time = departure_time

    def evaluate(
        self,
        route: NDArray[np.float64],
        speeds: NDArray[np.float64] | None = None,
    ) -> ObjectiveValues:
        """
        Evaluate route fitness.
        
        Args:
            route: Route waypoints as (N, 2) array of [lat, lon].
            speeds: Optional speed profile per leg (N-1 elements). Uses service speed if None.
            
        Returns:
            ObjectiveValues with all objectives computed.
        """
        n_waypoints = len(route)
        if n_waypoints < 2:
            return ObjectiveValues(
                fuel=float("inf"),
                time=float("inf"),
                risk=1.0,
                emissions=float("inf"),
                comfort=0.0,
            )

        # Default to service speed if not specified
        if speeds is None:
            speeds = np.full(n_waypoints - 1, self.ship.service_speed)

        # Calculate metrics per leg
        total_fuel = 0.0
        total_time = 0.0
        total_risk = 0.0
        total_wave_exposure = 0.0
        current_time = self.departure_time

        for i in range(n_waypoints - 1):
            lat1, lon1 = route[i]
            lat2, lon2 = route[i + 1]
            speed = speeds[i]

            # Distance calculation (great circle)
            distance_nm = self._haversine_nm(lat1, lon1, lat2, lon2)

            # Get environmental conditions at midpoint
            mid_lat = (lat1 + lat2) / 2
            mid_lon = (lon1 + lon2) / 2

            resistance = self.ocean.get_resistance(mid_lat, mid_lon, current_time)
            current_u, current_v = self.ocean.get_current_vector(mid_lat, mid_lon, current_time)
            storm_risk = self.ocean.get_storm_risk(mid_lat, mid_lon, current_time)
            piracy_risk = self.ocean.get_piracy_risk(mid_lat, mid_lon)
            wave_height = self.ocean.get_wave_height(mid_lat, mid_lon, current_time)

            # Speed over ground (simplified current effect)
            heading = self._calculate_heading(lat1, lon1, lat2, lon2)
            current_effect = self._current_speed_effect(current_u, current_v, heading)
            effective_speed = max(speed + current_effect, self.ship.min_speed)

            # Time for this leg
            leg_time = distance_nm / effective_speed if effective_speed > 0 else float("inf")
            total_time += leg_time

            # Fuel consumption (adjusted for resistance)
            base_fuel = self.ship.calculate_fuel_consumption(speed, leg_time)
            adjusted_fuel = base_fuel * resistance
            total_fuel += adjusted_fuel

            # Risk accumulation
            leg_risk = max(storm_risk, piracy_risk) * (leg_time / 24)  # Risk-time weighted
            total_risk += leg_risk

            # Comfort (wave exposure)
            total_wave_exposure += wave_height * leg_time

            # Update time for next leg
            current_time += leg_time * 3600  # Convert hours to seconds

        # Normalize risk to 0-1
        risk_score = min(1.0, total_risk)

        # Comfort score (inverse of wave exposure, normalized)
        avg_wave = total_wave_exposure / max(total_time, 1)
        comfort_score = max(0.0, 1.0 - avg_wave / 10.0)  # Normalize by 10m max wave

        # Emissions
        emissions = total_fuel * self.CO2_FACTOR

        return ObjectiveValues(
            fuel=total_fuel,
            time=total_time,
            risk=risk_score,
            emissions=emissions,
            comfort=comfort_score,
        )

    def evaluate_batch(
        self,
        routes: list[NDArray[np.float64]],
        speeds_list: list[NDArray[np.float64] | None] | None = None,
    ) -> list[ObjectiveValues]:
        """
        Evaluate multiple routes.
        
        Args:
            routes: List of route arrays.
            speeds_list: Optional list of speed profiles.
            
        Returns:
            List of ObjectiveValues.
        """
        if speeds_list is None:
            speeds_list = [None] * len(routes)

        return [
            self.evaluate(route, speeds)
            for route, speeds in zip(routes, speeds_list)
        ]

    @staticmethod
    def _haversine_nm(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate great circle distance in nautical miles.
        
        Args:
            lat1, lon1: Start coordinates (degrees).
            lat2, lon2: End coordinates (degrees).
            
        Returns:
            Distance in nautical miles.
        """
        R = 3440.065  # Earth radius in nautical miles

        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlat = np.radians(lat2 - lat1)
        dlon = np.radians(lon2 - lon1)

        a = (
            np.sin(dlat / 2) ** 2
            + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2) ** 2
        )
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        return R * c

    @staticmethod
    def _calculate_heading(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """
        Calculate initial heading from point 1 to point 2.
        
        Returns:
            Heading in degrees (0 = North, 90 = East).
        """
        lat1_rad = np.radians(lat1)
        lat2_rad = np.radians(lat2)
        dlon = np.radians(lon2 - lon1)

        x = np.sin(dlon) * np.cos(lat2_rad)
        y = np.cos(lat1_rad) * np.sin(lat2_rad) - np.sin(lat1_rad) * np.cos(lat2_rad) * np.cos(dlon)

        heading = np.degrees(np.arctan2(x, y))
        return (heading + 360) % 360

    @staticmethod
    def _current_speed_effect(
        current_u: float,
        current_v: float,
        heading: float,
    ) -> float:
        """
        Calculate current effect on speed over ground.
        
        Args:
            current_u: East-west current component (positive = east, m/s).
            current_v: North-south current component (positive = north, m/s).
            heading: Ship heading in degrees.
            
        Returns:
            Speed adjustment in knots (positive = favorable, negative = adverse).
        """
        # Convert current to knots (1 m/s ≈ 1.944 knots)
        current_u_kt = current_u * 1.944
        current_v_kt = current_v * 1.944

        # Project current onto heading
        heading_rad = np.radians(heading)
        ship_dir_east = np.sin(heading_rad)
        ship_dir_north = np.cos(heading_rad)

        # Dot product gives component in ship's direction
        return current_u_kt * ship_dir_east + current_v_kt * ship_dir_north
