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

## Phase 4 — Metrics Platform

Status: complete. Validated on 2026-09-20.

- [x] Shared time-series schema for device, interface, ONU, and subscriber entities
- [x] Device health, performance, reachability, latency, and environmental metrics
- [x] Interface rate, utilization, error, discard, counter, and state metrics
- [x] Configurable ONU optical, temperature, voltage, state, and distance collection
- [x] Configurable subscriber session, rate, uptime, and disconnect collection
- [x] Raw, 5-minute, hourly, and daily query resolutions
- [x] Configurable 30-day raw, 180-day 5-minute, and two-year hourly retention
- [x] Long-term daily aggregates without an expiry policy
- [x] Permission-protected, bounded metrics query API

## Phase 5 — Subscriber Operational Model

Status: complete. Validated on 2026-09-20.

- [x] Pseudonymous subscriber model without unnecessary customer PII
- [x] Optional unique external ISP reference mapping
- [x] Package speed, status, NAS, OLT, PON, ONU, current IP, and MAC fields
- [x] Subscriber session history with start/end, NAS, IP, reason, and duration
- [x] Database constraints for package speed, duration, and session time order
- [x] Permission-protected subscriber list, search, resolve, detail, and session APIs
- [x] Service/repository layering and standardized not-found behavior

## Phase 6 — OLT / PON / ONU Model

Status: complete. Validated on 2026-09-20.

- [x] Device-linked OLT model with frames, slot information, and uplinks
- [x] Frame/slot/port PON hierarchy with technology, state, capacity, and counts
- [x] ONU identity, registration, subscriber relation, current optics, and distance
- [x] Database-enforced ONU PON/OLT consistency
- [x] Vendor/technology/model-specific optical threshold configuration
- [x] GOOD, WARNING, CRITICAL, and UNKNOWN optical classification
- [x] Current, 24-hour, 7-day, and 30-day optical history API and UI
- [x] Read-only fiber inventory UI with OLT/PON/ONU hierarchy
- [x] Audited RBAC-protected threshold management
- [x] Phase 2 schema drift corrected and global Alembic check clean

## Phase 7 — Topology Engine

Status: complete. Validated on 2026-09-20.

- [x] Typed topology nodes and upstream-to-downstream dependency edges
- [x] PON subscriber, subscriber OLT, OLT upstream, common ancestor, interface
  downstream, and failure-impact queries
- [x] Cycle, duplicate, and self-edge protection
- [x] Interactive topology UI with filtering and downstream impact selection
- [x] Healthy, warning, critical, and unknown status text/icons plus color

## Phase 8 — Rule Engine

Status: complete. Validated on 2026-09-20.

- [x] Configurable conditions, duration, severity, category, recommendation,
  and enabled state
- [x] Fixed deterministic comparison operators without executable expressions
- [x] Congestion, optical, device-failure, and subscriber-instability rules
- [x] Persistent condition evidence and trigger-state evaluation history
- [x] RBAC-protected, trusted-origin, audited rule management

## Phase 9 — Outage Correlation Engine

Status: complete. Validated on 2026-09-20.

- [x] Configurable 30–120 second correlation window
- [x] Entity path resolution and lowest-common-ancestor correlation
- [x] Lowest shared failing dependency plus site/uplink dimension evidence
- [x] Downstream subscriber impact and shared-infrastructure evidence
- [x] LOW, MEDIUM, HIGH, and CONFIRMED evidence-derived confidence
- [x] Persisted findings without pre-empting Phase 14 incident lifecycle

## Phase 10 — Root Cause Classification

Status: complete. Validated on 2026-09-20.

- [x] Deterministic PON-level outage classification
- [x] Deterministic link-congestion classification
- [x] Deterministic subscriber optical-fault classification
- [x] OLT/core correlation mappings and safe `UNDETERMINED` result
- [x] Classification, severity, evidence, affected entities, and checks

## Latest validation

- Backend: 101 tests passed; Ruff passed; strict mypy passed.
- Frontend: 11 tests passed; ESLint passed; TypeScript and production build passed.
- Docker backend, migration, and frontend images built successfully.
- Alembic live migration reached revision `0014` (head), and the global schema
  drift check reports no pending upgrade operations.
- API and frontend returned HTTP 200; PostgreSQL, TimescaleDB, and Redis health passed.
- Celery Beat dispatched repeated cycles and the worker completed them without errors.
- UDP syslog was exercised through the loopback-only host binding.
- Docker exposure audit found only loopback backend, frontend, and syslog publications.

## Next phase

Phase 11 — Subscriber Health Scoring. It has not been started.
