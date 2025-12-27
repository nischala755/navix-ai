"""
Route Memory Bank

Versioned route storage with similarity detection and warm-start support.
"""

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from numpy.typing import NDArray


@dataclass
class StoredRoute:
    """Stored route with metadata."""
    route_id: str
    origin: tuple[float, float]
    destination: tuple[float, float]
    waypoints: list[list[float]]
    objectives: dict[str, float]
    ship_type: str
    created_at: datetime
    version: int
    performance_score: float


class RouteMemoryBank:
    """
    Route memory for warm-start optimization.
    
    Stores historical routes and provides similar route lookup
    for faster optimization convergence.
    """

    def __init__(self, max_routes: int = 1000):
        self.max_routes = max_routes
        self.routes: dict[str, StoredRoute] = {}
        self.od_index: dict[str, list[str]] = {}  # Origin-destination to route IDs

    def _compute_od_hash(self, origin: tuple[float, float], destination: tuple[float, float]) -> str:
        """Compute hash for origin-destination pair."""
        # Round to 0.1 degree for grouping nearby ports
        o_lat = round(origin[0], 1)
        o_lon = round(origin[1], 1)
        d_lat = round(destination[0], 1)
        d_lon = round(destination[1], 1)
        key = f"{o_lat},{o_lon}|{d_lat},{d_lon}"
        return hashlib.md5(key.encode()).hexdigest()[:16]

    def _compute_route_signature(self, waypoints: list[list[float]]) -> str:
        """Compute route signature for similarity matching."""
        # Sample key waypoints
        n = len(waypoints)
        samples = [0, n // 4, n // 2, 3 * n // 4, n - 1]
        key_points = [waypoints[min(i, n - 1)] for i in samples]
        data = json.dumps([[round(p[0], 2), round(p[1], 2)] for p in key_points])
        return hashlib.md5(data.encode()).hexdigest()[:16]

    def store_route(
        self,
        route_id: str,
        origin: tuple[float, float],
        destination: tuple[float, float],
        waypoints: list[list[float]],
        objectives: dict[str, float],
        ship_type: str = "generic",
        version: int = 1,
    ) -> None:
        """
        Store a route in the memory bank.
        """
        # Calculate performance score (lower is better)
        perf_score = (
            objectives.get("fuel", 0) * 0.3 +
            objectives.get("time", 0) * 0.25 +
            objectives.get("risk", 0) * 100 * 0.2 +
            objectives.get("emissions", 0) * 0.15 +
            (1 - objectives.get("comfort", 1)) * 100 * 0.1
        )

        stored = StoredRoute(
            route_id=route_id,
            origin=origin,
            destination=destination,
            waypoints=waypoints,
            objectives=objectives,
            ship_type=ship_type,
            created_at=datetime.now(),
            version=version,
            performance_score=perf_score,
        )

        self.routes[route_id] = stored

        # Index by OD pair
        od_hash = self._compute_od_hash(origin, destination)
        if od_hash not in self.od_index:
            self.od_index[od_hash] = []
        if route_id not in self.od_index[od_hash]:
            self.od_index[od_hash].append(route_id)

        # Prune if over limit
        if len(self.routes) > self.max_routes:
            self._prune_old_routes()

    def _prune_old_routes(self) -> None:
        """Remove oldest/worst performing routes."""
        if len(self.routes) <= self.max_routes:
            return

        # Sort by performance (keep best) and age (keep recent)
        routes_list = list(self.routes.values())
        routes_list.sort(key=lambda r: (r.performance_score, -r.created_at.timestamp()))

        to_remove = routes_list[self.max_routes:]
        for route in to_remove:
            del self.routes[route.route_id]
            od_hash = self._compute_od_hash(route.origin, route.destination)
            if od_hash in self.od_index:
                self.od_index[od_hash] = [
                    rid for rid in self.od_index[od_hash] if rid != route.route_id
                ]

    def find_similar_routes(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        ship_type: str | None = None,
        top_k: int = 5,
    ) -> list[StoredRoute]:
        """
        Find similar historical routes for warm-start.
        """
        od_hash = self._compute_od_hash(origin, destination)
        route_ids = self.od_index.get(od_hash, [])

        if not route_ids:
            # Try to find nearby OD pairs
            route_ids = self._find_nearby_routes(origin, destination)

        candidates = [self.routes[rid] for rid in route_ids if rid in self.routes]

        # Filter by ship type if specified
        if ship_type:
            candidates = [r for r in candidates if r.ship_type == ship_type or r.ship_type == "generic"]

        # Sort by performance
        candidates.sort(key=lambda r: r.performance_score)

        return candidates[:top_k]

    def _find_nearby_routes(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        search_radius: float = 1.0,
    ) -> list[str]:
        """Find routes with nearby OD pairs."""
        nearby_ids = []

        for route in self.routes.values():
            origin_dist = np.sqrt(
                (route.origin[0] - origin[0])**2 +
                (route.origin[1] - origin[1])**2
            )
            dest_dist = np.sqrt(
                (route.destination[0] - destination[0])**2 +
                (route.destination[1] - destination[1])**2
            )

            if origin_dist < search_radius and dest_dist < search_radius:
                nearby_ids.append(route.route_id)

        return nearby_ids

    def get_warm_start_routes(
        self,
        origin: tuple[float, float],
        destination: tuple[float, float],
        ship_type: str | None = None,
    ) -> list[NDArray[np.float64]]:
        """
        Get routes suitable for warm-start optimization.
        
        Returns list of route waypoint arrays.
        """
        similar = self.find_similar_routes(origin, destination, ship_type)
        return [np.array(r.waypoints) for r in similar]

    def compute_frechet_distance(
        self,
        route_a: list[list[float]],
        route_b: list[list[float]],
    ) -> float:
        """
        Compute Fréchet distance between two routes.
        
        Measures geometric similarity of curves.
        """
        p = np.array(route_a)
        q = np.array(route_b)

        n, m = len(p), len(q)
        ca = np.full((n, m), -1.0)

        def dist(i: int, j: int) -> float:
            return float(np.sqrt(np.sum((p[i] - q[j])**2)))

        def recurse(i: int, j: int) -> float:
            if ca[i, j] > -1:
                return ca[i, j]

            if i == 0 and j == 0:
                ca[i, j] = dist(0, 0)
            elif i > 0 and j == 0:
                ca[i, j] = max(recurse(i - 1, 0), dist(i, 0))
            elif i == 0 and j > 0:
                ca[i, j] = max(recurse(0, j - 1), dist(0, j))
            else:
                ca[i, j] = max(
                    min(recurse(i - 1, j), recurse(i - 1, j - 1), recurse(i, j - 1)),
                    dist(i, j),
                )

            return ca[i, j]

        return recurse(n - 1, m - 1)

    def get_statistics(self) -> dict:
        """Get memory bank statistics."""
        if not self.routes:
            return {"total_routes": 0, "od_pairs": 0}

        performances = [r.performance_score for r in self.routes.values()]
        return {
            "total_routes": len(self.routes),
            "od_pairs": len(self.od_index),
            "avg_performance": np.mean(performances),
            "best_performance": np.min(performances),
            "worst_performance": np.max(performances),
        }
