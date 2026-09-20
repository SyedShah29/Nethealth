# NetHealth Project Progress

## Phase 0 — Project Foundation

Status: complete. Revalidated on 2026-09-20.

- [x] FastAPI backend and Next.js TypeScript frontend
- [x] PostgreSQL 16 with TimescaleDB and Alembic
- [x] Redis and Celery worker foundation
- [x] Docker Compose and environment configuration
- [x] Structured logging and standardized error handling
- [x] API, database, and Redis health endpoints
- [x] Backend and frontend test, lint, type-check, and build foundations
- [x] Loopback-only host publishing; PostgreSQL and Redis remain internal-only

## Phase 1 — Authentication and Access Control

Status: complete. Revalidated on 2026-09-20.

- [x] User, role, permission, session, and append-only audit models
- [x] Argon2id password hashing and opaque server-side sessions
- [x] Login, logout, expiration, failed-login lockout, and account disabling
- [x] Permission enforcement on every protected endpoint
- [x] Initial role capability mappings, including least-privilege support and field roles
- [x] Administrator role and permission management with core-admin lockout protection
- [x] Auditing for authentication, users, role assignments, and configuration changes
- [x] Audit event vocabulary for later threshold and incident actions

## Phase 2 — Network Inventory

Status: complete. Revalidated on 2026-09-20.

- [x] Exact approved device types
- [x] Site, device, interface, collector-profile, and collector-assignment models
- [x] CRUD APIs for sites, devices, interfaces, and collector assignments
- [x] Persistent, audited configuration changes
- [x] Device list, search, site/type/status/monitoring filters, site grouping, and state
- [x] Device detail and interface list views
- [x] Frontend inventory tests

## Phase 3 — Collector Framework

Status: complete. Revalidated on 2026-09-20.

- [x] Common read-only collector contract
- [x] Multi-attempt ICMP reachability, mean latency, packet loss, and failure thresholds
- [x] SNMPv3-first transport with SNMPv2c compatibility
- [x] Uptime, CPU, memory, interface state, counters, errors, and discards
- [x] Temperature plus vendor power/fan metrics where supported
- [x] Vendor optical and subscriber metric paths where supported
- [x] Generic, Cisco, Huawei, MikroTik, and ZTE adapters
- [x] UDP syslog receiver and normalized event schema
- [x] Configurable assignment intervals and Celery Beat dispatch
- [x] Database-backed assignment execution without credentials in task payloads
- [x] Safe per-assignment failure isolation and persistent collector status
- [x] Authenticated collector-status API

## Latest validation

- Backend: 45 tests passed; Ruff passed; strict mypy passed.
- Frontend: 4 tests passed; ESLint passed; TypeScript passed; production build passed.
- Docker images built and the complete stack started successfully.
- Alembic live migration reached revision `0006` (head).
- API and frontend returned HTTP 200; PostgreSQL, TimescaleDB, and Redis health passed.
- Celery Beat dispatched repeated cycles and the worker completed them without errors.
- UDP syslog was exercised through the loopback-only host binding.
- Docker exposure audit found only loopback backend, frontend, and syslog publications.

## Next phase

Phase 4 — Metrics Platform. It has not been started.
