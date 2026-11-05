# NetHealth Roadmap Audit

Audit date: 2026-09-22

Scope: every requirement and exit criterion in `MASTER_PLAN.md` Phases 0-32.
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
| 21 Field technician | Complete | Assignment-scoped tickets, ordered actions, notes, bounded photos, and a field operations UI. |
| 22 Historical analytics | Complete | Incident, outage, repair-time, subscriber, optical, congestion, and availability measures. |
| 23 Reporting | Complete | Six permission-protected operational CSV report types. |
| 24 Global search | Complete | Permission-filtered subscriber, fiber, inventory, incident, and site search. |
| 25 Escalation | Complete | Configurable ordered escalation steps, scheduled evaluation, delivery, and deduplication. |
| 26 Maintenance | Complete | Audited device/site windows and explicit expected-maintenance incident labeling. |
| 27 Suppression | Complete | Topology-aware downstream attachment to an active explaining upstream incident. |
| 28 Security hardening | Complete | Environment-backed credentials and boolean-only credential state in API responses. |
| 29 Segmentation | Complete | Private application data network, collector-only outbound network, and loopback host publications. |
| 30 Database security | Complete | Production TLS enforcement, separate runtime/migration/backup roles, and encrypted backups. |
| 31 Audit log | Complete | Append-only audit integration for authentication, configuration, workflow, and incident actions. |
| 32 Privacy | Complete | Pseudonymous subscriber identity and schema/API exclusion of prohibited customer data. |
| 33 Scale testing | Complete | Four approved synthetic scales and the 5,000-disconnect correlated incident scenario. |
| 34 Simulator | Complete | Approved topology shape and deterministic operational metric generation. |
| 35 Failure simulation | Complete | All ten manual failures with evidence and expected diagnoses. |
| 36 Automated suite | Complete | Unit, integration, API, collector, rule, correlation, security, authorization, database, frontend, and E2E categories. |
| 37 Correlation regressions | Complete | Exact PON, OLT, isolated optical, and shared-core congestion scenarios. |
| 38 UX polish | Complete | Consistent accessible status text and non-color indicators across shared status UI. |
| 39 Observability | Complete | Authenticated platform health for all ten approved platform signals. |
| 40 Disaster recovery | Complete | Encrypted database/configuration backups and a successful guarded restore test. |
| 41 Production deployment | Ready | Linux Compose, hardened Nginx TLS proxy, and deployment checks are implemented; approved host deployment remains external. |
| 42 Pilot | Blocked | Runbook and evidence validation exist; an approved router/OLT pilot is required. |
| 43 Real data | Blocked | Five authoritative comparison gates require ISP access and operator evidence. |
| 44 Expansion | Blocked | POP-to-full-network progression requires successful live gate evidence. |
| 45 Acceptance | Blocked | Final sign-off cannot precede pilot, real-data, and expansion evidence. |

## Cross-cutting verification

- Backend: 149 tests passed; Ruff passed; strict mypy passed across 120 source files.
- Frontend: 18 tests passed; ESLint, TypeScript, and production build passed.
- Database: migrations applied through `0019`; Alembic drift check found no changes.
- Runtime: backend, frontend, PostgreSQL, TimescaleDB, and Redis health checks passed.
- Exposure: backend `127.0.0.1:8000`, frontend `127.0.0.1:3000`, and syslog
  `127.0.0.1:5514/udp`; PostgreSQL and Redis are internal-only. No unspecified,
  `0.0.0.0`, or IPv6-any host binding, Docker socket, privileged container, or
  host networking is configured.
- Security: no production credentials were introduced; the browser remains
  backend-only and collectors remain the sole infrastructure-facing layer.
  Upgrade-safe role provisioning and an encrypted backup smoke test passed.

The next operational work is Phase 41 deployment on an approved Linux host,
followed by the Phase 42 pilot. Phases 42-45 remain evidence-gated.
