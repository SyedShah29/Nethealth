# Performance and Scale Validation

The deterministic scale harness runs the approved 1,000, 10,000, 50,000, and
100,000-subscriber datasets without creating customer PII or contacting ISP
infrastructure:

```text
python -m scripts.performance_scale --sizes 1000 10000 50000 100000
```

Each result reports generated events, elapsed time, throughput, incident count,
and shared dependency. The critical scenario generates 5,000 disconnects in a
30-second logical window and must produce one correlated PON incident rather
than 5,000 subscriber incidents.

The simulator defaults to 20 OLTs, 320 PONs, 10,000 ONUs/subscribers, 20
switches, and four core routers. It emits CPU, memory, traffic, latency, packet
loss, optical, disconnect, outage, and congestion facts. Manual failure choices
cover ONU, PON, OLT, access switch, aggregation, core, congestion, optical
degradation, packet loss, and latency spike:

```text
python -m simulator.cli --failure PON_FAILURE
python -m simulator.cli --disconnect-storm 5000
```

These repeatable synthetic results validate application algorithms. They do not
replace Phase 42–45 pilot, real-data, expansion, or operational acceptance
evidence.
