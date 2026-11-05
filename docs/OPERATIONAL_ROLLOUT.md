# Operational Rollout and Acceptance

Phases 42–45 are evidence gates performed against explicitly approved ISP
infrastructure. They must never be marked complete from simulator results.

## Pilot network

Start with one read-only router collector, one OLT, one or two PONs, and a small
pseudonymous subscriber group. Record the approved management targets,
collector profile keys, start/end time, operator, rollback contact, and evidence
that collection, normalization, metrics, rules, correlation, incidents,
notifications, and dashboards all worked. Never place credentials in this file
or in the evidence artifact.

## Real-data comparison

For each router, OLT, subscriber session, and known outage sample, record the
timestamp, pseudonymous entity ID, NetHealth value, authoritative CLI/tool value,
allowed tolerance, result, and investigation notes. Required sources are router
CLI, OLT CLI, the existing monitoring platform, RADIUS, and known outage history.
Discrepancies must be investigated; thresholds must not be changed merely to
hide incorrect collection or normalization.

## Expansion gates

Advance only in this order: `PILOT`, `ONE_POP`, `SEVERAL_POPS`, `ONE_REGION`,
`FULL_NETWORK`. At every gate record collector CPU/memory, failed polls, database
growth, queue depth, API latency, alert volume, incident deduplication, and an
explicit go/no-go approval. A failed gate returns to the previous stable scope.

## Final acceptance

Use `python scripts/operational_acceptance.py <evidence.json>` to validate that
the pilot, all five authoritative comparisons, every expansion gate, and the
seven Phase 45 acceptance areas have signed evidence. A `BLOCKED` result is
intentional until real operational evidence exists.
