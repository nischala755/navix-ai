"""
Ship Profile Model

Vessel specifications for propulsion, fuel consumption, and emission modeling.
"""

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ShipProfile(Base, UUIDMixin, TimestampMixin):
    """
    Ship profile with propulsion and emission characteristics.
    
    Contains all vessel-specific parameters needed for fuel consumption,
    speed optimization, and emission calculations.
    """

    __tablename__ = "ship_profiles"

    # Ship identification
    imo_number: Mapped[str | None] = mapped_column(String(20), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    ship_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="container",
    )  # container, tanker, bulk_carrier, general_cargo, etc.

    # Dimensions
    length_overall: Mapped[float] = mapped_column(Float, nullable=False)  # meters
    beam: Mapped[float] = mapped_column(Float, nullable=False)  # meters
    draft_design: Mapped[float] = mapped_column(Float, nullable=False)  # meters
    draft_max: Mapped[float] = mapped_column(Float, nullable=False)  # meters
    deadweight: Mapped[float] = mapped_column(Float, nullable=False)  # tonnes
    gross_tonnage: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Propulsion
    engine_power: Mapped[float] = mapped_column(Float, nullable=False)  # kW (MCR)
    design_speed: Mapped[float] = mapped_column(Float, nullable=False)  # knots
    service_speed: Mapped[float] = mapped_column(Float, nullable=False)  # knots
    min_speed: Mapped[float] = mapped_column(Float, default=8.0)  # knots
    max_speed: Mapped[float] = mapped_column(Float, nullable=False)  # knots

    # Fuel consumption
    fuel_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="VLSFO",
    )  # HFO, VLSFO, LSFO, MGO, LNG
    sfc_design: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        default=180.0,
    )  # g/kWh at design conditions
    fuel_consumption_design: Mapped[float | None] = mapped_column(Float, nullable=True)  # tonnes/day at design speed

    # Hull characteristics (for resistance calculations)
    block_coefficient: Mapped[float] = mapped_column(Float, default=0.65)  # Cb
    wetted_surface_area: Mapped[float | None] = mapped_column(Float, nullable=True)  # m²
    hull_efficiency: Mapped[float] = mapped_column(Float, default=0.98)  # Hull efficiency factor

    # Speed-power curve coefficients (cubic approximation: P = a + b*V + c*V² + d*V³)
    power_coef_a: Mapped[float] = mapped_column(Float, default=0.0)
    power_coef_b: Mapped[float] = mapped_column(Float, default=0.0)
    power_coef_c: Mapped[float] = mapped_column(Float, default=0.0)
    power_coef_d: Mapped[float] = mapped_column(Float, default=1.0)  # Cubic term (admiralty formula)

    # Emission factors (g per kg fuel)
    emission_co2: Mapped[float] = mapped_column(Float, default=3114.0)  # CO2
    emission_sox: Mapped[float] = mapped_column(Float, default=10.5)  # SOx (VLSFO)
    emission_nox: Mapped[float] = mapped_column(Float, default=87.0)  # NOx
    emission_pm: Mapped[float] = mapped_column(Float, default=6.5)  # Particulate Matter

    # Carbon Intensity Indicator (CII)
    cii_rating: Mapped[str | None] = mapped_column(String(1), nullable=True)  # A, B, C, D, E
    cii_required: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Notes
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_ship_profiles_type", "ship_type"),
    )

    def __repr__(self) -> str:
        return f"<ShipProfile {self.name} ({self.ship_type})>"

    def calculate_power(self, speed: float) -> float:
        """
        Calculate required power for given speed using cubic approximation.
        
        Args:
            speed: Speed in knots.
            
        Returns:
            Required power in kW.
        """
        return (
            self.power_coef_a
            + self.power_coef_b * speed
            + self.power_coef_c * speed**2
            + self.power_coef_d * speed**3
        )

    def calculate_fuel_consumption(self, speed: float, hours: float = 24) -> float:
        """
        Calculate fuel consumption for given speed and duration.
        
        Args:
            speed: Speed in knots.
            hours: Duration in hours.
            
        Returns:
            Fuel consumption in tonnes.
        """
        power = self.calculate_power(speed)
        # Scale by SFC and time
        fuel_rate = power * self.sfc_design / 1_000_000  # Convert to tonnes/hour
        return fuel_rate * hours

    def calculate_emissions(self, fuel_tonnes: float) -> dict[str, float]:
        """
        Calculate emissions for given fuel consumption.
        
        Args:
            fuel_tonnes: Fuel consumed in tonnes.
            
        Returns:
            Dictionary of emissions in tonnes.
        """
        fuel_kg = fuel_tonnes * 1000
        return {
            "co2": (fuel_kg * self.emission_co2) / 1_000_000,  # tonnes
            "sox": (fuel_kg * self.emission_sox) / 1_000_000,
            "nox": (fuel_kg * self.emission_nox) / 1_000_000,
            "pm": (fuel_kg * self.emission_pm) / 1_000_000,
        }
