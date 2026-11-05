# Production Deployment

## Linux host

Use a maintained Linux host with Docker Engine and the Compose plugin. Store
`.env`, TLS private keys, collector secrets, notification-provider secrets, and
backup encryption keys outside Git with owner-only permissions. Set
`APP_ENV=production`, a verifying PostgreSQL TLS mode, and
`BACKEND_CORS_ORIGINS` to a JSON list containing the externally visible HTTPS
origin. Set `TLS_CERT_PATH` and `TLS_KEY_PATH` to absolute, operator-managed
host paths. The production frontend is built with the same-origin `/api/v1`
base URL so browser requests pass through the TLS reverse proxy; do not set it
to a loopback backend address in production.

Start the TLS reverse-proxy profile with certificate and key paths supplied by
the deployment environment:

```text
docker compose -f docker-compose.yml -f docker-compose.production.yml up -d --build
```

The production override removes direct backend, frontend, and syslog host
publications. Nginx is the only HTTP entry point and publishes TLS on loopback by
default for safe local validation. A production load balancer or explicitly
approved firewall/NAT rule may forward to it; do not change the repository to an
any-address binding without the required approval and decision record.
Nginx runs as non-root with a read-only root filesystem; only its dedicated
temporary filesystem is writable.

## Backups and restore

Create encrypted database and deployment-configuration backups:

```text
docker compose --profile tools run --rm backup
docker compose --profile tools run --rm config-backup
```

The latest database artifact is linked as `/backups/latest.dump.enc`. A guarded
verification restore only targets a database ending in `_restore_verify`:

```text
RESTORE_REPLACE=true docker compose --profile tools run --rm restore-verify
```

Restoring to any other database additionally requires
`ALLOW_PRODUCTION_RESTORE=true`. The script always refuses to overwrite the
configured source database. Test restores should be dropped after evidence is
recorded. Keep encryption keys separately from backup storage.

## Deployment checks

Verify migration head/drift, API/database/Redis health, worker and scheduler
heartbeats, the Platform Health dashboard, loopback-only publications, encrypted
backup/restore, TLS headers, and the absence of credentials in API responses or
logs before admitting pilot traffic.
