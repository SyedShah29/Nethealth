# Security Policy

NetHealth is an operations platform for ISP infrastructure, so security
reports are taken seriously and handled privately.

## Reporting a vulnerability

Please **do not** open a public issue for a suspected vulnerability.

Use GitHub's private vulnerability reporting:

1. Open the repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Include the affected component, a reproduction, and the impact you expect.

You will receive an acknowledgement, an assessment, and a remediation plan.
Please allow time for a fix before any public disclosure.

## Scope

In scope:

- Authentication, session handling, and authorization bypasses
- Secret exposure (API responses, logs, task payloads, container config)
- Injection into API, database, or collector paths
- Container, Compose, or reverse-proxy exposure
- Privilege escalation through role or user administration

Out of scope:

- Findings that require a compromised host or database
- Volumetric denial of service against a self-hosted deployment
- Missing hardening headers on deployments that bypass the provided proxy

## Design commitments

- Infrastructure access is read-only and restricted to collector services.
- Passwords use Argon2id; sessions are opaque tokens stored as SHA-256 hashes.
- Secrets are supplied through the environment and never returned by the API.
- Application, migration, and backup database roles are separated.
- Containers run non-root, drop capabilities, and use read-only root filesystems.
- Host ports bind to loopback; database and cache publish no host ports.

The full security model, environment rules, and deployment hardening guidance
live in [`docs/SECURITY.md`](docs/SECURITY.md).
