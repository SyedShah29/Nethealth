import pytest
from httpx import AsyncClient


@pytest.mark.parametrize(
    ("method", "path"),
    [
        ("GET", "/api/topology"),
        ("POST", "/api/topology/common-infrastructure"),
        ("GET", "/api/rules"),
        ("GET", "/api/rules/evaluations"),
        ("GET", "/api/correlations"),
        ("POST", "/api/correlations/evaluate"),
        ("GET", "/api/root-causes"),
        ("POST", "/api/root-causes/classify"),
        ("GET", "/api/subscriber-health/SUB-1"),
        ("GET", "/api/subscribers/SUB-1/diagnostics"),
        ("GET", "/api/anomalies"),
        ("GET", "/api/incidents"),
        ("GET", "/api/notification-channels"),
        ("GET", "/api/dashboard"),
        ("GET", "/api/capacity/assessments"),
        ("GET", "/api/capacity/trends"),
    ],
)
async def test_phase_7_to_10_endpoints_require_authentication(
    client: AsyncClient, method: str, path: str
) -> None:
    response = await client.request(method, path, json={})
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "AUTHENTICATION_REQUIRED"
