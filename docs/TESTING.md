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

