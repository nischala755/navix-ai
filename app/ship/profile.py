"""
Ship Profile Manager

Manages ship profiles and provides fuel/power calculations.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class ShipSpecs:
    """Ship specifications for optimization."""
    imo_number: str
    name: str
    ship_type: str
    length_overall: float  # meters
    beam: float  # meters
    draft_design: float  # meters
    deadweight: float  # tonnes
    engine_power: float  # kW
    design_speed: float  # knots
    service_speed: float  # knots
    min_speed: float  # knots
    max_speed: float  # knots
    sfc_design: float  # g/kWh
    fuel_type: str
    block_coefficient: float


class ShipProfileManager:
    """Manages ship profiles and calculations."""

    # Standard ship profiles
    DEFAULT_PROFILES = {
        "container_large": ShipSpecs(
            imo_number="9876543",
            name="Large Container Ship",
            ship_type="container",
            length_overall=400,
            beam=59,
            draft_design=14.5,
            deadweight=200000,
            engine_power=80000,
            design_speed=24,
            service_speed=20,
            min_speed=10,
            max_speed=25,
            sfc_design=170,
            fuel_type="VLSFO",
            block_coefficient=0.65,
        ),
        "tanker_vlcc": ShipSpecs(
            imo_number="9876544",
            name="VLCC Tanker",
            ship_type="tanker",
            length_overall=333,
            beam=60,
            draft_design=22,
            deadweight=300000,
            engine_power=36000,
            design_speed=15,
            service_speed=13,
            min_speed=8,
            max_speed=16,
            sfc_design=180,
            fuel_type="VLSFO",
            block_coefficient=0.82,
        ),
        "bulk_capesize": ShipSpecs(
            imo_number="9876545",
            name="Capesize Bulk Carrier",
            ship_type="bulk_carrier",
            length_overall=300,
            beam=50,
            draft_design=18,
            deadweight=180000,
            engine_power=20000,
            design_speed=14,
            service_speed=12,
            min_speed=8,
            max_speed=15,
            sfc_design=185,
            fuel_type="VLSFO",
            block_coefficient=0.85,
        ),
    }

    def __init__(self):
        self.profiles: dict[str, ShipSpecs] = self.DEFAULT_PROFILES.copy()

    def get_profile(self, profile_id: str) -> ShipSpecs | None:
        """Get ship profile by ID."""
        return self.profiles.get(profile_id)

    def add_profile(self, profile_id: str, specs: ShipSpecs) -> None:
        """Add a new ship profile."""
        self.profiles[profile_id] = specs

    def calculate_power(self, specs: ShipSpecs, speed: float) -> float:
        """
        Calculate required power for speed using admiralty formula.
        
        P ∝ Δ^(2/3) × V^3
        """
        displacement = specs.deadweight * 1.1  # Approximate full displacement
        power_coef = specs.engine_power / (displacement**(2/3) * specs.design_speed**3)
        return power_coef * displacement**(2/3) * speed**3

    def calculate_fuel_rate(self, specs: ShipSpecs, speed: float) -> float:
        """
        Calculate fuel consumption rate (tonnes/day).
        """
        power = self.calculate_power(specs, speed)
        # SFC in g/kWh, convert to tonnes/day
        return power * specs.sfc_design * 24 / 1_000_000

    def calculate_fuel_consumption(
        self,
        specs: ShipSpecs,
        speed: float,
        distance_nm: float,
    ) -> float:
        """
        Calculate fuel consumption for voyage segment.
        
        Returns fuel in tonnes.
        """
        if speed <= 0:
            return 0.0
        hours = distance_nm / speed
        daily_rate = self.calculate_fuel_rate(specs, speed)
        return daily_rate * hours / 24

    def get_optimal_speed_range(self, specs: ShipSpecs) -> tuple[float, float]:
        """Get economical speed range for vessel."""
        # Typically 75-90% of service speed
        return specs.service_speed * 0.75, specs.service_speed * 0.95

    def estimate_voyage_fuel(
        self,
        specs: ShipSpecs,
        distance_nm: float,
        target_time_hours: float | None = None,
    ) -> dict:
        """
        Estimate voyage fuel consumption.
        
        Returns dict with speed options and fuel consumption.
        """
        results = []
        
        for speed in np.linspace(specs.min_speed, specs.max_speed, 10):
            hours = distance_nm / speed
            fuel = self.calculate_fuel_consumption(specs, speed, distance_nm)
            results.append({
                "speed_kt": round(speed, 1),
                "time_hours": round(hours, 1),
                "fuel_tonnes": round(fuel, 1),
            })
        
        return {"distance_nm": distance_nm, "options": results}
