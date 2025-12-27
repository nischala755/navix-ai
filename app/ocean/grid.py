"""
Digital Ocean Grid

Spatial grid for ocean environment data with time-varying layers.
"""

from datetime import datetime
import numpy as np
from numpy.typing import NDArray
from typing import List, Optional


class OceanGrid:
    """
    Digital twin of ocean environment.
    
    Provides spatial queries for wave, current, storm, and piracy data
    with bilinear interpolation and time-indexing.
    """

    def __init__(
        self,
        resolution: float = 0.5,
        lat_range: tuple[float, float] = (-60, 70),
        lon_range: tuple[float, float] = (-180, 180),
    ):
        self.resolution = resolution
        self.lat_min, self.lat_max = lat_range
        self.lon_min, self.lon_max = lon_range
        
        self.n_lat = int((self.lat_max - self.lat_min) / resolution)
        self.n_lon = int((self.lon_max - self.lon_min) / resolution)
        
        # Initialize data layers
        self._land_mask: NDArray[np.bool_] | None = None
        self._depth: NDArray[np.float64] | None = None
        self._wave_height: NDArray[np.float64] | None = None
        self._current_u: NDArray[np.float64] | None = None
        self._current_v: NDArray[np.float64] | None = None
        
        # Zone data
        self._storm_zones: list[dict] = []
        self._piracy_zones: list[dict] = []
        
        self._initialize_default_data()

    def _initialize_default_data(self) -> None:
        """Initialize with synthetic ocean data."""
        np.random.seed(42)
        
        # Simple land mask (continents approximation)
        self._land_mask = np.zeros((self.n_lat, self.n_lon), dtype=bool)
        
        # Mark rough continental areas
        lat_idx = np.arange(self.n_lat)
        lon_idx = np.arange(self.n_lon)
        lats = self.lat_min + lat_idx * self.resolution
        lons = self.lon_min + lon_idx * self.resolution
        
        for i, lat in enumerate(lats):
            for j, lon in enumerate(lons):
                if self._is_approximate_land(lat, lon):
                    self._land_mask[i, j] = True
        
        # Depth (random but deeper away from coasts)
        self._depth = np.random.uniform(100, 5000, (self.n_lat, self.n_lon))
        self._depth[self._land_mask] = 0
        
        # Wave height (random 0-8m)
        self._wave_height = np.random.uniform(0.5, 4, (self.n_lat, self.n_lon))
        self._wave_height[self._land_mask] = 0
        
        # Currents (random vectors)
        self._current_u = np.random.uniform(-0.5, 0.5, (self.n_lat, self.n_lon))
        self._current_v = np.random.uniform(-0.5, 0.5, (self.n_lat, self.n_lon))
        self._current_u[self._land_mask] = 0
        self._current_v[self._land_mask] = 0

    def _is_approximate_land(self, lat: float, lon: float) -> bool:
        """Rough continental approximation."""
        # North America
        if 25 < lat < 70 and -130 < lon < -60:
            if lat < 50 and lon > -100:
                return True
        # South America
        if -55 < lat < 10 and -80 < lon < -35:
            return True
        # Europe
        if 35 < lat < 70 and -10 < lon < 40:
            return True
        # Africa
        if -35 < lat < 35 and -20 < lon < 50:
            return True
        # Asia
        if 10 < lat < 70 and 40 < lon < 150:
            return True
        # Australia
        if -45 < lat < -10 and 110 < lon < 155:
            return True
        return False

    def _get_grid_indices(self, lat: float, lon: float) -> tuple[int, int]:
        """Convert lat/lon to grid indices."""
        i = int((lat - self.lat_min) / self.resolution)
        j = int((lon - self.lon_min) / self.resolution)
        i = max(0, min(i, self.n_lat - 1))
        j = max(0, min(j, self.n_lon - 1))
        return i, j

    def is_land(self, lat: float, lon: float) -> bool:
        """Check if position is on land."""
        i, j = self._get_grid_indices(lat, lon)
        return bool(self._land_mask[i, j])

    def get_depth(self, lat: float, lon: float) -> float:
        """Get water depth at position (meters)."""
        i, j = self._get_grid_indices(lat, lon)
        return float(self._depth[i, j])

    def get_wave_height(self, lat: float, lon: float, time: float | None = None) -> float:
        """Get significant wave height (meters)."""
        i, j = self._get_grid_indices(lat, lon)
        base = float(self._wave_height[i, j])
        # Add time variation
        if time:
            variation = np.sin(time / 86400 * 2 * np.pi) * 0.5
            return max(0, base + variation)
        return base

    def get_current_vector(self, lat: float, lon: float, time: float | None = None) -> tuple[float, float]:
        """Get ocean current (u, v) in m/s."""
        i, j = self._get_grid_indices(lat, lon)
        return float(self._current_u[i, j]), float(self._current_v[i, j])

    def get_resistance(self, lat: float, lon: float, time: float | None = None) -> float:
        """Get combined resistance factor (1.0 = normal)."""
        wave = self.get_wave_height(lat, lon, time)
        # Resistance increases with wave height
        return 1.0 + 0.1 * wave

    def get_storm_risk(self, lat: float, lon: float, time: float | None = None) -> float:
        """Get storm risk at position (0-1)."""
        for zone in self._storm_zones:
            dist = np.sqrt((lat - zone["lat"])**2 + (lon - zone["lon"])**2)
            if dist < zone["radius"]:
                if time and zone.get("valid_until"):
                    if time > zone["valid_until"]:
                        continue
                return zone["risk"] * (1 - dist / zone["radius"])
        return 0.0

    def get_piracy_risk(self, lat: float, lon: float) -> float:
        """Get piracy risk at position (0-1)."""
        for zone in self._piracy_zones:
            if (zone["min_lat"] <= lat <= zone["max_lat"] and
                zone["min_lon"] <= lon <= zone["max_lon"]):
                return zone["risk"]
        return 0.0

    def add_storm_zone(
        self,
        lat: float,
        lon: float,
        radius: float,
        risk: float,
        valid_until: float | None = None,
    ) -> None:
        """Add a storm zone."""
        self._storm_zones.append({
            "lat": lat, "lon": lon, "radius": radius,
            "risk": risk, "valid_until": valid_until
        })

    def add_piracy_zone(
        self,
        min_lat: float,
        max_lat: float,
        min_lon: float,
        max_lon: float,
        risk: float,
    ) -> None:
        """Add a piracy zone."""
        self._piracy_zones.append({
            "min_lat": min_lat, "max_lat": max_lat,
            "min_lon": min_lon, "max_lon": max_lon, "risk": risk
        })

    def get_layer_data(self, layer: str) -> dict:
        """Get layer data for visualization."""
        if layer == "wave":
            return {"data": self._wave_height.tolist(), "min": 0, "max": 8}
        elif layer == "current":
            magnitude = np.sqrt(self._current_u**2 + self._current_v**2)
            return {"data": magnitude.tolist(), "min": 0, "max": 1}
        elif layer == "depth":
            return {"data": self._depth.tolist(), "min": 0, "max": 5000}
        return {}
