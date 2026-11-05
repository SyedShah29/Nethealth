import argparse
import json

from simulator.network import FailureKind, NetworkSimulator, SimulatorScale


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate deterministic NetHealth simulation data")
    parser.add_argument("--subscribers", type=int, default=10_000)
    parser.add_argument("--failure", choices=[item.value for item in FailureKind])
    parser.add_argument("--disconnect-storm", type=int)
    args = parser.parse_args()
    scale = SimulatorScale(onus=max(10_000, args.subscribers), subscribers=args.subscribers)
    simulator = NetworkSimulator(scale)
    if args.failure:
        result = simulator.trigger(FailureKind(args.failure))
        print(json.dumps(result.__dict__, default=str, indent=2))
    elif args.disconnect_storm:
        print(json.dumps(simulator.disconnect_storm(args.disconnect_storm), indent=2))
    else:
        print(json.dumps(simulator.snapshot(), indent=2))


if __name__ == "__main__":
    main()
