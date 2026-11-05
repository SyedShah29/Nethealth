from app.services.analysis import classify_root_cause


def test_scenario_a_shared_pon_outage() -> None:
    result = classify_root_cause(
        {
            "offline_subscriber_count": 100,
            "subscribers_sharing_pon": 98,
            "pon_down": True,
            "olt_reachable": True,
            "other_pons_healthy": True,
        },
        None,
    )
    assert result[0] == "PON_LEVEL_OUTAGE"


def test_scenario_b_olt_outage() -> None:
    result = classify_root_cause(
        {"offline_subscriber_count": 600, "olt_reachable": False}, None
    )
    assert result[0] == "OLT_LEVEL_OUTAGE"


def test_scenario_c_isolated_subscriber_optical_fault() -> None:
    result = classify_root_cause(
        {
            "offline_subscriber_count": 1,
            "neighbors_healthy": True,
            "optical_degraded_before_disconnect": True,
        },
        None,
    )
    assert result[0] == "SUBSCRIBER_OPTICAL_FAULT"


def test_scenario_d_shared_core_congestion() -> None:
    result = classify_root_cause(
        {
            "shared_core_interface": True,
            "affected_path_count": 4,
            "uplink_utilization_pct": 98,
            "latency_increasing": True,
        },
        None,
    )
    assert result[:2] == ("CORE_CONGESTION", "CRITICAL")
    assert {item["fact"] for item in result[2]} >= {
        "shared_core_interface",
        "uplink_utilization_pct",
    }
