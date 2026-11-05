from pathlib import Path

from scripts.operational_acceptance import validate_evidence

from app.core.platform_metrics import ApiMetrics

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_api_metrics_track_latency_and_server_errors() -> None:
    metrics = ApiMetrics()
    metrics.observe(10.0, 200)
    metrics.observe(30.0, 503)
    snapshot = metrics.snapshot()
    assert snapshot.request_count == 2
    assert snapshot.error_count == 1
    assert snapshot.average_response_ms == 20.0
    assert snapshot.maximum_response_ms == 30.0


def test_operational_acceptance_remains_blocked_without_real_evidence() -> None:
    assert validate_evidence({})


def test_operational_acceptance_requires_every_external_gate() -> None:
    evidence = {
        "pilot": {
            "router": "router-1",
            "olt": "olt-1",
            "pons": ["pon-1"],
            "subscriber_group": "pilot-a",
            "pipeline_validated": True,
        },
        "real_data_comparisons": {
            key: {"status": "MATCHED"}
            for key in (
                "router_cli",
                "olt_cli",
                "existing_monitoring",
                "radius",
                "known_outage_history",
            )
        },
        "expansion": {
            "completed_stages": [
                "PILOT",
                "ONE_POP",
                "SEVERAL_POPS",
                "ONE_REGION",
                "FULL_NETWORK",
            ]
        },
        "acceptance": {
            key: "ACCEPTED"
            for key in (
                "monitoring",
                "metrics",
                "intelligence",
                "operations",
                "analytics",
                "security",
                "platform_reliability",
            )
        },
    }
    assert validate_evidence(evidence) == []


def test_production_frontend_uses_same_origin_api() -> None:
    production_compose = (PROJECT_ROOT / "docker-compose.production.yml").read_text(
        encoding="utf-8"
    )

    assert production_compose.count("NEXT_PUBLIC_API_BASE_URL: /api/v1") == 2
    assert "http://127.0.0.1:8000" not in production_compose


def test_non_root_proxy_uses_writable_temporary_paths() -> None:
    production_compose = (PROJECT_ROOT / "docker-compose.production.yml").read_text(
        encoding="utf-8"
    )
    nginx_config = (PROJECT_ROOT / "deploy" / "nginx" / "nginx.conf").read_text(
        encoding="utf-8"
    )

    assert 'user: "101:101"' in production_compose
    assert "- /tmp" in production_compose
    assert "pid /tmp/nginx.pid;" in nginx_config
    for temporary_path in (
        "client_body_temp_path /tmp/client_temp;",
        "proxy_temp_path /tmp/proxy_temp;",
        "fastcgi_temp_path /tmp/fastcgi_temp;",
        "uwsgi_temp_path /tmp/uwsgi_temp;",
        "scgi_temp_path /tmp/scgi_temp;",
    ):
        assert temporary_path in nginx_config
