# Contributing to NetHealth

Thanks for taking the time to improve NetHealth.

## Workflow

1. Fork the repository and create a topic branch from `master`.
2. Keep changes focused: one problem per pull request.
3. Add or update tests for any behavior change.
4. Run the full check suite before opening the pull request.
5. Describe the problem, the approach, and the verification in the PR.

## Backend checks

```bash
cd backend
python -m pytest
python -m ruff check .
python -m mypy app
alembic upgrade head --sql
```

## Frontend checks

```bash
cd frontend
npm test
npm run lint
npm run typecheck
npm run build
```

## Standards

- Python 3.12, strict typing, ruff with `E,F,I,UP,B,ASYNC`.
- TypeScript strict mode; no `any` without justification.
- Every schema change ships with an Alembic migration.
- New endpoints require an explicit permission dependency.
- The frontend never talks to network infrastructure; collectors do.
- No secrets in source, tests, fixtures, logs, or documentation.
- No customer PII beyond pseudonymous operational identifiers.

## Commit messages

Use a short imperative subject line, then a body explaining the change and
its verification. Example:

```text
feat: correlate PON outages to shared fiber ancestors

Adds lowest-common-ancestor resolution and confidence tiers, persists
evidence, and opens a single incident for downstream faults.

Verified with: pytest tests/test_correlation_regressions.py
```

## Security

Report vulnerabilities privately as described in [SECURITY.md](SECURITY.md).
