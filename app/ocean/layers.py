"""
Environment Layers

Individual data layers for the ocean grid system.
"""

from abc import ABC, abstractmethod
from datetime import datetime
import numpy as np
from numpy.typing import NDArray


class EnvironmentLayer(ABC):
    """Base class for environment data layers."""

    def __init__(self, name: str, unit: str):
        self.name = name
        self.unit = unit
        self._data: NDArray[np.float64] | None = None

    @abstractmethod
    def get_value(self, lat: float, lon: float, time: float | None = None) -> float:
        """Get value at position."""
        pass

    def interpolate(self, lat: float, lon: float, data: NDArray[np.float64], resolution: float, lat_min: float, lon_min: float) -> float:
        """Bilinear interpolation."""
        i = (lat - lat_min) / resolution
        j = (lon - lon_min) / resolution
        
        i0, j0 = int(i), int(j)
        i1, j1 = min(i0 + 1, data.shape[0] - 1), min(j0 + 1, data.shape[1] - 1)
        
        di, dj = i - i0, j - j0
        
        v00 = data[i0, j0]
        v01 = data[i0, j1]
        v10 = data[i1, j0]
        v11 = data[i1, j1]
        
        return float(v00 * (1 - di) * (1 - dj) + v01 * (1 - di) * dj + v10 * di * (1 - dj) + v11 * di * dj)


class WaveLayer(EnvironmentLayer):
    """Significant wave height layer."""

    def __init__(self):
        super().__init__("wave_height", "m")

    def get_value(self, lat: float, lon: float, time: float | None = None) -> float:
        if self._data is None:
            return 1.5  # Default
        # Would use interpolation with actual data
        return 1.5


class CurrentLayer(EnvironmentLayer):
    """Ocean current layer (u, v components)."""

    def __init__(self):
        super().__init__("current", "m/s")
        self._data_u: NDArray[np.float64] | None = None
        self._data_v: NDArray[np.float64] | None = None

    def get_value(self, lat: float, lon: float, time: float | None = None) -> float:
        """Get current magnitude."""
        if self._data_u is None or self._data_v is None:
            return 0.2
        return 0.2

    def get_vector(self, lat: float, lon: float, time: float | None = None) -> tuple[float, float]:
        """Get current vector (u, v)."""
        return 0.1, 0.1


class StormLayer(EnvironmentLayer):
    """Storm/cyclone risk layer."""

    def __init__(self):
        super().__init__("storm_risk", "")
        self._zones: list[dict] = []

    def add_zone(self, center_lat: float, center_lon: float, radius_deg: float, risk: float, valid_until: datetime | None = None) -> None:
        self._zones.append({
            "lat": center_lat, "lon": center_lon, "radius": radius_deg,
            "risk": risk, "valid_until": valid_until.timestamp() if valid_until else None
        })

    def get_value(self, lat: float, lon: float, time: float | None = None) -> float:
        max_risk = 0.0
        for zone in self._zones:
            if time and zone["valid_until"] and time > zone["valid_until"]:
                continue
            dist = np.sqrt((lat - zone["lat"])**2 + (lon - zone["lon"])**2)
            if dist < zone["radius"]:
                risk = zone["risk"] * (1 - dist / zone["radius"])
                max_risk = max(max_risk, risk)
        return max_risk


class PiracyLayer(EnvironmentLayer):
    """Piracy risk layer."""

    def __init__(self):
        super().__init__("piracy_risk", "")
        self._zones: list[dict] = []

    def add_zone(self, min_lat: float, max_lat: float, min_lon: float, max_lon: float, risk: float) -> None:
        self._zones.append({
            "min_lat": min_lat, "max_lat": max_lat,
            "min_lon": min_lon, "max_lon": max_lon, "risk": risk
        })

    def get_value(self, lat: float, lon: float, time: float | None = None) -> float:
        for zone in self._zones:
            if (zone["min_lat"] <= lat <= zone["max_lat"] and
                zone["min_lon"] <= lon <= zone["max_lon"]):
                return zone["risk"]
        return 0.0
