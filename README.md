# NetHealth

NetHealth is an ISP network monitoring, assurance, outage-correlation, and
incident-management platform. The current implementation contains the Phase 0
foundation and Phase 1 authentication and access control.

## Local development

Requirements:

- Docker Desktop with Docker Compose
- Node.js 22 for frontend checks outside Docker
- Python 3.12 for backend checks outside Docker

Copy `.env.example` to `.env` and replace every `CHANGE_ME` value with a
different, randomly generated secret. Never commit `.env`.

Start the stack:

```text
docker compose up --build
```

Host access is deliberately limited to:

- frontend: `http://127.0.0.1:3000`
- backend API: `http://127.0.0.1:8000`

PostgreSQL/TimescaleDB and Redis have no host-published ports. They are
reachable only by services on the private Docker network. Use `docker compose
exec postgres psql` for local database administration rather than publishing
the database port.

## Verification

Backend, from `backend/`:

```text
python -m pytest
python -m ruff check .
python -m mypy app
alembic upgrade head --sql
```

Frontend, from `frontend/`:

```text
npm test
npm run lint
npm run typecheck
npm run build
npm audit
```

See `docs/MASTER_PLAN.md` for approved scope and `docs/SECURITY.md` for the
mandatory local network-exposure rules.

## First administrator

After migrations complete, create the first administrator from an interactive
terminal. The password is prompted securely and is never passed as a command
argument:

```text
docker compose exec backend python -m app.cli.create_admin \
  --name "NetHealth Administrator" --email "admin@example.com"
```

The bootstrap command stops working after an active administrator exists.
Additional users must then be created through the authenticated `/api/users`
API. Never place an administrator password in `.env`, Compose, shell history,
or documentation.
