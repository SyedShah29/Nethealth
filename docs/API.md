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
