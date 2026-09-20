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

