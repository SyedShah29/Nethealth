\# NetHealth Coding Standards



\## Backend architecture



Use:



API Layer

&#x20;  ↓

Service Layer

&#x20;  ↓

Repository Layer

&#x20;  ↓

Database



Do not place business logic directly inside API routes.



\## Python



\- use type hints

\- use Pydantic schemas

\- use SQLAlchemy

\- use Alembic migrations

\- use async operations where appropriate



\## Collectors



Vendor-specific code must live under:



collectors/vendors/<vendor>/



Generic networking code must not contain vendor-specific parsing.



\## Errors



Do not silently swallow exceptions.



Collector failures must not crash the whole worker.



\## Logging



Use structured logging.



Do not use print() for production logging.



\## Frontend



\- TypeScript strict mode

\- avoid `any`

\- reusable components

\- API logic separate from UI

\- no infrastructure credentials in frontend



\## Comments



Comments should explain why something exists.



Do not add comments that simply restate obvious code.

