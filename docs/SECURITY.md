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

