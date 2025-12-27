"""
Ocean Models

Models for ocean grid cells, storm zones, and piracy risk regions.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class OceanCell(Base, UUIDMixin, TimestampMixin):
    """
    Ocean grid cell with environmental data.
    
    Represents a spatial cell in the digital ocean twin with
    time-varying oceanographic and meteorological properties.
    """

    __tablename__ = "ocean_cells"

    # Grid coordinates (cell center)
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Grid indices for fast lookup
    grid_row: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    grid_col: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Timestamp for time-varying data
    valid_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    # Wave data
    significant_wave_height: Mapped[float | None] = mapped_column(Float, nullable=True)  # meters
    mean_wave_period: Mapped[float | None] = mapped_column(Float, nullable=True)  # seconds
    wave_direction: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees from north

    # Current data
    current_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # m/s
    current_direction: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees from north

    # Wind data
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # m/s
    wind_direction: Mapped[float | None] = mapped_column(Float, nullable=True)  # degrees from north

    # Resistance factor (combined environmental resistance)
    resistance_factor: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Bathymetry
    depth: Mapped[float | None] = mapped_column(Float, nullable=True)  # meters (positive down)

    # Land/water flag
    is_land: Mapped[bool] = mapped_column(default=False, nullable=False)

    __table_args__ = (
        Index("ix_ocean_cells_grid", "grid_row", "grid_col", "valid_time"),
        Index("ix_ocean_cells_spatial", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<OceanCell ({self.latitude:.2f}, {self.longitude:.2f}) @ {self.valid_time}>"


class StormZone(Base, UUIDMixin, TimestampMixin):
    """
    Storm/cyclone zone with temporal validity.
    
    Represents hazardous weather areas that should be avoided
    or weighted heavily in route optimization.
    """

    __tablename__ = "storm_zones"

    # Storm identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    storm_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="tropical_cyclone",
    )  # tropical_cyclone, typhoon, hurricane, extratropical

    # Center position
    center_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    center_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Storm extent
    radius_nm: Mapped[float] = mapped_column(Float, nullable=False)  # Nautical miles
    max_wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # knots

    # Saffir-Simpson category (1-5) or equivalent
    category: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Risk level (0.0 - 1.0)
    risk_level: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # Temporal validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    # Forecast track (JSON array of future positions)
    forecast_track: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Active flag
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        Index("ix_storm_zones_temporal", "valid_from", "valid_until"),
        Index("ix_storm_zones_position", "center_latitude", "center_longitude"),
    )

    def __repr__(self) -> str:
        return f"<StormZone {self.name} (Cat {self.category})>"


class PiracyZone(Base, UUIDMixin, TimestampMixin):
    """
    Piracy risk zone.
    
    Represents maritime regions with elevated piracy/armed robbery risk.
    Based on IMB Piracy Reporting Centre data.
    """

    __tablename__ = "piracy_zones"

    # Zone identification
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False)  # e.g., "Gulf of Aden", "Malacca Strait"

    # Bounding box (simplified geometry)
    min_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    max_latitude: Mapped[float] = mapped_column(Float, nullable=False)
    min_longitude: Mapped[float] = mapped_column(Float, nullable=False)
    max_longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Risk assessment
    risk_level: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    incident_count: Mapped[int] = mapped_column(Integer, default=0)  # Recent incidents

    # Temporal validity
    valid_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    valid_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Advisory notes
    advisory: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Active flag
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    __table_args__ = (
        Index("ix_piracy_zones_bounds", "min_latitude", "max_latitude", "min_longitude", "max_longitude"),
    )

    def __repr__(self) -> str:
        return f"<PiracyZone {self.name} (Risk: {self.risk_level:.2f})>"

    def contains_point(self, lat: float, lon: float) -> bool:
        """Check if a point is within this zone."""
        return (
            self.min_latitude <= lat <= self.max_latitude
            and self.min_longitude <= lon <= self.max_longitude
        )
