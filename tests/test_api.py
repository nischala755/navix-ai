"""Tests for API endpoints."""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.fixture
async def client():
    """Create async test client."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_check(client):
    """Test health endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data


@pytest.mark.asyncio
async def test_root_redirect(client):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "docs" in data


@pytest.mark.asyncio
async def test_get_map_layers(client):
    """Test map layers endpoint."""
    response = await client.get("/map/layers")
    assert response.status_code == 200
    data = response.json()
    assert "layers" in data
    assert len(data["layers"]) > 0


@pytest.mark.asyncio
async def test_get_storm_layer(client):
    """Test storm layer data endpoint."""
    response = await client.get("/map/layer/storm")
    assert response.status_code == 200
    data = response.json()
    assert data["layer"] == "storm"
    assert data["type"] == "zones"


@pytest.mark.asyncio
async def test_get_piracy_layer(client):
    """Test piracy layer data endpoint."""
    response = await client.get("/map/layer/piracy")
    assert response.status_code == 200
    data = response.json()
    assert data["layer"] == "piracy"
    assert "zones" in data


@pytest.mark.asyncio
async def test_benchmark_endpoint(client):
    """Test benchmark comparison endpoint."""
    response = await client.get("/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert "hacopso" in data
    assert "ga" in data
    assert "winner" in data


@pytest.mark.asyncio
async def test_optimize_missing_port(client):
    """Test optimization with non-existent port."""
    payload = {
        "origin_locode": "XXXXX",
        "destination_locode": "YYYYY",
        "ship_id": "container_large",
    }
    response = await client.post("/optimize", json=payload)
    # Should return 404 for missing port
    assert response.status_code in (404, 422)


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    """Test getting non-existent job."""
    response = await client.get("/jobs/nonexistent-job-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_routes_not_found(client):
    """Test getting routes for non-existent job."""
    response = await client.get("/routes/nonexistent-job-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_explain_not_found(client):
    """Test explaining non-existent route."""
    response = await client.get("/explain/nonexistent-route-id")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_openapi_docs(client):
    """Test OpenAPI docs are generated."""
    response = await client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "openapi" in data
    assert "paths" in data
    assert "/optimize" in data["paths"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
