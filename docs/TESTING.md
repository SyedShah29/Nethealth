\# NetHealth Testing Requirements



No feature is complete without tests.



\## Backend



Test:



\- API endpoints

\- services

\- repositories

\- authentication

\- permissions

\- rule engine

\- correlation

\- collectors

\- anomaly detection



Use pytest.



\## Frontend



Run:



\- lint

\- type checking

\- component tests



\## Database changes



Test migrations.

For Phase 4 metrics changes, also verify the live TimescaleDB hypertable,
continuous aggregates, refresh policies, retention policies, and application
role read access. Unit tests must cover collector-to-metric normalization,
counter-derived rates and utilization, entity types, and time-window validation.

For Phase 5 subscriber changes, test pseudonymous identifier validation,
external-reference mapping, IP/MAC normalization, session duration and time
ordering, database constraints, not-found behavior, authorized access, and
unauthenticated rejection. Tests must also confirm prohibited customer PII is
absent from the response schema.

For Phase 6 fiber changes, test hierarchy integrity, PON capacity constraints,
ONU-to-PON/OLT consistency, threshold boundary validation, all four optical
classifications, vendor/technology/model selection, history window
downsampling, threshold audit events, authorized access, and unauthenticated
rejection. Run Alembic's global drift check after applying migrations.

For Phase 7, test upstream/downstream traversal, lowest common ancestors,
disconnected graphs, cycle/self-edge protection, failure impact, interface
dependencies, UI interaction, and status text/icons in addition to color.

For Phase 8, test every condition operator, all trigger states, duration
handling, the four initial operational rules, persisted evidence, RBAC, and
audited configuration changes.

For Phases 9 and 10, permanently test PON, OLT, and core outage correlation,
window rejection, all confidence levels, subscriber-specific optical faults,
congestion, evidence and recommended checks, and `UNDETERMINED` behavior when
facts are insufficient. Run the global Alembic drift check after migrations.

For Phases 11-20, test configurable health scoring and its component
explanation; every initial anomaly method and required evidence; Customer 360
sections and deterministic diagnosis; incident deduplication, transitions, and
timeline; incident-level notification routing and deduplication; NOC widgets;
all topology filters and impact counts; sustained configurable capacity
thresholds; and statistical projection assumptions. Test protected routes for
unauthenticated rejection and run the global Alembic drift check.



\## Collector changes



Every collector must test:



\- success

\- timeout

\- authentication failure

\- malformed response

\- device unavailable



\## Correlation



Permanent regression tests must exist for:



\- PON outage

\- OLT outage

\- core outage

\- subscriber-specific fault

\- congestion



\## Security



Test both:



\- authorized requests

\- unauthorized requests

For Phases 21-32, test assignment-scoped field workflows, ordered transitions,
bounded photo validation, permission-filtered search, analytics and CSV exports,
escalation timing/deduplication, maintenance labeling, dependency-aware incident
attachment, credential-reference redaction, production database TLS enforcement,
and migration drift.

For Phases 33-41, run all four approved synthetic subscriber scales and the
5,000-disconnect storm; test every simulator failure; retain the four exact
correlation regression scenarios; test status text in addition to color;
protect the platform-health API; build the production frontend; validate the
TLS proxy configuration; and complete encrypted database and configuration
backup tests plus an actual guarded database restore.

Phases 42-45 require evidence from the approved pilot network, authoritative
router/OLT/RADIUS/tool comparisons, every staged expansion gate, and operator
acceptance. Simulator or unit-test output must not be substituted for that
evidence.

