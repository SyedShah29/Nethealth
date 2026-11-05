from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_PILOT = {"router", "olt", "pons", "subscriber_group", "pipeline_validated"}
REQUIRED_COMPARISONS = {
    "router_cli",
    "olt_cli",
    "existing_monitoring",
    "radius",
    "known_outage_history",
}
EXPANSION_STAGES = ["PILOT", "ONE_POP", "SEVERAL_POPS", "ONE_REGION", "FULL_NETWORK"]
ACCEPTANCE_AREAS = {
    "monitoring",
    "metrics",
    "intelligence",
    "operations",
    "analytics",
    "security",
    "platform_reliability",
}


def validate_evidence(payload: dict[str, Any]) -> list[str]:
    missing: list[str] = []
    pilot = payload.get("pilot", {})
    for key in sorted(REQUIRED_PILOT):
        if not pilot.get(key):
            missing.append(f"pilot.{key}")
    comparisons = payload.get("real_data_comparisons", {})
    for key in sorted(REQUIRED_COMPARISONS):
        if comparisons.get(key, {}).get("status") != "MATCHED":
            missing.append(f"real_data_comparisons.{key}.status=MATCHED")
    expansion = payload.get("expansion", {})
    if expansion.get("completed_stages") != EXPANSION_STAGES:
        missing.append("expansion.completed_stages")
    acceptance = payload.get("acceptance", {})
    for key in sorted(ACCEPTANCE_AREAS):
        if acceptance.get(key) != "ACCEPTED":
            missing.append(f"acceptance.{key}=ACCEPTED")
    return missing


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate operational acceptance evidence")
    parser.add_argument("evidence", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.evidence.read_text(encoding="utf-8"))
    missing = validate_evidence(payload)
    print(json.dumps({"status": "BLOCKED" if missing else "COMPLETE", "missing": missing}, indent=2))
    raise SystemExit(1 if missing else 0)


if __name__ == "__main__":
    main()
