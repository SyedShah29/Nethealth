\# NetHealth Codex Instructions



This repository contains an ISP network monitoring,

assurance, outage-correlation and incident-management platform.



\## Mandatory startup procedure



Before making ANY code changes:



1\. Read this file completely.

2\. Read `docs/MASTER\_PLAN.md`.

3\. Read `docs/DECISIONS.md`.

4\. Read `docs/PROGRESS.md`.

5\. Read all documentation relevant to the requested task.

6\. Inspect the current implementation before modifying it.



\## Source of truth



`docs/MASTER\_PLAN.md` contains the approved complete project plan.



Do not silently change the project plan.



\## Decision changes



If implementation deviates from the approved plan, architecture,

technology stack, database design, security rules, or API design,

a new entry MUST be added to:



`docs/DECISIONS.md`



before the changed implementation is considered complete.



Never delete old decisions.



If a decision is reversed, create a new decision referencing the old one.



\## Scope control



Implement ONLY the phase or task explicitly requested.



Do not:

\- begin future phases

\- add unrelated features

\- perform unrelated refactoring

\- redesign the application without approval



\## Architecture



Read `docs/ARCHITECTURE.md` before architectural changes.



The frontend must NEVER communicate directly with:

\- routers

\- switches

\- OLTs

\- ONUs

\- ISP infrastructure management interfaces



Only collector services may communicate with ISP infrastructure.



Vendor-specific networking code must be isolated inside vendor adapters.



\## No LLM



This project does NOT use an LLM.



Do not add:

\- OpenAI APIs

\- local LLMs

\- generative AI

\- chatbot functionality

\- natural-language querying



unless explicitly requested by the user.



\## Network safety



The application is read-only toward ISP infrastructure by default.



Do not implement router, switch, OLT, ONU, or other network

configuration capabilities unless explicitly approved.



\## Security



Read `docs/SECURITY.md`.



Never:

\- hardcode credentials

\- commit secrets

\- log credentials

\- expose credentials to the frontend

\- expose network secrets in APIs

\- collect unnecessary customer PII



\## Customer privacy



Do not require:

\- CNIC

\- payment details

\- banking information

\- browsing history

\- DNS history

\- home address



Use internal subscriber IDs whenever possible.



\## Database



Every schema change requires a migration.



Do not manually mutate production database schemas.



\## Testing



Read `docs/TESTING.md`.



Every task must have appropriate tests.



Run relevant tests before reporting completion.



Never claim tests passed unless they were actually executed.



\## Documentation



Update documentation whenever:

\- behavior changes

\- architecture changes

\- APIs change

\- schemas change

\- security behavior changes



\## Progress



Update:



`docs/PROGRESS.md`



after completing planned work.



\## Definition of Done



A task is complete only when:



\- implementation is complete

\- error handling is present

\- tests are added

\- tests pass

\- type checking passes

\- linting passes

\- documentation is updated

\- migrations exist if required

\- DECISIONS.md is updated if needed

\- PROGRESS.md is updated

\- no secrets were introduced



\## Required completion report



At the end of every task report:



1\. What was implemented

2\. Files created

3\. Files modified

4\. Database migrations

5\. Tests added

6\. Tests executed and results

7\. Documentation updated

8\. Decisions added

9\. Unresolved issues

10\. Next task according to MASTER\_PLAN.md

