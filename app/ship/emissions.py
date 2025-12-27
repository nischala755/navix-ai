"""
Emission Calculator

Carbon and pollution emission modeling for maritime vessels.
"""

from dataclasses import dataclass
from enum import Enum


class FuelType(str, Enum):
    """Maritime fuel types."""
    HFO = "HFO"  # Heavy Fuel Oil
    VLSFO = "VLSFO"  # Very Low Sulfur Fuel Oil
    LSFO = "LSFO"  # Low Sulfur Fuel Oil  
    MGO = "MGO"  # Marine Gas Oil
    LNG = "LNG"  # Liquefied Natural Gas
    METHANOL = "METHANOL"
    AMMONIA = "AMMONIA"


@dataclass
class EmissionFactors:
    """Emission factors in g per kg fuel."""
    co2: float
    sox: float
    nox: float
    pm: float  # Particulate Matter
    ch4: float = 0.0  # Methane (for LNG)


class EmissionCalculator:
    """
    Calculate vessel emissions based on fuel consumption.
    
    Follows IMO guidelines for emission estimation.
    """

    # Emission factors by fuel type (g/kg fuel)
    EMISSION_FACTORS = {
        FuelType.HFO: EmissionFactors(co2=3114, sox=54.0, nox=87.0, pm=7.6),
        FuelType.VLSFO: EmissionFactors(co2=3114, sox=10.5, nox=87.0, pm=6.5),
        FuelType.LSFO: EmissionFactors(co2=3114, sox=20.0, nox=87.0, pm=6.8),
        FuelType.MGO: EmissionFactors(co2=3206, sox=2.0, nox=78.0, pm=1.5),
        FuelType.LNG: EmissionFactors(co2=2750, sox=0.0, nox=15.0, pm=0.1, ch4=50.0),
        FuelType.METHANOL: EmissionFactors(co2=1375, sox=0.0, nox=30.0, pm=0.5),
        FuelType.AMMONIA: EmissionFactors(co2=0, sox=0.0, nox=20.0, pm=0.0),
    }

    # Global Warming Potential (100-year)
    GWP = {"co2": 1, "ch4": 28, "n2o": 265}

    def __init__(self, fuel_type: FuelType = FuelType.VLSFO):
        self.fuel_type = fuel_type
        self.factors = self.EMISSION_FACTORS[fuel_type]

    def calculate(self, fuel_tonnes: float) -> dict[str, float]:
        """
        Calculate emissions for fuel consumption.
        
        Args:
            fuel_tonnes: Fuel consumed in tonnes.
            
        Returns:
            Dict of emissions in tonnes.
        """
        fuel_kg = fuel_tonnes * 1000
        
        return {
            "co2_tonnes": self.factors.co2 * fuel_kg / 1_000_000,
            "sox_kg": self.factors.sox * fuel_kg / 1000,
            "nox_kg": self.factors.nox * fuel_kg / 1000,
            "pm_kg": self.factors.pm * fuel_kg / 1000,
            "ch4_kg": self.factors.ch4 * fuel_kg / 1000,
        }

    def calculate_co2e(self, fuel_tonnes: float) -> float:
        """
        Calculate CO2 equivalent emissions (tonnes).
        
        Includes methane GWP for LNG.
        """
        emissions = self.calculate(fuel_tonnes)
        co2e = emissions["co2_tonnes"]
        co2e += emissions["ch4_kg"] / 1000 * self.GWP["ch4"]
        return co2e

    def calculate_eeoi(
        self,
        fuel_tonnes: float,
        distance_nm: float,
        cargo_tonnes: float,
    ) -> float:
        """
        Calculate Energy Efficiency Operational Indicator.
        
        EEOI = CO2 / (cargo × distance)
        
        Returns gCO2/tonne-nm.
        """
        if distance_nm <= 0 or cargo_tonnes <= 0:
            return 0.0
        
        co2_grams = self.factors.co2 * fuel_tonnes * 1000
        return co2_grams / (cargo_tonnes * distance_nm)

    def calculate_cii(
        self,
        annual_fuel_tonnes: float,
        annual_distance_nm: float,
        dwt: float,
    ) -> tuple[float, str]:
        """
        Calculate Carbon Intensity Indicator and rating.
        
        CII = Annual CO2 / (DWT × Distance)
        
        Returns (CII value, rating A-E).
        """
        if annual_distance_nm <= 0 or dwt <= 0:
            return 0.0, "E"
        
        co2_grams = self.factors.co2 * annual_fuel_tonnes * 1000
        cii = co2_grams / (dwt * annual_distance_nm)

        # Simplified rating thresholds
        if cii < 3.0:
            rating = "A"
        elif cii < 4.0:
            rating = "B"
        elif cii < 5.0:
            rating = "C"
        elif cii < 6.0:
            rating = "D"
        else:
            rating = "E"

        return cii, rating

    @staticmethod
    def carbon_cost(co2_tonnes: float, price_per_tonne: float = 50.0) -> float:
        """
        Calculate carbon cost (EU ETS style).
        
        Args:
            co2_tonnes: CO2 emissions in tonnes.
            price_per_tonne: Carbon price in USD/EUR.
            
        Returns:
            Carbon cost.
        """
        return co2_tonnes * price_per_tonne
