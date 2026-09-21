\# NetHealth Security Requirements



\## Secrets



Treat as secrets:



\- router passwords

\- switch passwords

\- OLT credentials

\- SNMP credentials

\- API keys

\- RADIUS secrets

\- database passwords

\- encryption keys



Secrets must never:



\- appear in source code

\- appear in Git

\- appear in frontend code

\- appear in logs

\- appear in error responses



\## Infrastructure access



Network access is read-only unless explicitly approved.



\## Authentication



Implement RBAC.



Initial roles:



\- ADMIN

\- NOC\_ENGINEER

\- SUPPORT

\- FIELD\_TECHNICIAN

\- VIEWER

Passwords are hashed with Argon2id and are never stored or logged in plaintext.
Authentication uses cryptographically random opaque session tokens. Only token
hashes are persisted. Session cookies are HttpOnly and SameSite=Strict, are
scoped to `/api`, and use Secure in production.

Sessions expire after a configurable duration and logout revokes the server-side
session. Repeated failures lock an account for a configurable period. Login
failures use generic responses to avoid user enumeration and are serialized
with a database row lock to prevent concurrent attempts bypassing the limit.

Browser state-changing requests are checked against the configured trusted
origins. Protected endpoints enforce explicit permission codes. Disabling a
user invalidates their sessions on the next request, self-disabling is blocked,
and the final active administrator cannot be removed.



\## Customer data



Avoid storing unnecessary personal data.



Do not require:



\- CNIC

\- payment information

\- banking information

\- browsing history

\- DNS history

\- home address



Prefer internal subscriber IDs.

Phase 5 subscriber records use pseudonymous operational IDs. Optional external
references, current IP addresses, and MAC addresses are available only through
authenticated endpoints protected by `subscribers:read`. The schema does not
store customer names, CNICs, home addresses, billing/payment information,
browsing history, or DNS history. Subscriber lookup failures use a generic
not-found response and no subscriber value is written to authentication logs.

Phase 6 fiber inventory and optical diagnostics are read-only through the API
and require `operational:read`. The browser never connects to an OLT or ONU.
Only NetHealth optical threshold configuration is mutable; those operations
require `thresholds:manage`, trusted-origin validation, database constraints,
and append-only audit events. No collector credential is stored in OLT, PON,
ONU, threshold, optical-status, or optical-history records.

Phase 7 topology reads require `topology:read`; topology metadata changes use
the existing `devices:manage` capability, trusted-origin validation, cycle and
integrity checks, and audit logging. Topology attributes must never contain
credentials or customer PII. The browser receives dependency metadata only and
never contacts infrastructure management interfaces.

Phase 8 rule configuration requires `rules:manage`, trusted-origin validation,
and audit logging. Rule conditions use fixed operators and cannot contain or
execute code. Evaluation evidence contains normalized operational signals only,
never credentials.

Phase 9 correlation reads require `incidents:read`; explicit evaluation requires
`incidents:manage`. Phase 10 assessment access requires `diagnostics:read`.
Both engines are deterministic, operate on stored topology and supplied facts,
and create no outbound network traffic. State-changing browser requests remain
subject to trusted-origin checks.

Phases 11-20 preserve the same RBAC and trusted-origin boundaries. Health and
anomaly evaluation, incident changes, notification configuration, and capacity
configuration require explicit management permissions and are never exposed to
anonymous callers. Threshold, notification, and incident changes create audit
or incident-timeline records as applicable.

Notification channels store only a configuration-key reference, never provider
credentials. External email, SMS, WhatsApp, Telegram, and web-push adapters do
not transmit until a provider is separately approved and configured. Customer
360 exposes only the existing privacy-minimized operational subscriber record.
No frontend route communicates directly with a router, switch, OLT, ONU, or NAS.

\## Local Development Network Exposure

Local development services that must be published to the host must bind
explicitly to `127.0.0.1`. Unspecified host bindings and bindings to
`0.0.0.0` or `::` are prohibited unless the user explicitly approves the
exposure and the decision is recorded in `docs/DECISIONS.md`.

PostgreSQL/TimescaleDB and Redis should normally remain internal-only on a
private Docker network. Do not publish their ports merely for convenience.
If temporary host database administration is explicitly required, bind only
to `127.0.0.1:5432` and remove the mapping afterward.

Docker daemon exposure is prohibited. Do not configure unauthenticated Docker
TCP sockets or mount `/var/run/docker.sock` into application containers.

Privileged containers, host networking, broad device mounts, and
`network_mode: host` require explicit user approval and a decision entry.

Normal application runtime must use a least-privilege database role rather
than the PostgreSQL bootstrap/superuser account. Database migrations use a
separate non-superuser role. Credentials must be supplied through ignored
`.env` files or secure secret injection.

Collector profiles persist only a configuration key. SNMP usernames,
communities, authentication secrets, and privacy secrets are resolved from the
ignored `COLLECTOR_PROFILES_JSON` environment value inside collector workers.
That value may also contain deployment-specific read-only vendor OID overrides.
Secrets are never placed in Celery task arguments, API responses, failure logs,
or frontend bundles. Only collector workers join the outbound collector network.

The local syslog receiver is published as UDP on `127.0.0.1` only. It logs
normalized metadata but not raw syslog message bodies, which may contain
operational or authentication details.



\## Audit logging



Audit:



\- login

\- failed login

\- user changes

\- role changes

\- rule changes

\- threshold changes

\- collector configuration

\- maintenance windows

\- incident acknowledgement

\- incident resolution

\- credential updates

