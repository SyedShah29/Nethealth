import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_public_health_to_protected_platform_health_end_to_end(
    client: AsyncClient,
) -> None:
    health = await client.get("/api/health")
    assert health.status_code == 200
    assert health.json()["status"] == "healthy"

    protected = await client.get("/api/system/platform-health")
    assert protected.status_code == 401
    assert protected.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
    assert protected.json()["error"]["message"] == "Authentication is required."
    assert protected.json()["error"]["request_id"]
