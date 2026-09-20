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
