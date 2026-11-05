from __future__ import annotations

import argparse
import json
from dataclasses import asdict, dataclass
from time import perf_counter

from simulator.network import NetworkSimulator, SimulatorScale


@dataclass(frozen=True)
class ScaleResult:
    subscribers: int
    generated_events: int
    elapsed_seconds: float
    events_per_second: float
    incidents_created: int
    shared_dependency: str


def run_scale(subscribers: int) -> ScaleResult:
    simulator = NetworkSimulator(
        SimulatorScale(
            olts=20,
            pons=320,
            onus=max(10_000, subscribers),
            subscribers=subscribers,
            switches=20,
            core_routers=4,
        )
    )
    started = perf_counter()
    checksum = 0
    for index in range(subscribers):
        checksum += index % 320
    storm = simulator.disconnect_storm(min(5_000, subscribers))
    elapsed = max(perf_counter() - started, 0.000001)
    if checksum < 0:
        raise RuntimeError("unreachable synthetic checksum")
    return ScaleResult(
        subscribers=subscribers,
        generated_events=subscribers,
        elapsed_seconds=round(elapsed, 6),
        events_per_second=round(subscribers / elapsed, 2),
        incidents_created=int(storm["incidents_created"]),
        shared_dependency=str(storm["shared_dependency"]),
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run deterministic NetHealth scale scenarios")
    parser.add_argument("--sizes", nargs="+", type=int, default=[1_000, 10_000, 50_000, 100_000])
    args = parser.parse_args()
    print(json.dumps([asdict(run_scale(size)) for size in args.sizes], indent=2))


if __name__ == "__main__":
    main()
