# NetHealth API

Base path:

/api

Planned API groups:

/api/auth
/api/users
/api/sites
/api/devices
/api/interfaces
/api/olts
/api/pons
/api/onus
/api/subscribers
/api/topology
/api/metrics
/api/incidents
/api/alerts
/api/rules
/api/anomalies
/api/capacity
/api/technicians
/api/maintenance
/api/reports
/api/admin
/api/system

Exact contracts are documented as endpoints are implemented.

## Phase 0 health endpoints

`GET /api/health` returns API process health and the service name.

`GET /api/health/database` verifies PostgreSQL connectivity and confirms that
the TimescaleDB extension is enabled.

`GET /api/health/redis` verifies Redis connectivity.

Dependency failures return HTTP 503 using the standardized envelope:

```json
{
  "error": {
    "code": "REDIS_UNAVAILABLE",
    "message": "Redis health check failed.",
    "request_id": "request-correlation-id"
  }
}
```

Credentials, dependency exceptions, and connection details are never returned.

## Phase 1 authentication

Authentication uses an opaque server-side session. The raw token is delivered
as an HttpOnly, SameSite=Strict cookie scoped to `/api`; only its SHA-256 hash is
stored. Production cookies also use the Secure attribute.

- `POST /api/auth/login` accepts `email` and `password`, sets the session
  cookie, and returns the user plus expiration time.
- `POST /api/auth/logout` revokes the current session and clears the cookie.
- `GET /api/auth/me` returns the authenticated user.

Invalid credentials, inactive users, locked users, expired sessions, and
revoked sessions use generic responses that do not disclose sensitive account
state.

## Phase 1 users and administration

The following endpoints require explicit RBAC permissions:

- `GET /api/users` requires `users:manage`.
- `POST /api/users` requires `users:manage` and creates a user.
- `PATCH /api/users/{user_id}` requires `users:manage` and may change a name,
  role, or active state.
- `GET /api/admin/roles` requires `roles:read`.
- `GET /api/admin/audit-logs?limit=100` requires `audit:read`.

State-changing browser requests must originate from an approved frontend or
the backend origin. Permission failures return `PERMISSION_DENIED` with HTTP
403. Missing, expired, or revoked sessions return `AUTHENTICATION_REQUIRED`
with HTTP 401.
## Phase 2 inventory endpoints

Sites, devices, interfaces, collector profiles, and collector assignments expose
authenticated CRUD endpoints under `/api`. Device listing supports search,
site, device type, status, and monitoring-state filters. These endpoints manage
metadata only and never communicate directly with ISP infrastructure.
Collector profiles support `GET/POST/PATCH/DELETE`; they remain declarative
configuration consumed asynchronously by collector workers. Profile fields
include collector type, secret configuration key, polling interval, failure
threshold, enabled state, name, and description. API responses never include
resolved credentials.
`GET /api/collector-status` exposes authenticated persisted collector health,
optionally filtered by `device_id`.

## Phase 1 role administration

- `GET /api/admin/roles` and `GET /api/admin/permissions` require `roles:read`.
- `PATCH /api/admin/roles/{role_id}` requires `roles:manage`, replaces an
  optional permission set, and may update the description.

The administrator role cannot lose `users:manage`, `roles:manage`, or
`audit:read`, preventing configuration from removing all administrative access.
Role changes are audited.

## Phase 4 metrics

`GET /api/metrics` requires `metrics:read` and a bounded half-open time window
using the `start` and `end` query parameters. Optional filters are
`entity_type`, `entity_id`, `metric_name`, and `source`. `limit` defaults to
1,000 and is capped at 10,000.

The `resolution` parameter accepts:

- `raw` for individual metric envelopes
- `5m` for 5-minute aggregates
- `1h` for hourly aggregates
- `1d` for daily aggregates

Aggregate responses contain the bucket and metric dimensions plus
`value_avg`, `value_min`, `value_max`, `value_sum`, and `sample_count`. The API
has no metric write endpoint; operational samples are written only by collector
workers. Invalid or reversed time windows return `INVALID_TIME_RANGE` with HTTP
422. Credentials and infrastructure management addresses are never metric tags
or response fields.

## Phase 5 subscribers

All subscriber endpoints require `subscribers:read`. They expose operational
identifiers only and never expose infrastructure credentials or unnecessary
customer PII.

- `GET /api/subscribers` lists subscribers with offset/limit pagination.
  Optional filters are `search`, `status`, `nas_id`, `olt_id`, `pon_id`, and
  `onu_id`. Search matches the NetHealth subscriber ID or permitted external
  reference.
- `GET /api/subscribers/resolve?external_reference=...` resolves an existing
  ISP reference to the independently managed NetHealth subscriber ID.
- `GET /api/subscribers/{subscriber_id}` returns one operational record.
- `GET /api/subscribers/{subscriber_id}/sessions` returns newest sessions
  first and accepts a bounded `limit`.

Unknown subscribers and mappings return `SUBSCRIBER_NOT_FOUND` with HTTP 404.
Phase 5 adds no browser-facing subscriber mutation endpoint; later approved
integration and synchronization phases own record ingestion.

## Phase 6 fiber access and optics

Read endpoints require `operational:read`:

- `GET /api/olts` and `GET /api/olts/{olt_id}`
- `GET /api/pons` and `GET /api/pons/{pon_id}`; listing supports OLT and status
  filters.
- `GET /api/onus` and `GET /api/onus/{onu_id}`; listing supports OLT, PON,
  subscriber, status, search, and bounded pagination.
- `GET /api/onus/{onu_id}/optical-status` returns current RX/TX power,
  temperature, and distance classified as `GOOD`, `WARNING`, `CRITICAL`, or
  `UNKNOWN`.
- `GET /api/onus/{onu_id}/optical-history?window=...` accepts `current`, `24h`,
  `7d`, or `30d`. Historical windows use 5-minute, hourly, and daily Phase 4
  aggregates respectively.
- `GET /api/optical-thresholds` lists threshold configurations.

Creating, updating, or deleting `/api/optical-thresholds` requires
`thresholds:manage`, a trusted browser origin, and creates a threshold-change
audit event. Threshold scope consists of vendor, technology, optional device
model, and metric; credentials and management operations are never exposed.

## Phase 7 topology

Topology reads require `topology:read`. Node and edge configuration requires
`devices:manage`, trusted-origin validation, and creates an audit event.

- `GET /api/topology` returns all nodes and upstream-to-downstream edges.
- `POST /api/topology/nodes` and `PATCH/DELETE /api/topology/nodes/{node_id}`
  manage topology nodes.
- `POST /api/topology/edges` and `DELETE /api/topology/edges/{edge_id}` manage
  dependency edges.
- `GET /api/topology/nodes/{node_id}/downstream` returns descendants.
- `GET /api/topology/nodes/{node_id}/impact` groups failure impact by type.
- `POST /api/topology/common-infrastructure` returns the lowest shared ancestor.
- `GET /api/topology/pons/{pon_id}/subscribers` returns dependent subscribers.
- `GET /api/topology/subscribers/{subscriber_id}/olt` returns the serving OLT.
- `GET /api/topology/olts/{olt_id}/upstream` returns the nearest upstream device.
- `GET /api/topology/interfaces/{interface_id}/downstream-devices` returns
  devices depending on an inventory interface.

## Phase 8 rules

- `GET /api/rules` and `GET /api/rules/{rule_id}` require `operational:read`.
- `POST /api/rules` and `PATCH/DELETE /api/rules/{rule_id}` require
  `rules:manage` and trusted origin.
- `POST /api/rules/{rule_id}/evaluate` requires `rules:manage`, evaluates
  normalized signals, and persists evidence and trigger state.
- `GET /api/rules/evaluations` requires `operational:read` and supports rule,
  entity-type, entity-ID, and bounded-limit filters.

## Phase 9 outage correlation

- `POST /api/correlations/evaluate` requires `incidents:manage`. Observations
  must fit within a configured 30–120 second window.
- `GET /api/correlations` requires `incidents:read`.

Responses contain common ancestor, classification, discrete confidence,
affected entities, and factual evidence. They are not Phase 14 incident records.

## Phase 10 root-cause classification

- `POST /api/root-causes/classify` deterministically classifies supplied facts
  and an optional correlation result.
- `GET /api/root-causes` and `GET /api/root-causes/{assessment_id}` read saved
  assessments.

All root-cause endpoints require `diagnostics:read`. Outputs contain a
classification, severity, evidence, affected entities, and recommended checks.
