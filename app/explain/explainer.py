"""
Route Explainer

Explainable AI layer for maritime route decisions.
Provides trade-off decomposition and sensitivity analysis.
"""

from dataclasses import dataclass
from datetime import datetime
import numpy as np
from numpy.typing import NDArray


@dataclass
class RouteDecision:
    """Individual route decision explanation."""
    decision_type: str
    description: str
    waypoint_index: int | None
    impact: dict[str, float]
    confidence: float
    trade_off: str


@dataclass
class RouteExplanation:
    """Complete route explanation."""
    route_id: str
    summary: str
    decisions: list[RouteDecision]
    trade_offs: dict[str, str]
    sensitivity: dict[str, float]
    alternatives_considered: int


class RouteExplainer:
    """
    Explainable AI for maritime routing decisions.
    
    Provides human-readable explanations for:
    - Why specific waypoints were chosen
    - Trade-offs between objectives
    - Sensitivity to parameter changes
    """

    def __init__(self):
        self.decision_templates = {
            "storm_avoidance": "Deviated {distance}nm {direction} to avoid {storm_name} (Category {category})",
            "piracy_avoidance": "Routed around {zone_name} piracy zone, adding {time}h to travel time",
            "fuel_optimization": "Reduced speed to {speed}kt in favorable current zone, saving {fuel}t fuel",
            "current_riding": "Aligned route with {current_name} current, gaining {speed_boost}kt effective speed",
            "weather_routing": "Adjusted course to minimize wave exposure, improving comfort by {comfort_pct}%",
            "eca_compliance": "Switched to low-sulfur fuel zone routing, emission impact: {sox_reduction}%",
        }

    def explain_route(
        self,
        route: NDArray[np.float64],
        objectives: dict[str, float],
        baseline_objectives: dict[str, float] | None = None,
        storm_zones: list[dict] | None = None,
        piracy_zones: list[dict] | None = None,
    ) -> RouteExplanation:
        """
        Generate comprehensive route explanation.
        """
        decisions: list[RouteDecision] = []
        trade_offs: dict[str, str] = {}

        # Calculate baseline comparison
        if baseline_objectives:
            fuel_diff = objectives["fuel"] - baseline_objectives["fuel"]
            time_diff = objectives["time"] - baseline_objectives["time"]
            
            if fuel_diff < 0:
                trade_offs["fuel_vs_time"] = f"Saved {abs(fuel_diff):.1f}t fuel at cost of {time_diff:.1f}h extra travel time"
            
            if objectives.get("risk", 0) < baseline_objectives.get("risk", 0):
                risk_reduction = (1 - objectives["risk"] / max(baseline_objectives["risk"], 0.01)) * 100
                trade_offs["safety"] = f"Reduced combined risk by {risk_reduction:.0f}%"

        # Analyze route decisions
        decisions.extend(self._analyze_deviations(route, storm_zones or [], piracy_zones or []))
        decisions.extend(self._analyze_speed_changes(route, objectives))

        # Generate summary
        summary = self._generate_summary(objectives, baseline_objectives, len(decisions))

        # Sensitivity analysis
        sensitivity = self._compute_sensitivity(objectives)

        return RouteExplanation(
            route_id="",
            summary=summary,
            decisions=decisions,
            trade_offs=trade_offs,
            sensitivity=sensitivity,
            alternatives_considered=0,
        )

    def _analyze_deviations(
        self,
        route: NDArray[np.float64],
        storm_zones: list[dict],
        piracy_zones: list[dict],
    ) -> list[RouteDecision]:
        """Analyze route deviations from direct path."""
        decisions = []

        # Calculate great circle path
        origin = route[0]
        destination = route[-1]
        gc_path = np.array([origin + t * (destination - origin) for t in np.linspace(0, 1, len(route))])

        # Find significant deviations
        for i, waypoint in enumerate(route[1:-1], 1):
            deviation = np.sqrt(np.sum((waypoint - gc_path[i])**2))

            if deviation > 1.0:  # More than 1 degree deviation
                # Check if near a storm zone
                for storm in storm_zones:
                    storm_dist = np.sqrt((waypoint[0] - storm["lat"])**2 + (waypoint[1] - storm["lon"])**2)
                    if storm_dist < storm.get("radius", 5) + 2:
                        decisions.append(RouteDecision(
                            decision_type="storm_avoidance",
                            description=f"Deviated {deviation * 60:.0f}nm to avoid storm zone",
                            waypoint_index=i,
                            impact={"time": deviation * 2, "risk": -0.3},
                            confidence=0.9,
                            trade_off="Added travel time to reduce storm encounter risk",
                        ))
                        break

                # Check if near a piracy zone
                for zone in piracy_zones:
                    if (zone["min_lat"] - 2 <= waypoint[0] <= zone["max_lat"] + 2 and
                        zone["min_lon"] - 2 <= waypoint[1] <= zone["max_lon"] + 2):
                        decisions.append(RouteDecision(
                            decision_type="piracy_avoidance",
                            description=f"Routed around piracy zone: {zone.get('name', 'Unknown')}",
                            waypoint_index=i,
                            impact={"time": deviation * 3, "risk": -0.4},
                            confidence=0.85,
                            trade_off="Extended route to avoid high-risk piracy area",
                        ))
                        break

        return decisions

    def _analyze_speed_changes(
        self,
        route: NDArray[np.float64],
        objectives: dict[str, float],
    ) -> list[RouteDecision]:
        """Analyze speed optimization decisions."""
        decisions = []

        # Fuel efficiency decision
        if objectives.get("fuel", 0) < objectives.get("time", 0) * 5:  # Good fuel efficiency
            decisions.append(RouteDecision(
                decision_type="fuel_optimization",
                description="Adopted slow steaming strategy for fuel efficiency",
                waypoint_index=None,
                impact={"fuel": -objectives["fuel"] * 0.15, "time": objectives["time"] * 0.1},
                confidence=0.8,
                trade_off="Reduced speed for significant fuel savings",
            ))

        return decisions

    def _generate_summary(
        self,
        objectives: dict[str, float],
        baseline: dict[str, float] | None,
        decision_count: int,
    ) -> str:
        """Generate human-readable summary."""
        parts = []

        parts.append(f"Optimized route with {decision_count} key routing decisions.")

        if baseline:
            fuel_savings = baseline.get("fuel", 0) - objectives.get("fuel", 0)
            if fuel_savings > 0:
                parts.append(f"Saves {fuel_savings:.1f} tonnes of fuel ({fuel_savings / max(baseline['fuel'], 1) * 100:.1f}%).")

            emission_savings = baseline.get("emissions", 0) - objectives.get("emissions", 0)
            if emission_savings > 0:
                parts.append(f"Reduces CO2 emissions by {emission_savings:.1f} tonnes.")

        comfort = objectives.get("comfort", 0)
        if comfort > 0.7:
            parts.append("Route provides good passenger/cargo comfort.")
        elif comfort < 0.4:
            parts.append("Route may experience rough conditions in some segments.")

        return " ".join(parts)

    def _compute_sensitivity(self, objectives: dict[str, float]) -> dict[str, float]:
        """Compute sensitivity to objective weights."""
        baseline_score = sum(objectives.values())

        return {
            "fuel_weight": objectives.get("fuel", 0) / max(baseline_score, 1),
            "time_weight": objectives.get("time", 0) / max(baseline_score, 1),
            "risk_sensitivity": 1 - objectives.get("risk", 0),
            "comfort_importance": objectives.get("comfort", 0),
        }

    def explain_trade_off(
        self,
        route_a_objectives: dict[str, float],
        route_b_objectives: dict[str, float],
    ) -> str:
        """Explain trade-off between two routes."""
        comparisons = []

        for key in ["fuel", "time", "risk", "emissions", "comfort"]:
            a_val = route_a_objectives.get(key, 0)
            b_val = route_b_objectives.get(key, 0)
            diff = b_val - a_val
            pct = abs(diff / max(a_val, 0.01)) * 100

            if abs(diff) > 0.01:
                better = "Route A" if (diff > 0 and key != "comfort") or (diff < 0 and key == "comfort") else "Route B"
                comparisons.append(f"{key.capitalize()}: {better} is {pct:.1f}% better")

        return "; ".join(comparisons) if comparisons else "Routes are equivalent"

    def why_this_route(
        self,
        route: NDArray[np.float64],
        objectives: dict[str, float],
        weights: dict[str, float],
    ) -> dict:
        """
        Answer "Why this route?" query.
        
        Returns structured explanation suitable for API response.
        """
        explanation = self.explain_route(route, objectives)

        # Rank objectives by weight
        sorted_objectives = sorted(weights.items(), key=lambda x: -x[1])
        primary_objective = sorted_objectives[0][0] if sorted_objectives else "fuel"

        return {
            "summary": explanation.summary,
            "primary_optimization": f"Route optimized primarily for {primary_objective}",
            "key_decisions": [
                {
                    "type": d.decision_type,
                    "description": d.description,
                    "impact": d.impact,
                    "trade_off": d.trade_off,
                }
                for d in explanation.decisions
            ],
            "trade_offs": explanation.trade_offs,
            "sensitivity": explanation.sensitivity,
            "confidence": np.mean([d.confidence for d in explanation.decisions]) if explanation.decisions else 0.8,
        }
