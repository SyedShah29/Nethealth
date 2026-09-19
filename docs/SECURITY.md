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

