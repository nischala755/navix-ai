"""Map layers endpoint."""

from fastapi import APIRouter, Query
from pydantic import BaseModel

from app.ocean.grid import OceanGrid

router = APIRouter()


class LayerInfo(BaseModel):
    """Map layer information."""
    name: str
    description: str
    type: str


class LayersResponse(BaseModel):
    """Available map layers."""
    layers: list[LayerInfo]


class StormZoneResponse(BaseModel):
    """Storm zone data."""
    name: str
    center_lat: float
    center_lon: float
    radius_nm: float
    risk_level: float
    category: int | None = None


class PiracyZoneResponse(BaseModel):
    """Piracy zone data."""
    name: str
    bounds: dict
    risk_level: float


@router.get("/layers", response_model=LayersResponse)
async def get_available_layers():
    """Get list of available map layers."""
    return LayersResponse(
        layers=[
            LayerInfo(name="wave", description="Significant wave height (meters)", type="grid"),
            LayerInfo(name="current", description="Ocean current magnitude (m/s)", type="grid"),
            LayerInfo(name="depth", description="Bathymetry (meters)", type="grid"),
            LayerInfo(name="storm", description="Active storm zones", type="zones"),
            LayerInfo(name="piracy", description="Piracy risk zones", type="zones"),
            LayerInfo(name="eca", description="Emission Control Areas", type="zones"),
        ]
    )


@router.get("/layer/{layer_name}")
async def get_layer_data(
    layer_name: str,
    min_lat: float = Query(default=-60),
    max_lat: float = Query(default=70),
    min_lon: float = Query(default=-180),
    max_lon: float = Query(default=180),
):
    """
    Get data for a specific map layer.
    
    Returns gridded data or zone polygons depending on layer type.
    """
    ocean = OceanGrid()

    if layer_name in ("wave", "current", "depth"):
        data = ocean.get_layer_data(layer_name)
        return {
            "layer": layer_name,
            "type": "grid",
            "resolution": ocean.resolution,
            "bounds": {
                "min_lat": ocean.lat_min,
                "max_lat": ocean.lat_max,
                "min_lon": ocean.lon_min,
                "max_lon": ocean.lon_max,
            },
            "data": data,
        }

    elif layer_name == "storm":
        # Return active storm zones
        zones = [
            StormZoneResponse(
                name="Tropical Storm Alpha",
                center_lat=15.5,
                center_lon=-60.2,
                radius_nm=150,
                risk_level=0.8,
                category=2,
            ),
            StormZoneResponse(
                name="Typhoon Beta",
                center_lat=22.3,
                center_lon=125.5,
                radius_nm=200,
                risk_level=0.95,
                category=4,
            ),
        ]
        return {"layer": layer_name, "type": "zones", "zones": [z.dict() for z in zones]}

    elif layer_name == "piracy":
        # Return piracy zones
        zones = [
            PiracyZoneResponse(
                name="Gulf of Aden",
                bounds={"min_lat": 10, "max_lat": 15, "min_lon": 43, "max_lon": 54},
                risk_level=0.7,
            ),
            PiracyZoneResponse(
                name="Strait of Malacca",
                bounds={"min_lat": 0, "max_lat": 6, "min_lon": 95, "max_lon": 105},
                risk_level=0.4,
            ),
            PiracyZoneResponse(
                name="Gulf of Guinea",
                bounds={"min_lat": -2, "max_lat": 8, "min_lon": -5, "max_lon": 10},
                risk_level=0.85,
            ),
        ]
        return {"layer": layer_name, "type": "zones", "zones": [z.dict() for z in zones]}

    elif layer_name == "eca":
        # Emission Control Areas
        return {
            "layer": layer_name,
            "type": "zones",
            "zones": [
                {
                    "name": "North Sea ECA",
                    "type": "SOx",
                    "polygon": [
                        [51.0, -5.0], [51.0, 10.0], [62.0, 10.0], [62.0, -5.0], [51.0, -5.0]
                    ],
                },
                {
                    "name": "Baltic Sea ECA",
                    "type": "SOx",
                    "polygon": [
                        [53.0, 10.0], [53.0, 30.0], [66.0, 30.0], [66.0, 10.0], [53.0, 10.0]
                    ],
                },
            ],
        }

    return {"error": f"Unknown layer: {layer_name}"}
