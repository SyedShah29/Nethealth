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
