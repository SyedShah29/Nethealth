\# NetHealth Architecture



\## Core architecture



Frontend

&#x20;  |

&#x20;  v

Backend API

&#x20;  |

&#x20;  +-------------------+

&#x20;  |                   |

PostgreSQL         TimescaleDB

&#x20;  |

Analysis Services

&#x20;  |

&#x20;  +---------------------+

&#x20;  |                     |

Rule Engine       Correlation Engine

&#x20;  |

Incident Engine

&#x20;  |

Notification Engine





Collector Services

&#x20;  |

&#x20;  v

ISP Management Network

&#x20;  |

&#x20;  +-- Routers

&#x20;  +-- Switches

&#x20;  +-- OLTs

&#x20;  +-- ONUs

&#x20;  +-- RADIUS



\## Security boundary



The browser/frontend must never communicate directly with ISP

network infrastructure.



Only collector services may communicate with network devices.



Network credentials must remain within secure backend/collector

infrastructure.



\## Backend



\- Python 3.12

\- FastAPI

\- SQLAlchemy

\- Alembic

\- PostgreSQL

\- TimescaleDB

\- Redis



\## Frontend



\- Next.js

\- React

\- TypeScript



\## Workers



\- Celery

\- Redis



unless a documented decision changes this architecture.



\## Deployment



Initial deployment:



\- Linux

\- Docker

\- Docker Compose

\- reverse proxy

\- PostgreSQL/TimescaleDB

\- Redis

\- backend

\- workers

\- frontend

\## Phase 0 container networking

The local Compose stack uses separate edge and private bridge networks.

Only the frontend and backend API publish host ports, and both publish to
`127.0.0.1` only. PostgreSQL/TimescaleDB and Redis publish no host ports.
The database, cache, migration job, backend, and worker communicate over an
internal Docker network.

The database bootstrap account is limited to initialization. Alembic uses a
separate non-superuser migration role, while the backend and worker use a
least-privilege application role. PostgreSQL host authentication uses SCRAM.

No service mounts the Docker socket. Application containers run as non-root,
drop Linux capabilities, prevent privilege escalation, and use read-only root
filesystems with temporary storage where practical.

\## Phase 1 authentication architecture

Authentication and access control follow API, service, repository, and database
layers. Passwords use Argon2id. Browser clients receive an opaque HttpOnly
session cookie, while PostgreSQL stores only a SHA-256 token hash and explicit
expiration/revocation state.

Users belong to one role. Roles receive permissions through a many-to-many
mapping, and protected API dependencies require specific permission codes.
Authentication, user administration, role changes, disabling, and logout create
append-only audit records through the service layer.

Phase 2 inventory follows the API → service → repository → database layering.
Collector profiles and assignments are declarative metadata consumed by the
Phase 3 collector runtime.

Phase 3 collectors implement the shared `DeviceCollector` contract and return
normalized internal schemas. Protocol and vendor adapters are isolated under
`app/collectors`; collectors are the only layer permitted to communicate with
ISP infrastructure.

Collector assignments are selected from PostgreSQL by a Celery Beat dispatcher.
Only assignment identifiers enter Redis task payloads. Workers resolve secret
profile configuration at execution time, choose the protocol/vendor adapter,
invoke all supported collection contracts, and persist status independently so
one target failure cannot terminate the worker.

The worker joins a dedicated un-published collector bridge for outbound access
to explicitly configured management targets. The API, scheduler, database, and
Redis do not join that network. The syslog receiver publishes UDP only on the
host loopback interface during local development.

Phase 4 collector results flow through the metrics service into a TimescaleDB
hypertable. The service normalizes device, interface, ONU, and subscriber
observations into one metric envelope. Interface rates are calculated from
successive counter samples; raw counters remain available for traceability.
TimescaleDB continuous aggregates provide 5-minute, hourly, and daily query
resolutions. The API can only read metrics and requires `metrics:read`; only
collector workers write operational samples.

Phase 5 adds a privacy-minimized subscriber operational model behind the
backend API. The browser accesses subscriber records only through protected
API routes; it never queries RADIUS, NAS devices, OLTs, or ONUs. API requests
flow through the subscriber service and repository, and require the existing
`subscribers:read` capability. External ISP references are optional mappings,
so NetHealth subscriber IDs and session history remain independently usable.

Phase 6 models fiber access as inventory Device → OLT → frame/slot/port PON →
ONU. Composite database integrity prevents an ONU from referencing a PON on a
different OLT. Fiber APIs are read-only toward infrastructure; configuration
writes apply only to NetHealth optical threshold records and are audited.

Current ONU optical readings live on the operational ONU record. Historical
views read the Phase 4 TimescaleDB aggregates by the stable ONU identifier.
Threshold selection first matches vendor and technology, then applies a
device-model-specific threshold over a generic vendor/technology threshold.
The frontend reads these backend APIs only and never contacts OLTs or ONUs.

Phase 7 stores a directed acyclic dependency graph. Edges point from upstream
infrastructure to downstream dependents. The topology service performs graph
traversal, nearest-upstream, downstream-impact, interface-impact, and lowest
common-ancestor queries. Topology configuration flows through the protected
backend and never causes network-device configuration.

Phase 8 evaluates configurable rules with a deliberately small deterministic
operator set. Callers provide normalized signals; the rule service evaluates
every condition, applies the configured duration, and persists evidence and
trigger state. Rule configuration cannot execute code.

Phase 9 correlates observations only within the configured 30–120 second
window. It resolves entities into topology, identifies the lowest shared
ancestor, checks known health, calculates downstream impact, and assigns a
discrete evidence-derived confidence level. If multiple ancestors are shared,
the lowest unhealthy ancestor is selected. Shared site, OLT, PON, access,
aggregation, uplink, and router dimensions are retained as evidence. Phase 14
will convert findings into managed incidents.

Phase 10 applies ordered classifiers for PON outages, link congestion,
subscriber optical faults, OLT outages, and core outages. Each assessment
contains its evidence and recommended checks. Unmatched inputs are
`UNDETERMINED`; no probabilistic or LLM inference is used.

Phases 11-13 add persisted subscriber health and anomaly analysis. Health scores
retain component contributions, the exact configurable weights, and category
thresholds used. Customer 360 composes existing repositories into one backend
response. Anomaly methods are deterministic and retain baseline, difference,
threshold, duration, rolling mean, and rolling standard deviation evidence.

Phases 14-16 add the incident lifecycle, append-only incident events, and
notification routing. Triggered rules and correlated outages call the incident
service, which attaches evidence to an active incident for the same category and
primary entity. Notifications are aggregated at incident scope and deduplicated
per incident/channel. Dashboard delivery is local; external channel adapters
remain queued until an approved provider is configured.

Phases 17-20 expose read-only NOC, topology-impact, capacity, and trend views.
Capacity evaluation uses sustained samples and configurable thresholds. Trend
projection uses ordinary least-squares and always returns its assumptions; it is
presented as an estimate. The frontend continues to communicate only with the
backend API and never with infrastructure management interfaces.

Phases 21-32 add operational workflows around the same service and repository
boundaries. Field technicians see only tasks assigned to them. Historical
analytics, CSV reports, and global search read existing operational records and
filter search domains by the caller's permissions. Escalation evaluation runs
on the Celery scheduler through provider-independent notification adapters.

Maintenance windows are resolved before incident creation. Expected failures
are labeled as maintenance-related, and dependency-aware suppression attaches
downstream effects to an existing upstream incident. Application and collector
network separation remains intact; host publications remain loopback-only.
Production database roles are provisioned idempotently before migrations so
existing volumes receive the restricted backup role. The opt-in, non-root
backup image encrypts dumps with a key supplied outside source control.

Phases 33-41 add a deterministic synthetic network and scale harness, permanent
correlation regression scenarios, in-process API timing, worker heartbeats, and
an authenticated Platform Health view. Observability reads operational database
and Redis state but does not communicate with ISP infrastructure.

Database backups use encrypted PostgreSQL custom-format dumps. Restore tooling
refuses the source database and defaults to a disposable verification database.
Configuration backups encrypt deployment files, including the ignored runtime
environment file. The production Compose override places a hardened Nginx TLS
reverse proxy on the edge network and removes direct application publications.
