import httpx
import pytest

from apps.api.main import app


@pytest.mark.asyncio
async def test_healthcheck_routes_return_ok() -> None:
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        healthz_response = await client.get("/healthz")
        health_response = await client.get("/health")

    assert healthz_response.status_code == 200
    assert health_response.status_code == 200
    assert healthz_response.json()["status"] == "ok"
    assert health_response.json() == healthz_response.json()
