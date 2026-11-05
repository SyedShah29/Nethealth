from simulator.network import FailureKind, NetworkSimulator, SimulatorScale


def test_default_simulator_matches_approved_network_shape_and_metrics() -> None:
    simulator = NetworkSimulator()
    assert simulator.scale == SimulatorScale()
    assert set(simulator.snapshot()["metrics"]) == {
        "cpu_percent",
        "memory_percent",
        "traffic_percent",
        "latency_ms",
        "packet_loss_percent",
        "optical_rx_dbm",
        "disconnects",
    }


def test_every_manual_failure_has_evidence_and_expected_diagnosis() -> None:
    simulator = NetworkSimulator()
    for failure_kind in FailureKind:
        failure = simulator.trigger(failure_kind)
        assert failure.expected_diagnosis
        assert failure.evidence
        assert failure.affected_subscribers >= 1


def test_critical_disconnect_storm_is_correlated_to_one_incident() -> None:
    result = NetworkSimulator().disconnect_storm()
    assert result["events_ingested"] == 5_000
    assert result["window_seconds"] == 30
    assert result["incidents_created"] == 1
    assert result["shared_dependency"] == "PON-4"


def test_all_approved_scale_sizes_remain_bounded() -> None:
    from scripts.performance_scale import run_scale

    for size in (1_000, 10_000, 50_000, 100_000):
        result = run_scale(size)
        assert result.generated_events == size
        assert result.events_per_second > 0
        assert result.incidents_created == 1
