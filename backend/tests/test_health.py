from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Jawhar" in data["name"]
    assert "docs_url" in data
    # Check headers added by middleware
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers


@pytest.mark.asyncio
async def test_full_health_endpoint(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["database"]["status"] == "up"
    assert data["database"]["latency_ms"] is not None
    assert "version" in data
    assert "uptime_seconds" in data
    assert "python_version" in data


@pytest.mark.asyncio
async def test_readiness_probe(client: AsyncClient):
    response = await client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_liveness_probe(client: AsyncClient):
    response = await client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"
