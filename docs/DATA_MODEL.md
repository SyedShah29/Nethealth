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

Permissions are stable action codes. Phase 1 defines `users:manage`,
`roles:read`, and `audit:read`. The `ADMIN` role receives all Phase 1
permissions. Later phases add their own permission codes when their protected
resources are implemented.

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

Sites, devices, interfaces, collector profiles, and collector assignments are
represented as authoritative metadata. Collector assignments do not execute
collectors or connect to ISP infrastructure.
