# NetHealth Roadmap Audit

Audit date: 2026-09-21

Scope: every requirement and exit criterion in `MASTER_PLAN.md` Phases 0-20.
Evidence was checked against implementation, migrations, automated tests, the
production frontend build, and the running Docker Compose stack.

| Phase | Result | Verified evidence |
| --- | --- | --- |
| 0 Foundation | Complete | FastAPI and strict Next.js foundations, canonical `/api/v1` plus required `/api` health compatibility, PostgreSQL/TimescaleDB, Redis, Celery, structured errors/logging, migrations, tests, and Docker startup. |
| 1 Access control | Complete | Users, roles, permissions, Argon2id, opaque server sessions, lockout/disable/logout, protected APIs, and append-only audit events. |
| 2 Inventory | Complete | Approved site/device/interface/profile/assignment models, filters, APIs, views, and audited configuration. |
| 3 Collectors | Complete | Read-only contracts, ICMP, SNMPv3/v2c, syslog, vendor adapters, schedules, failure isolation, status persistence, and required failure-category tests. |
| 4 Metrics | Complete | Normalized TimescaleDB samples, rate derivation, aggregates, retention, bounded queries, and collector-only writes. |
| 5 Subscribers | Complete | Pseudonymous operational identity, mapping, sessions, constraints, protected APIs, search, and no prohibited PII. |
| 6 Fiber | Complete | OLT/PON/ONU hierarchy, integrity, configurable optics, classification, history, UI, RBAC, and threshold auditing. |
| 7 Topology | Complete | Directed dependencies, graph queries, impact/common-infrastructure resolution, protected configuration, and accessible interactive UI. |
| 8 Rules | Complete | Fixed safe operators, configurable duration/severity/category/recommendation, initial rules, evidence, persistence, RBAC, and auditing. |
| 9 Correlation | Complete | Bounded windows, shared failing dependency, topology impact, confidence levels, evidence, persistence, and outage regression coverage. |
| 10 Root cause | Complete | Deterministic PON, congestion, optical, OLT, and core classifiers; safe `UNDETERMINED` behavior; evidence and checks. |
| 11 Health scoring | Complete | Configurable six-component weights and category thresholds, persisted 0-100 scores, and per-component UI explanation. |
| 12 Customer 360 | Complete | Identity, session, fiber, performance, stability, incident, deterministic diagnosis, recommendation, and health sections. |
| 13 Anomalies | Complete | Rolling mean/deviation, z-score, EWMA, rate-of-change, baseline, seasonal, optical/traffic classifications, and required explanation. |
| 14 Incidents | Complete | Full incident record, all states, rule/correlation creation, deduplication, assignments, comments, impact, evidence, and recommendations. |
| 15 Timeline | Complete | Chronological creation, evidence attachment, lifecycle, assignment, and comment events. |
| 16 Alerting | Complete | Six channel adapter types, configurable routing, incident-level aggregation, and per-channel deduplication; external providers remain queued until configured. |
| 17 NOC dashboard | Complete | Required summary and all ten widgets, including latest subscriber-health distribution and OLT device status. |
| 18 Topology dashboard | Complete | Site, device type, severity, vendor, and region filters plus downstream subscriber/PON impact counts. |
| 19 Capacity | Complete | Generic approved entity/metric monitoring, seeded and configurable 70/80/90 thresholds, sustained multi-sample evaluation, and evidence. |
| 20 Trending | Complete | Statistical slope, projected threshold crossing, observation window/sample count, disclosed assumptions, and non-certain wording. |

## Cross-cutting verification

- Backend: 126 tests passed; Ruff and strict mypy passed.
- Frontend: 16 tests passed; ESLint, TypeScript, and production build passed.
- Database: migrations applied through `0018`; Alembic drift check found no changes.
- Runtime: backend, frontend, PostgreSQL, TimescaleDB, and Redis health checks passed.
- Exposure: backend `127.0.0.1:8000`, frontend `127.0.0.1:3000`, and syslog
  `127.0.0.1:5514/udp`; PostgreSQL and Redis are internal-only. No unspecified,
  `0.0.0.0`, or IPv6-any host binding, Docker socket, privileged container, or
  host networking is configured.
- Security: no production credentials were introduced; the browser remains
  backend-only and collectors remain the sole infrastructure-facing layer.

The next approved work is Phase 21, the Field Technician Module.
