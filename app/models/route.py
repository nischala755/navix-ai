"""
Route Solution Models

Models for storing computed routes, waypoints, Pareto archive, and explainability logs.
"""

from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class RouteSolution(Base, UUIDMixin, TimestampMixin):
    """
    Computed route solution from optimization.
    
    Represents a single Pareto-optimal route with objective values
    and summary statistics.
    """

    __tablename__ = "route_solutions"

    # Parent job
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("optimization_jobs.id"),
        nullable=False,
        index=True,
    )

    # Solution ranking (within Pareto front)
    rank: Mapped[int] = mapped_column(Integer, default=0)
    crowding_distance: Mapped[float] = mapped_column(Float, default=0.0)

    # Objective values
    fuel_consumption: Mapped[float] = mapped_column(Float, nullable=False)  # tonnes
    travel_time: Mapped[float] = mapped_column(Float, nullable=False)  # hours
    risk_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0
    co2_emissions: Mapped[float] = mapped_column(Float, nullable=False)  # tonnes
    comfort_score: Mapped[float] = mapped_column(Float, nullable=False)  # 0.0 - 1.0 (higher = better)

    # Route summary
    total_distance_nm: Mapped[float] = mapped_column(Float, nullable=False)  # nautical miles
    waypoint_count: Mapped[int] = mapped_column(Integer, default=0)
    average_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # knots

    # Speed profile (JSON array of speeds per leg)
    speed_profile: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Computed route (serialized waypoints as JSON for quick access)
    route_geojson: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Comparison to baseline (fastest great circle route)
    fuel_savings_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    time_penalty_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    emissions_savings_pct: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Version for route memory bank
    version: Mapped[int] = mapped_column(Integer, default=1)

    # Relationships
    job = relationship("OptimizationJob", back_populates="solutions")
    waypoints = relationship(
        "RouteWaypoint",
        back_populates="route",
        cascade="all, delete-orphan",
        order_by="RouteWaypoint.sequence",
    )
    explainability_logs = relationship(
        "ExplainabilityLog",
        back_populates="route",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        Index("ix_route_solutions_objectives", "fuel_consumption", "travel_time", "risk_score"),
    )

    def __repr__(self) -> str:
        return f"<RouteSolution {self.id[:8]} (Fuel: {self.fuel_consumption:.1f}t, Time: {self.travel_time:.1f}h)>"


class RouteWaypoint(Base, UUIDMixin):
    """
    Individual waypoint in a route solution.
    
    Ordered sequence of coordinates defining the ship's path.
    """

    __tablename__ = "route_waypoints"

    # Parent route
    route_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("route_solutions.id"),
        nullable=False,
        index=True,
    )

    # Sequence number (0 = origin, N = destination)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)

    # Geographic position
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    # Timestamp (ETA at this waypoint)
    eta: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Leg to next waypoint
    leg_distance_nm: Mapped[float | None] = mapped_column(Float, nullable=True)
    leg_speed: Mapped[float | None] = mapped_column(Float, nullable=True)  # knots
    leg_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)  # tonnes
    leg_duration_hours: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Environmental conditions at waypoint
    wave_height: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_speed: Mapped[float | None] = mapped_column(Float, nullable=True)
    current_direction: Mapped[float | None] = mapped_column(Float, nullable=True)
    wind_speed: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Relationship
    route = relationship("RouteSolution", back_populates="waypoints")

    __table_args__ = (
        Index("ix_route_waypoints_sequence", "route_id", "sequence"),
    )

    def __repr__(self) -> str:
        return f"<RouteWaypoint {self.sequence}: ({self.latitude:.4f}, {self.longitude:.4f})>"


class ParetoArchive(Base, UUIDMixin, TimestampMixin):
    """
    Historical Pareto archive for route memory bank.
    
    Stores aggregated Pareto fronts across multiple optimization runs
    for similar origin-destination pairs.
    """

    __tablename__ = "pareto_archive"

    # Origin-destination pair hash (for quick lookup)
    od_pair_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    # Origin and destination LOCODEs
    origin_locode: Mapped[str] = mapped_column(String(10), nullable=False)
    destination_locode: Mapped[str] = mapped_column(String(10), nullable=False)

    # Reference to best solution for this pair
    best_route_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("route_solutions.id"),
        nullable=True,
    )

    # Aggregated statistics
    optimization_count: Mapped[int] = mapped_column(Integer, default=1)
    avg_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)
    avg_time: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)
    min_time: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Serialized Pareto front (JSON array of route IDs)
    pareto_front_ids: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Similarity signature for warm-start matching
    route_signature: Mapped[str | None] = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_pareto_archive_od", "origin_locode", "destination_locode"),
    )

    def __repr__(self) -> str:
        return f"<ParetoArchive {self.origin_locode} -> {self.destination_locode}>"


class ExplainabilityLog(Base, UUIDMixin, TimestampMixin):
    """
    Explainability log for route decisions.
    
    Records why specific routing decisions were made,
    supporting the "Why this route?" API.
    """

    __tablename__ = "explainability_logs"

    # Parent route
    route_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("route_solutions.id"),
        nullable=False,
        index=True,
    )

    # Decision type
    decision_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # deviation, speed_change, route_choice, constraint_avoidance

    # Decision details
    description: Mapped[str] = mapped_column(Text, nullable=False)

    # Affected waypoint (if applicable)
    waypoint_sequence: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Quantified impact
    impact_fuel: Mapped[float | None] = mapped_column(Float, nullable=True)  # tonnes
    impact_time: Mapped[float | None] = mapped_column(Float, nullable=True)  # hours
    impact_risk: Mapped[float | None] = mapped_column(Float, nullable=True)  # delta
    impact_emissions: Mapped[float | None] = mapped_column(Float, nullable=True)  # tonnes CO2

    # Trade-off explanation
    trade_off: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Confidence level (0.0 - 1.0)
    confidence: Mapped[float] = mapped_column(Float, default=1.0)

    # Relationship
    route = relationship("RouteSolution", back_populates="explainability_logs")

    def __repr__(self) -> str:
        return f"<ExplainabilityLog {self.decision_type}: {self.description[:50]}>"
