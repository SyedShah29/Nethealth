\# NetHealth Project Progress



\## Phase 0 — Project Foundation



Status: complete, including live Docker integration validation on 2026-09-19.

Governance and security review completed on 2026-09-19. The review added the
planned top-level repository directories and ensured unexpected exception
messages cannot leak through logs or API responses.

\- \[x] Backend skeleton

\- \[x] Frontend skeleton

\- \[x] PostgreSQL

\- \[x] TimescaleDB

\- \[x] Redis

\- \[x] Docker Compose

\- \[x] Environment configuration

\- \[x] Structured logging

\- \[x] Standardized error handling

\- \[x] Health endpoints

\- \[x] Backend testing setup

\- \[x] Frontend testing setup

\- \[x] Linting

\- \[x] Type checking

Completed verification:

\- backend unit/API tests

\- backend lint and type checking

\- frontend component tests, lint, type checking, and production build

\- Alembic offline migration generation

\- Docker Compose configuration rendering and network-exposure audit

\- live PostgreSQL 16 and TimescaleDB 2.19.3 startup

\- live Redis, migration, backend, worker, and frontend startup

\- live API, database, Redis, and frontend health checks

\- live host-port, private-network, non-root process, and container-hardening audit

\- dependency audit with zero reported npm vulnerabilities

\- unexpected-error secret-safety regression test



\## Phase 1 — Authentication and RBAC



Status: complete, including live migration and integration validation on
2026-09-19.

\- \[x] User model

\- \[x] Roles

\- \[x] Permissions

\- \[x] Authentication

\- \[x] Logout and session expiration

\- \[x] Failed-login protection and account disabling

\- \[x] RBAC enforcement

\- \[x] Audit logging

Completed verification:

\- backend authentication, session, lockout, RBAC, audit, API, and model tests

\- backend lint and strict type checking

\- frontend tests, lint, type checking, and production build

\- Alembic offline SQL generation and live upgrade to revision `0002`

\- live seeded-role, permission, runtime database grant, and audit-event checks

\- live unauthenticated, invalid-credential, health, and container exposure checks



\## Phase 2 — Network Inventory



\- \[ ] Sites

\- \[ ] Devices

\- \[ ] Interfaces

\- \[ ] Device API

\- \[ ] Inventory UI



\## Phase 3 — Collector Framework



\- \[ ] Collector abstraction

\- \[ ] ICMP collector

\- \[ ] SNMP collector

\- \[ ] Syslog receiver

\- \[ ] Vendor adapters

\- \[ ] Scheduler

\- \[ ] Collector failure handling



\## Remaining Phases



See `docs/MASTER\_PLAN.md`.

Phase 2 inventory implementation is complete: sites, devices, interfaces,
metadata-only collector profiles/assignments, RBAC permissions, migration 0003,
CRUD APIs, and the inventory search/filter view.
Collector profiles now also support update and delete operations.
Phase 2 inventory UI is complete with site grouping, device detail pages,
interface lists, monitoring state, and frontend coverage.

Phase 3 collector framework complete: shared collector contracts, normalized
health/syslog schemas, ICMP/SNMP adapter boundaries, vendor adapter structure,
and scheduler primitives are implemented with tests. Network transports remain
configuration-driven and no credentials are hardcoded.

Phase 3 runtime pieces added: platform ICMP probe, SNMP query transport boundary,
UDP syslog receiver, consecutive-failure tracking, scheduler status tracking,
and migration 0004 for persistent collector status.
Concrete SNMP/UDP transport integration, vendor adapter modules, collector
runner persistence hooks, and default polling interval scheduling are included.
Collector registry, scheduled execution wiring, authenticated collector-status
listing, and end-to-end runner/registry tests complete the Phase 3 scope.
The common contract now includes device health, interfaces, optical metrics,
subscriber sessions, and environment collection; SNMP counter/environment OIDs,
vendor OID maps, assignment execution, and the Celery poll boundary are wired.
Optical and subscriber-session collection paths now execute through configured
SNMP OIDs, vendor overrides are applied during collection, and worker services
execute persisted assignment batches.
SNMP table walking, power/fan readings, expanded vendor metric maps, and syslog
event classification are implemented and covered by tests.

