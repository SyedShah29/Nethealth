\# NetHealth Data Model



Planned core entities:



\- User

\- Role

\- Permission



\- Site

\- Device

\- Interface



\- OLT

\- PON

\- ONU



\- Subscriber

\- SubscriberSession



\- TopologyNode

\- TopologyEdge



\- MetricDefinition

\- MetricSample



\- Rule

\- RuleCondition



\- Alert



\- Incident

\- IncidentEvent

\- IncidentAffectedEntity



\- MaintenanceWindow



\- Technician

\- TechnicianTask



\- NotificationChannel

\- NotificationRule



\- AuditLog



\- CollectorProfile

\- CollectorStatus



Detailed definitions are added during implementation.

\## Phase 1 authentication and access control

\### Role

Roles are seeded by migration and use the names `ADMIN`, `NOC_ENGINEER`,
`SUPPORT`, `FIELD_TECHNICIAN`, and `VIEWER`. A role has many permissions and
many users.

\### Permission

Permissions are stable action codes. The initial role mappings cover user and
role administration, audits, operational read access, topology, metrics,
subscribers, incidents, diagnostics, jobs, field notes/photos, dashboards, and
the planned configuration domains. The `ADMIN` role receives every seeded
permission. NOC, support, field, and viewer roles receive only their roadmap
capabilities; protected resources still enforce their specific code when those
later-phase endpoints are introduced.

\### User

Fields:

\- `id` UUID primary key
\- `name`
\- normalized, unique `email`
\- Argon2id `password_hash` (never returned by the API)
\- `role_id`
\- `active`
\- `failed_login_count`
\- `locked_until`
\- `created_at`
\- `updated_at`
\- `last_login`

\### AuthSession

Sessions contain a SHA-256 hash of a cryptographically random opaque token,
the owning user, creation and expiration timestamps, and an optional revocation
timestamp. Raw session tokens are sent only as HttpOnly cookies and are never
stored in the database.

\### AuditLog

Authentication and access-control events record the event type, optional actor
and target users, success state, request correlation ID, a one-way subject
fingerprint where needed, safe event metadata, and occurrence time. No API
supports updating or deleting audit events.

## Phase 2 inventory

`Site` stores name, code, region, optional coordinates, and description.
`Device` stores the approved device type, identity, management IP, vendor,
model, site, monitoring state, collector-profile reference, status, and
timestamps. `Interface` stores its device, name, description, speed, MAC
address, and administrative and operational states.

`CollectorProfile` declares `ICMP` or `SNMP`, an optional secret configuration
key, interval, failure threshold, description, and enabled state.
`CollectorAssignment` links a device to a collector profile and can be disabled
independently.

## Phase 3 collector status

`CollectorStatus` has one row per device and collector type. It stores the last
successful and failed poll times, consecutive failure count, latency, current
health, current worker, and update time. Operational metric samples are not
stored here; time-series persistence begins in Phase 4.

Collector credentials are not database fields. A profile stores only a key
that resolves to secret environment configuration inside collector workers.

## Phase 4 metrics platform

`MetricSample` is a TimescaleDB hypertable partitioned by `timestamp`. Every
sample uses the shared envelope:

- `timestamp`
- `entity_type`: `DEVICE`, `INTERFACE`, `ONU`, or `SUBSCRIBER`
- `entity_id`: a UUID string or stable collector-side identifier
- `metric_name`
- numeric `value`
- optional `unit`
- `source`
- JSON `tags` containing non-secret dimensions only

The primary key contains both the sample UUID and partition timestamp, as
required for TimescaleDB hypertables. The entity/metric/time index supports
bounded time-series lookup. Entity IDs intentionally have no foreign key so
ONU and subscriber observations can be retained before their Phase 5+ domain
records exist.

Continuous aggregates materialize 5-minute, hourly, and daily buckets with
average, minimum, maximum, sum, and sample count. Starting retention is 30 days
for raw samples, 180 days for 5-minute aggregates, 730 days for hourly
aggregates, and unlimited for daily aggregates. The first three durations are
configurable through `METRICS_*_RETENTION_DAYS` when the migration is applied.

## Phase 5 subscriber operational model

`Subscriber` uses the pseudonymous `subscriber_id` as its primary key. It
stores an optional unique `external_reference`, package speed in bits per
second, operational status, NAS/OLT/PON/ONU identifiers, optional current IP
and MAC address, and creation/update timestamps. It deliberately contains no
customer name, government identifier, address, billing data, browsing history,
or DNS history.

NAS, OLT, PON, and ONU identifiers are operational strings in Phase 5. The
fiber-access entities and their relational links are introduced by Phase 6;
Phase 5 does not pre-empt that schema.

`SubscriberSession` stores a UUID, owning subscriber, start and optional end
timestamps, NAS, optional IP address, optional disconnect reason, and optional
duration in seconds. Database checks reject negative durations and end times
before the start. Deleting a subscriber cascades only to that subscriber's
session history.

## Phase 6 fiber access model

`OLT` has a one-to-one relation to an inventory `Device` and stores vendor,
model, frame count, structured slot information, and uplink identifiers.

`PON` belongs to an OLT and is uniquely identified within it by frame, slot,
and port. It stores the access technology, status, subscriber count, and
configured capacity. Database checks reject negative coordinates/counts,
non-positive capacity, and subscriber counts above capacity.

`ONU` belongs to a PON and carries the same OLT identifier through a composite
foreign key, preventing a PON/OLT mismatch. It stores the ONU identifier,
globally unique serial number, optional subscriber relation, status, last-seen
time, registration status, current RX/TX power, temperature, and optional
distance.

`OpticalThreshold` scopes one metric configuration by vendor, technology, and
optional device model. Supported metrics are RX power, TX power, temperature,
and distance. Low/high warning and critical boundaries are validated in both
Pydantic and PostgreSQL. A PostgreSQL nulls-not-distinct unique index prevents
duplicate generic thresholds when no device model is specified.

Migration `0009` reconciles the Phase 2 inventory foreign-key indexes with ORM
metadata. TimescaleDB's extension-owned timestamp index is excluded from
Alembic comparison; migration `0010` adds the Phase 6 tables.

## Phase 7 topology engine

`TopologyNode` represents `TRANSIT`, `CORE`, `BNG`, `BRAS`, `AGGREGATION`,
`ACCESS`, `OLT`, `PON`, `ONU`, or `SUBSCRIBER`. A node has a human-readable
name, status, non-secret attributes, and an optional unique reference to its
authoritative operational entity.

`TopologyEdge` is directed from upstream `source_node_id` to downstream
`target_node_id`. Self-edges and duplicate edges are rejected. An optional
inventory interface identifies the upstream interface carrying the dependency.
Node attributes may carry non-secret normalized site, uplink, or other
correlation dimension identifiers.

## Phase 8 rule engine

`Rule` stores its entity type, validated condition list, evaluation duration,
severity, incident category, recommendation, and enabled state. Conditions use
the deterministic `GT`, `GTE`, `LT`, `LTE`, `EQ`, and `NE` operators.

`RuleEvaluation` records every evaluation's rule, entity, time, boolean result,
condition evidence, and `DISABLED`, `CLEAR`, `PENDING`, or `TRIGGERED` state.
Migration `0012` seeds the congestion, critical optical, device-unreachable,
and unstable-subscriber rules described by the master plan.

## Phase 9 outage correlation

`OutageCorrelation` stores the bounded correlation window, lowest shared
topology ancestor, deterministic classification, evidence-derived confidence,
affected entity references, and evidence. Confidence is `LOW`, `MEDIUM`,
`HIGH`, or `CONFIRMED`, never an invented percentage.

Correlation findings are analysis records. Phase 14 remains responsible for
incident lifecycle, automatic creation, and deduplication.

## Phase 10 root-cause classification

`RootCauseAssessment` stores an optional correlation reference, classification,
severity, factual evidence, affected entities, and ordered recommended checks.
Classifiers return `UNDETERMINED` when facts do not match a known case.

Migrations `0011` through `0014` add the Phase 7–10 tables.
