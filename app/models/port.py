"""
Port Model

Maritime port locations with metadata for routing endpoints.
"""

from sqlalchemy import Float, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Port(Base, UUIDMixin, TimestampMixin):
    """Maritime port with location and operational data."""

    __tablename__ = "ports"

    # LOCODE (UN/LOCODE format, e.g., SGSIN, NLRTM)
    locode: Mapped[str] = mapped_column(
        String(10),
        unique=True,
        nullable=False,
        index=True,
    )

    # Port name
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    # Country code (ISO 3166-1 alpha-2)
    country_code: Mapped[str] = mapped_column(String(2), nullable=False, index=True)

    # Geographic coordinates
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Port characteristics
    max_draft: Mapped[float | None] = mapped_column(Float, nullable=True)  # Max vessel draft (meters)
    max_loa: Mapped[float | None] = mapped_column(Float, nullable=True)  # Max length overall (meters)
    is_major: Mapped[bool] = mapped_column(default=False)  # Major shipping hub

    # Timezone (IANA format)
    timezone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Additional metadata
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Indexes for spatial queries
    __table_args__ = (
        Index("ix_ports_coordinates", "latitude", "longitude"),
    )

    def __repr__(self) -> str:
        return f"<Port {self.locode}: {self.name}>"

    @property
    def coordinates(self) -> tuple[float, float]:
        """Return (lat, lon) tuple."""
        return (self.latitude, self.longitude)
