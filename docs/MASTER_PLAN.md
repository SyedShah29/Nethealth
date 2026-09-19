\# NetHealth Master Plan



Status: APPROVED



This file contains the complete approved project plan.



This file represents what the application is intended to become.



Do not silently rewrite requirements here to match implementation.



If implementation deviates from this plan, record the deviation in:



`docs/DECISIONS.md`



\---



\# 1. Project Name



NetHealth



\---



\# 2. Project Purpose



NetHealth is an independent ISP network monitoring, assurance, fault-correlation, incident-management, diagnostics, and capacity-planning platform.



The project is intended for a Tier-2 ISP.



The existing ISP software already handles areas such as:



\* customers

\* packages

\* pricing

\* subscriptions

\* provisioning

\* router configuration



NetHealth must NOT duplicate those functions.



NetHealth instead focuses on:



\* monitoring

\* diagnostics

\* fault detection

\* outage correlation

\* root-cause classification

\* subscriber health

\* optical monitoring

\* topology

\* incident management

\* field operations

\* alerts

\* network analytics

\* capacity planning

\* operational reporting



The primary value of NetHealth is:



> Do not simply tell the ISP that something is down. Determine what shared infrastructure is responsible, who is affected, what evidence supports that conclusion, and what the operations team should check next.



\---



\# 3. Core Design Principle



NetHealth must work without any LLM.



The platform must use:



\* deterministic rules

\* network topology

\* thresholds

\* statistics

\* time-series analysis

\* anomaly detection

\* historical baselines

\* correlation algorithms



The system must never invent diagnoses.



All conclusions must be explainable.



\---



\# 4. No LLM Requirement



The application must not use:



\* OpenAI APIs

\* ChatGPT APIs

\* local LLMs

\* generative AI

\* chatbot functionality

\* natural-language querying

\* LLM-generated troubleshooting



All displayed diagnoses must be derived from actual data and known rules.



\---



\# 5. Read-Only Infrastructure Requirement



NetHealth is primarily a monitoring and assurance platform.



Collectors may:



\* read SNMP data

\* ping devices

\* read router APIs

\* read OLT APIs

\* read RADIUS data

\* receive syslog

\* read interface counters

\* read ONU information

\* collect telemetry



NetHealth must NOT:



\* modify router configurations

\* modify OLT configurations

\* create VLANs

\* change subscriber profiles

\* modify routing

\* modify BGP

\* restart infrastructure devices

\* issue destructive commands



unless the user explicitly changes this requirement and the change is recorded in `docs/DECISIONS.md`.



\---



\# 6. Privacy Principle



NetHealth should collect only data required for network operations.



The platform should primarily use pseudonymous subscriber IDs.



Example:



```text

SUB-10482

```



instead of customer identity.



NetHealth does not require:



\* customer CNIC

\* banking details

\* payment details

\* credit/debit card information

\* browsing history

\* DNS history

\* websites visited

\* customer home address



unless a future formally approved requirement changes this scope.



\---



\# 7. Sensitive Data Principle



Network credentials must be treated as highly sensitive.



Sensitive values include:



\* router usernames/passwords

\* switch credentials

\* OLT credentials

\* SNMP credentials

\* RADIUS secrets

\* API tokens

\* database passwords

\* encryption keys

\* VPN keys



These must never:



\* appear in frontend code

\* be logged

\* be returned through normal APIs

\* be committed to Git

\* be exposed to support users

\* be stored as plaintext where avoidable



\---



\# 8. Project Technology Stack



\## Backend



Use:



\* Python 3.12

\* FastAPI

\* Pydantic

\* SQLAlchemy

\* Alembic



\---



\## Frontend



Use:



\* Next.js

\* React

\* TypeScript



Use TypeScript strict mode.



\---



\## Database



Use:



\* PostgreSQL

\* TimescaleDB extension



PostgreSQL stores operational data.



TimescaleDB stores time-series metrics.



\---



\## Cache / Queue



Use:



\* Redis



\---



\## Background Tasks



Use:



\* Celery



unless a documented decision changes this.



\---



\## Deployment



Initial deployment:



\* Linux server

\* Docker

\* Docker Compose

\* Nginx or equivalent reverse proxy

\* PostgreSQL

\* TimescaleDB

\* Redis

\* Backend

\* Workers

\* Frontend



Architecture must allow later scaling to multiple servers.



\---



\# 9. High-Level Architecture



```text

&#x20;                  ISP NETWORK

&#x20;                      │

&#x20;      ┌───────────────┼─────────────────┐

&#x20;      │               │                 │

&#x20;   Routers           OLTs            RADIUS

&#x20;      │               │                 │

&#x20;      └───────────────┼─────────────────┘

&#x20;                      │

&#x20;               COLLECTOR LAYER

&#x20;                      │

&#x20;              NORMALIZATION

&#x20;                      │

&#x20;         ┌────────────┴────────────┐

&#x20;         │                         │

&#x20;  Operational Database       Time-Series Database

&#x20;         │                         │

&#x20;         └────────────┬────────────┘

&#x20;                      │

&#x20;             Analysis Services

&#x20;                      │

&#x20;      ┌───────────────┼────────────────┐

&#x20;      │               │                │

&#x20;   Rule Engine     Topology         Anomaly

&#x20;                   Correlation      Detection

&#x20;      │               │                │

&#x20;      └───────────────┼────────────────┘

&#x20;                      │

&#x20;                Incident Engine

&#x20;                      │

&#x20;               Notification Engine

&#x20;                      │

&#x20;                 Backend API

&#x20;                      │

&#x20;                   Frontend

```



\---



\# 10. Repository Structure



The project should use:



```text

NetHealth/

│

├── AGENTS.md

├── README.md

├── .gitignore

├── .env.example

├── docker-compose.yml

│

├── docs/

│   ├── MASTER\_PLAN.md

│   ├── DECISIONS.md

│   ├── PROGRESS.md

│   ├── ARCHITECTURE.md

│   ├── SECURITY.md

│   ├── CODING\_STANDARDS.md

│   ├── TESTING.md

│   ├── DATA\_MODEL.md

│   └── API.md

│

├── backend/

├── frontend/

├── collectors/

├── simulator/

├── tests/

├── scripts/

└── docker/

```



\---



\# 11. Backend Structure



Recommended:



```text

backend/

└── app/

&#x20;   ├── api/

&#x20;   ├── core/

&#x20;   ├── models/

&#x20;   ├── schemas/

&#x20;   ├── services/

&#x20;   ├── repositories/

&#x20;   ├── rules/

&#x20;   ├── correlation/

&#x20;   ├── anomalies/

&#x20;   ├── incidents/

&#x20;   ├── notifications/

&#x20;   └── security/

```



\---



\# 12. Collector Structure



Recommended:



```text

collectors/

├── core/

├── vendors/

│   ├── generic\_snmp/

│   ├── mikrotik/

│   ├── huawei/

│   ├── zte/

│   └── cisco/

└── tests/

```



Vendor-specific logic must stay inside vendor adapters.



\---



\# PHASE 0 — PROJECT FOUNDATION



\## Objective



Create the production-quality foundation before implementing ISP features.



\---



\## Tasks



\### 0.1 Repository Structure



Create the complete repository layout.



\---



\### 0.2 Backend Skeleton



Create FastAPI backend.



Requirements:



\* application factory or clean startup structure

\* versioned API routing

\* configuration module

\* database integration

\* logging

\* health checks



\---



\### 0.3 Frontend Skeleton



Create Next.js TypeScript frontend.



Requirements:



\* TypeScript strict mode

\* application layout

\* API layer

\* shared UI structure

\* routing foundation



\---



\### 0.4 PostgreSQL Setup



Configure PostgreSQL.



\---



\### 0.5 TimescaleDB Setup



Enable TimescaleDB extension.



\---



\### 0.6 Redis Setup



Configure Redis.



\---



\### 0.7 Docker Compose



Docker Compose must run:



\* backend

\* frontend

\* PostgreSQL

\* TimescaleDB

\* Redis

\* worker where appropriate



\---



\### 0.8 Environment Configuration



Create safe environment configuration.



Never hardcode secrets.



Use `.env.example`.



\---



\### 0.9 Structured Logging



Every backend log should support fields such as:



\* timestamp

\* level

\* service

\* event

\* entity

\* device ID where relevant

\* subscriber ID where relevant

\* incident ID where relevant

\* message



Never log secrets.



\---



\### 0.10 Standardized Error Handling



Example:



```json

{

&#x20; "error": {

&#x20;   "code": "DEVICE\_NOT\_FOUND",

&#x20;   "message": "Requested device does not exist."

&#x20; }

}

```



\---



\### 0.11 Health Endpoints



Implement:



```text

/api/health

/api/health/database

/api/health/redis

```



\---



\### 0.12 Testing Foundation



Configure:



\* pytest

\* backend unit tests

\* backend API tests

\* frontend linting

\* frontend type checking

\* frontend test framework



\---



\## Phase 0 Exit Criteria



Do not proceed unless:



\* backend starts

\* frontend starts

\* PostgreSQL connects

\* TimescaleDB works

\* Redis connects

\* Docker environment works

\* migrations work

\* tests execute

\* linting executes

\* type checking executes



\---



\# PHASE 1 — AUTHENTICATION AND ACCESS CONTROL



\## Objective



Secure access to NetHealth.



\---



\## 1.1 User Model



Fields:



```text

id

name

email

password\_hash

role

active

created\_at

updated\_at

last\_login

```



\---



\## 1.2 Initial Roles



```text

ADMIN

NOC\_ENGINEER

SUPPORT

FIELD\_TECHNICIAN

VIEWER

```



\---



\## 1.3 ADMIN



Can:



\* manage users

\* manage roles

\* manage devices

\* manage thresholds

\* manage collectors

\* manage rules

\* manage notifications

\* view all operational data



\---



\## 1.4 NOC\_ENGINEER



Can:



\* view topology

\* view devices

\* view metrics

\* view subscribers

\* manage incidents

\* acknowledge incidents

\* investigate incidents

\* access diagnostics

\* manage operational rules where permitted



\---



\## 1.5 SUPPORT



Can:



\* search subscribers

\* view customer diagnostics

\* view current incidents

\* view subscriber health



Must not access infrastructure credentials.



\---



\## 1.6 FIELD\_TECHNICIAN



Can:



\* view assigned jobs

\* view relevant diagnostics

\* update task status

\* upload notes/photos



\---



\## 1.7 VIEWER



Read-only dashboards.



\---



\## 1.8 Authentication



Implement:



\* secure password hashing

\* login

\* logout

\* session/token expiration

\* failed-login protection

\* account disabling



\---



\## 1.9 Authorization



Every protected endpoint must enforce permissions.



\---



\## 1.10 Audit Trail



Audit:



\* login

\* logout

\* failed login

\* role change

\* user creation

\* user disabling

\* configuration changes

\* threshold changes

\* incident actions



\---



\# PHASE 2 — NETWORK INVENTORY



\## Objective



Build the authoritative inventory of ISP infrastructure.



\---



\## 2.1 Supported Device Types



```text

CORE\_ROUTER

EDGE\_ROUTER

BNG

BRAS

AGGREGATION\_SWITCH

ACCESS\_SWITCH

OLT

OTHER

```



\---



\## 2.2 Device Model



Fields:



```text

id

name

hostname

management\_ip

device\_type

vendor

model

site\_id

monitoring\_enabled

collector\_profile\_id

status

created\_at

updated\_at

```



\---



\## 2.3 Site Model



Represent locations such as:



\* POP

\* exchange

\* office

\* OLT site

\* distribution site



Fields:



```text

id

name

code

region

latitude optional

longitude optional

description

```



\---



\## 2.4 Interface Model



Store:



```text

device\_id

name

description

speed

mac\_address

admin\_status

oper\_status

```



\---



\## 2.5 Inventory API



Implement CRUD for:



\* sites

\* devices

\* interfaces

\* collector assignments



\---



\## 2.6 Inventory UI



Create:



\* device list

\* search

\* filters

\* device detail page

\* interface list

\* site grouping

\* monitoring state



\---



\# PHASE 3 — COLLECTOR FRAMEWORK



\## Objective



Build a modular collector system.



\---



\## 3.1 Common Collector Contract



Conceptual example:



```python

class DeviceCollector:

&#x20;   test\_connection()

&#x20;   collect\_device\_health()

&#x20;   collect\_interfaces()

&#x20;   collect\_optical\_metrics()

&#x20;   collect\_subscriber\_sessions()

&#x20;   collect\_environment()

```



\---



\## 3.2 SNMP Collector



Prefer SNMPv3.



Allow SNMPv2 only where equipment requires it.



Collect:



\* uptime

\* CPU

\* memory

\* interfaces

\* traffic counters

\* errors

\* discards

\* temperature

\* power status where supported

\* fan status where supported



\---



\## 3.3 ICMP Collector



Collect:



\* reachability

\* latency

\* packet loss



Do not mark a device offline after one failed ping.



Use configurable failure thresholds.



\---



\## 3.4 Syslog Receiver



Normalize syslog into:



```text

device

timestamp

facility

severity

message

event\_type

```



\---



\## 3.5 Vendor Adapter Architecture



Vendor-specific code must live in:



```text

collectors/vendors/

```



Examples:



```text

mikrotik/

huawei/

zte/

cisco/

generic\_snmp/

```



Adapters must normalize vendor responses into shared internal schemas.



\---



\## 3.6 Scheduler



Configurable polling intervals.



Example defaults:



```text

reachability        30 sec

device health       60 sec

interfaces          60 sec

optical metrics     2-5 min

inventory refresh   30 min

```



\---



\## 3.7 Collector Failure Handling



Collectors must safely handle:



\* timeout

\* authentication failure

\* connection failure

\* malformed response

\* unsupported metric

\* unavailable device



A collector failure must not crash the entire worker.



\---



\## 3.8 Collector Status Monitoring



Track:



\* last successful poll

\* last failed poll

\* failure count

\* latency

\* current health

\* current worker



\---



\# PHASE 4 — METRICS PLATFORM



\## Objective



Store and query time-series operational data.



\---



\## 4.1 Metric Schema



Common format:



```text

timestamp

entity\_type

entity\_id

metric\_name

value

unit

source

tags

```



\---



\## 4.2 Device Metrics



Collect:



\* CPU percentage

\* memory percentage

\* temperature

\* uptime

\* reachability

\* latency

\* packet loss



\---



\## 4.3 Interface Metrics



Collect:



\* inbound bps

\* outbound bps

\* utilization %

\* errors

\* discards

\* operational state



\---



\## 4.4 ONU Metrics



Collect where available:



\* RX optical power

\* TX optical power

\* temperature

\* voltage

\* online/offline

\* distance



\---



\## 4.5 Subscriber Metrics



Collect:



\* session state

\* session uptime

\* download rate

\* upload rate

\* disconnect events



\---



\## 4.6 Downsampling



Support:



\* raw metrics

\* 5-minute aggregates

\* hourly aggregates

\* daily aggregates



\---



\## 4.7 Retention



Starting policy:



```text

raw             30 days

5-minute        180 days

hourly          2 years

daily           long-term

```



Must be configurable.



\---



\# PHASE 5 — SUBSCRIBER OPERATIONAL MODEL



\## Objective



Represent ISP subscribers without unnecessary PII.



\---



\## 5.1 Subscriber Model



Recommended fields:



```text

subscriber\_id

external\_reference

package\_speed

status

nas\_id

olt\_id

pon\_id

onu\_id

current\_ip optional

mac\_address optional

created\_at

updated\_at

```



\---



\## 5.2 External Mapping



Allow optional mapping:



```text

Existing ISP Customer ID

&#x20;       ↓

NetHealth Subscriber ID

```



NetHealth should remain independently operational.



\---



\## 5.3 Subscriber Session Model



Store:



```text

subscriber\_id

session\_start

session\_end

nas

ip\_address

disconnect\_reason

duration

```



\---



\# PHASE 6 — OLT / PON / ONU MODEL



\## Objective



Accurately model the fiber access network.



\---



\## 6.1 OLT Structure



```text

OLT

&#x20;└── Frame

&#x20;     └── Slot

&#x20;          └── PON

&#x20;               └── ONU

```



\---



\## 6.2 OLT Model



Store:



\* device relation

\* vendor

\* model

\* frame count

\* slot information

\* uplinks



\---



\## 6.3 PON Model



Store:



```text

id

olt\_id

frame

slot

port

status

subscriber\_count

configured\_capacity

```



\---



\## 6.4 ONU Model



Store:



```text

id

onu\_identifier

serial\_number

olt\_id

pon\_id

subscriber\_id

status

last\_seen

registration\_status

rx\_power

tx\_power

temperature

distance optional

```



\---



\## 6.5 Optical Thresholds



Must be configurable by:



\* vendor

\* technology

\* device model where necessary



Classifications:



```text

GOOD

WARNING

CRITICAL

UNKNOWN

```



Do not hardcode one threshold globally.



\---



\## 6.6 Optical History



Display:



\* current

\* 24 hours

\* 7 days

\* 30 days



\---



\# PHASE 7 — TOPOLOGY ENGINE



\## Objective



Represent dependency relationships across the ISP.



\---



\## 7.1 Topology Node Types



Examples:



```text

TRANSIT

CORE

BNG

BRAS

AGGREGATION

ACCESS

OLT

PON

ONU

SUBSCRIBER

```



\---



\## 7.2 Topology Edge Model



Example:



```text

CORE-01

&#x20;  ↓

AGG-02

&#x20;  ↓

OLT-04

&#x20;  ↓

PON-7

&#x20;  ↓

ONU-38

&#x20;  ↓

SUB-13921

```



\---



\## 7.3 Required Dependency Queries



The system must answer programmatically:



\* which subscribers depend on this PON?

\* which OLT serves this subscriber?

\* which upstream device serves this OLT?

\* what common infrastructure serves these offline subscribers?

\* what devices exist downstream from this interface?

\* what impact would this device failure have?



\---



\## 7.4 Topology Visualization



Create interactive topology UI.



Status representation:



```text

GREEN   healthy

YELLOW  warning

RED     critical

GRAY    unknown/unreachable

```



Also include icons/text so color is not the only indicator.



\---



\# PHASE 8 — RULE ENGINE



\## Objective



Create deterministic operational intelligence.



\---



\## 8.1 Rule Model



Rules should be configurable.



Fields:



```text

name

description

entity\_type

conditions

duration

severity

incident\_category

recommendation

enabled

```



\---



\## 8.2 Congestion Rule



Example:



```text

interface utilization > 90%

for 10 minutes

AND

packet loss > 1%

```



Result:



```text

CATEGORY: CONGESTION

SEVERITY: HIGH

```



\---



\## 8.3 Optical Rule



Example:



```text

ONU RX crosses configured critical threshold

```



Result:



```text

OPTICAL\_SIGNAL\_CRITICAL

```



\---



\## 8.4 Device Failure Rule



Example:



```text

ICMP fails N times

AND

SNMP fails

```



Result:



```text

DEVICE\_UNREACHABLE

```



\---



\## 8.5 Subscriber Instability Rule



Example:



```text

disconnect\_count > configured threshold

within configured time

```



Result:



```text

UNSTABLE\_SUBSCRIBER

```



\---



\## 8.6 Rule Evaluation History



Store:



\* rule ID

\* entity

\* evaluation time

\* result

\* evidence

\* trigger state



\---



\# PHASE 9 — OUTAGE CORRELATION ENGINE



\## Objective



Turn many individual faults into one meaningful infrastructure incident.



\---



\## Example



Instead of:



```text

SUB-1 OFFLINE

SUB-2 OFFLINE

SUB-3 OFFLINE

...

SUB-135 OFFLINE

```



The engine determines:



```text

128 of these subscribers share OLT-04 / PON-7.

```



Create:



```text

PON OUTAGE



OLT: OLT-04

PON: 7

Affected Subscribers: 128

```



\---



\## 9.1 Correlation Dimensions



Use:



\* time

\* OLT

\* PON

\* access switch

\* aggregation switch

\* uplink

\* router

\* site

\* common upstream dependency



\---



\## 9.2 Correlation Window



Configurable.



Example:



```text

30-120 seconds

```



\---



\## 9.3 Common Ancestor Logic



For affected entities:



1\. determine each network path

2\. identify shared topology ancestors

3\. check health of shared components

4\. determine lowest common failing dependency

5\. classify incident

6\. attach downstream failures



\---



\## 9.4 Confidence Levels



Use:



```text

LOW

MEDIUM

HIGH

CONFIRMED

```



Confidence must derive from evidence.



Do not invent arbitrary AI-like percentages.



\---



\## 9.5 Example High Confidence



```text

139/142 affected users share PON-3

OLT reachable

other PONs healthy

PON-3 interface down

```



Result:



```text

HIGH confidence PON-level outage

```



\---



\# PHASE 10 — ROOT CAUSE CLASSIFICATION



\## Objective



Classify likely fault type using evidence.



\---



\## Example 1



Evidence:



```text

OLT reachable

PON down

other PONs healthy

many subscribers offline

```



Result:



```text

PON\_LEVEL\_OUTAGE

```



\---



\## Example 2



Evidence:



```text

router reachable

uplink utilization 98%

latency increasing

packet loss increasing

```



Result:



```text

LINK\_CONGESTION

```



\---



\## Example 3



Evidence:



```text

one subscriber offline

neighbors healthy

ONU optical signal degraded before disconnect

```



Result:



```text

SUBSCRIBER\_OPTICAL\_FAULT

```



\---



\## Root Cause Output



Every classification must show:



```text

classification

severity

evidence

affected entities

recommended checks

```



Example:



```text

Classification:

PON\_LEVEL\_OUTAGE



Evidence:

\- OLT reachable

\- PON 7 down

\- 118 subscribers disconnected

\- Other PONs healthy



Recommended Checks:

1\. Check PON interface.

2\. Check feeder fiber.

3\. Check splitter/distribution path.

```



\---



\# PHASE 11 — SUBSCRIBER HEALTH SCORING



\## Objective



Give each subscriber an explainable health score.



Range:



```text

0-100

```



\---



\## 11.1 Initial Components



Example weights:



```text

Optical health           25%

Packet loss              20%

Latency                  15%

Disconnect frequency     20%

Session stability        10%

Bandwidth performance    10%

```



Weights must be configurable.



\---



\## 11.2 Health Categories



Example:



```text

90-100 HEALTHY

75-89  GOOD

50-74  WARNING

0-49   CRITICAL

```



Thresholds must be configurable.



\---



\## 11.3 Explainability



The UI must show why the score is what it is.



Example:



```text

Health: 62/100



Optical:          12/25

Packet Loss:      15/20

Latency:          13/15

Disconnects:       8/20

Session Stability: 7/10

Bandwidth:         7/10

```



\---



\# PHASE 12 — CUSTOMER 360 DIAGNOSTICS



\## Objective



Create one screen for support/NOC to investigate a subscriber.



\---



\## 12.1 Identity



Show:



\* subscriber ID

\* external reference if permitted

\* package speed

\* current status



\---



\## 12.2 Session



Show:



\* NAS

\* IP

\* session uptime

\* last connection

\* last disconnect



\---



\## 12.3 Fiber



Show:



\* OLT

\* PON

\* ONU

\* RX

\* TX



\---



\## 12.4 Performance



Show:



\* latency

\* packet loss

\* current traffic

\* historical traffic



\---



\## 12.5 Stability



Show:



\* disconnects today

\* disconnects last 7 days

\* average session duration



\---



\## 12.6 Incidents



Show:



\* active incident

\* incident severity

\* incident scope

\* incident status



\---



\## 12.7 Diagnosis



Example:



```text

STATUS: CUSTOMER-SPECIFIC ISSUE



Evidence:

\- Core healthy

\- OLT healthy

\- PON healthy

\- Neighboring ONUs healthy

\- Customer RX degraded



Recommended Action:

Inspect drop fiber and connector.

```



\---



\# PHASE 13 — ANOMALY DETECTION



\## Objective



Detect unusual behavior compared to historical baselines.



\---



\## 13.1 Initial Methods



Prefer explainable techniques:



\* rolling average

\* rolling standard deviation

\* z-score

\* EWMA

\* rate-of-change detection

\* baseline comparison

\* seasonal comparison



\---



\## 13.2 Advanced Methods



May later include:



\* Isolation Forest



only where justified.



\---



\## 13.3 Optical Degradation



Example:



```text

Day 1   -18.3

Day 4   -19.1

Day 8   -21.0

Day 12  -23.8

```



Generate:



```text

OPTICAL DEGRADATION WARNING

```



\---



\## 13.4 Traffic Anomalies



Detect unusual:



\* interface utilization

\* packet loss

\* latency

\* disconnect frequency

\* CPU

\* memory



\---



\## 13.5 Explainability



Every anomaly must show:



```text

current value

historical baseline

difference

threshold

duration

```



\---



\# PHASE 14 — INCIDENT MANAGEMENT



\## Objective



Convert detected problems into operational incidents.



\---



\## 14.1 Incident Fields



```text

incident\_id

category

severity

status

title

description

first\_seen

last\_seen

resolved\_at

root\_cause

primary\_entity

affected\_subscribers

affected\_topology

evidence

recommendations

assigned\_team

assigned\_user

comments

timeline

```



\---



\## 14.2 Incident States



```text

OPEN

ACKNOWLEDGED

INVESTIGATING

RESOLVED

CLOSED

```



\---



\## 14.3 Automatic Incident Creation



Rules and correlation engine may automatically create incidents.



\---



\## 14.4 Duplicate Prevention



If an existing incident already explains the problem, attach new events to it.



Do not create duplicate incidents.



\---



\# PHASE 15 — INCIDENT TIMELINE



\## Objective



Maintain complete operational history.



Example:



```text

14:03:01 Packet loss rises

14:03:16 First ONU disconnects

14:03:24 34 ONUs offline

14:03:41 118 ONUs offline

14:03:43 Incident created

14:05:18 Technician assigned

14:31:12 PON restored

14:31:48 107 ONUs online

14:33:22 All expected ONUs restored

14:35:00 Incident resolved

```



Every significant incident change must become a timeline event.



\---



\# PHASE 16 — ALERTING SYSTEM



\## Objective



Notify correct teams without alert spam.



\---



\## 16.1 Notification Channels



Architect adapters for:



\* email

\* SMS

\* WhatsApp

\* Telegram

\* dashboard

\* web push



Actual implementation depends on available services.



\---



\## 16.2 Alert Routing



Example:



```text

Core outage

→ NOC + network engineering



PON outage

→ NOC + fiber team



Subscriber optical issue

→ support/field team



Capacity warning

→ network planning

```



\---



\## 16.3 Deduplication



Do not send:



```text

128 subscriber offline alerts

```



when one PON incident explains them.



Send:



```text

Critical PON Outage

OLT-04 / PON-7

128 subscribers affected

```



\---



\# PHASE 17 — NOC DASHBOARD



\## Objective



Provide immediate operational status.



\---



\## 17.1 Summary



Example:



```text

NETWORK STATUS

─────────────────────────

Devices          264

Healthy          249

Warning           11

Critical           4



Subscribers     18,492

Online          18,137

Offline            355



Active Incidents

Critical            2

High                4

Medium              7

```



\---



\## 17.2 Widgets



Include:



\* active incidents

\* device health

\* OLT status

\* PON status

\* subscriber health distribution

\* top congested links

\* highest packet-loss links

\* unstable subscribers

\* optical warnings

\* recent outages



\---



\# PHASE 18 — NETWORK TOPOLOGY DASHBOARD



\## Objective



Visualize network dependencies.



\---



\## Filters



Support:



\* site

\* device type

\* severity

\* vendor

\* region



\---



\## Impact View



Example:



```text

Taking OLT-07 offline would affect:



1,438 subscribers

16 PONs

```



\---



\# PHASE 19 — CAPACITY MONITORING



\## Objective



Detect infrastructure nearing saturation.



Monitor:



\* uplink utilization

\* interface utilization

\* PON subscriber count

\* PON traffic

\* OLT uplink traffic

\* aggregation links

\* core interfaces



\---



\## Example Thresholds



```text

70% informational

80% warning

90% critical

```



Use sustained load, not one-second spikes.



Thresholds must be configurable.



\---



\# PHASE 20 — CAPACITY TRENDING



\## Objective



Analyze growth over time.



Example:



```text

April       4.8 Gbps

May         5.3 Gbps

June        5.9 Gbps

July        6.5 Gbps

August      7.1 Gbps

September   7.7 Gbps

```



Use statistical trends.



Display projected threshold crossing.



Example:



```text

Based on the current 90-day trend,

this interface may cross 80% peak utilization around December.

```



Show assumptions.



Do not present predictions as certainty.



\---



\# PHASE 21 — FIELD TECHNICIAN MODULE



\## Objective



Provide operational workflows for field staff.



\---



\## 21.1 Technician Ticket View



Show:



\* incident

\* subscriber

\* OLT

\* PON

\* ONU

\* last RX

\* current status

\* recommended checks

\* assigned technician



\---



\## 21.2 Actions



Allow:



\* accept

\* start work

\* add notes

\* upload photo

\* mark restored

\* close task



\---



\## 21.3 Access Control



Technicians must not receive unnecessary core network access.



\---



\# PHASE 22 — HISTORICAL ANALYTICS



\## Objective



Provide long-term operational reporting.



Include:



\* outages by month

\* outages by site

\* outages by OLT

\* outages by PON

\* mean time to detect

\* mean time to acknowledge

\* mean time to repair

\* repeat incidents

\* unstable subscribers

\* optical degradation

\* congestion

\* device availability



\---



\# PHASE 23 — REPORTING



\## Objective



Generate operational reports.



Reports:



\* Daily Network Summary

\* Weekly Reliability Report

\* Monthly Incident Report

\* Capacity Report

\* OLT Health Report

\* Subscriber Stability Report



Export initially:



\* CSV



PDF may be added later if required.



\---



\# PHASE 24 — GLOBAL SEARCH



\## Objective



Provide fast operational search.



Support:



\* subscriber ID

\* IP

\* MAC

\* ONU serial

\* OLT

\* PON

\* device

\* hostname

\* incident

\* site



Search results must respect permissions.



\---



\# PHASE 25 — NOTIFICATION ESCALATION



\## Objective



Escalate unacknowledged critical incidents.



Example:



```text

Critical Incident Created

&#x20;       ↓

NOC Notified

&#x20;       ↓

Not acknowledged in 5 min

&#x20;       ↓

Team Lead Notified

&#x20;       ↓

Not acknowledged in 10 min

&#x20;       ↓

Manager Notified

```



Everything must be configurable.



\---



\# PHASE 26 — MAINTENANCE WINDOWS



\## Objective



Prevent planned work from generating false incidents.



Maintenance fields:



```text

device/site

start

end

reason

created\_by

```



During maintenance:



\* suppress expected alerts

\* or mark them as maintenance-related



Example:



```text

EXPECTED / MAINTENANCE

```



\---



\# PHASE 27 — DEPENDENCY-AWARE SUPPRESSION



\## Objective



Prevent downstream alert storms.



Example:



If:



```text

CORE-02 is down

```



do not independently generate:



```text

AGG-08 DOWN

OLT-31 DOWN

OLT-32 DOWN

5000 subscribers offline

```



Primary incident:



```text

CORE-02 FAILURE

```



All downstream effects attach to that incident.



\---



\# PHASE 28 — SECURITY HARDENING



\## Objective



Prepare the platform for real ISP deployment.



\---



\## 28.1 Secrets



Never store plaintext secrets in ordinary tables.



Use:



\* encrypted secret storage

\* environment secrets

\* dedicated secrets manager if available



\---



\## 28.2 Sensitive Credentials



Protect:



\* SNMP credentials

\* router credentials

\* switch credentials

\* OLT credentials

\* RADIUS credentials

\* API credentials

\* DB passwords



\---



\## 28.3 Frontend



Frontend must never receive raw credentials.



It may receive:



```text

credential\_configured: true

```



but not actual secret values.



\---



\# PHASE 29 — NETWORK SEGMENTATION



\## Recommended Deployment



```text

Users

&#x20;  │

Frontend/API

&#x20;  │

Application Network

&#x20;  │

Collector Services

&#x20;  │

Management Network

&#x20;  │

Routers / Switches / OLTs

```



Only collector services should communicate with infrastructure management addresses.



\---



\# PHASE 30 — DATABASE SECURITY



Implement:



\* least privilege

\* encrypted connections

\* backup encryption

\* restricted users

\* separate migration privileges where practical



\---



\# PHASE 31 — AUDIT LOG



Audit:



\* login

\* failed login

\* role modification

\* device addition

\* device deletion

\* threshold change

\* rule change

\* collector change

\* incident acknowledgement

\* incident closure

\* maintenance creation

\* credential replacement



Audit logs must not be editable by ordinary users.



\---



\# PHASE 32 — DATA PRIVACY ENFORCEMENT



NetHealth should primarily operate using:



```text

SUB-xxxxx

```



Do not collect:



\* CNIC

\* bank data

\* payment information

\* browser history

\* DNS history

\* websites visited



unless a documented future requirement explicitly changes scope.



Any such change requires a decision entry.



\---



\# PHASE 33 — PERFORMANCE AND SCALE TESTING



\## Objective



Ensure NetHealth works at ISP scale.



Test using synthetic datasets:



```text

1,000 subscribers

10,000 subscribers

50,000 subscribers

100,000 subscribers

```



Simulate:



\* polling

\* metrics ingestion

\* ONU data

\* subscriber reconnects

\* PON outages

\* OLT outages

\* router outages

\* congestion

\* alert storms



\---



\## Critical Scenario



Simulate:



```text

5,000 subscribers disconnect within 30 seconds

```



System must:



\* ingest events

\* remain responsive

\* correlate failures

\* avoid generating 5,000 incidents

\* identify shared dependencies



\---



\# PHASE 34 — SYNTHETIC NETWORK SIMULATOR



\## Objective



Allow development without production infrastructure.



Simulate:



```text

20 OLTs

320 PONs

10,000 ONUs

10,000 subscribers

20 switches

4 core routers

```



Generate:



\* CPU

\* memory

\* traffic

\* latency

\* packet loss

\* optical levels

\* disconnects

\* outages

\* congestion



\---



\# PHASE 35 — FAILURE SIMULATION



Simulator must allow manual triggering of:



\* ONU failure

\* PON failure

\* OLT failure

\* access switch failure

\* aggregation failure

\* core failure

\* congestion

\* optical degradation

\* packet loss

\* latency spike



Expected diagnosis must be testable.



\---



\# PHASE 36 — AUTOMATED TEST SUITE



Required categories:



\* unit tests

\* integration tests

\* API tests

\* collector tests

\* rule tests

\* correlation tests

\* security tests

\* authorization tests

\* database tests

\* frontend tests

\* end-to-end tests



\---



\# PHASE 37 — CORRELATION REGRESSION TESTS



\## Scenario A



Input:



```text

100 users offline

98 share PON-4

PON-4 down

OLT online

```



Expected:



```text

PON outage

```



\---



\## Scenario B



Input:



```text

600 users offline

all behind OLT-3

OLT unreachable

```



Expected:



```text

OLT outage

```



\---



\## Scenario C



Input:



```text

one user offline

neighbors healthy

ONU RX degraded

```



Expected:



```text

subscriber optical fault

```



\---



\## Scenario D



Input:



```text

latency high across multiple paths

shared core interface utilization 98%

```



Expected:



```text

core congestion

```



\---



\# PHASE 38 — FRONTEND UX POLISH



Use consistent status language.



Example:



```text

green  = healthy

yellow = warning

red    = critical

gray   = unknown

```



Do not rely only on color.



Use:



\* labels

\* icons

\* accessible text



\---



\# PHASE 39 — PLATFORM OBSERVABILITY



NetHealth must monitor itself.



Track:



\* collector health

\* worker status

\* queue depth

\* database latency

\* API response time

\* failed polls

\* metrics ingestion rate

\* disk usage

\* database size

\* notification failures



Create a:



```text

Platform Health

```



dashboard.



\---



\# PHASE 40 — BACKUPS AND DISASTER RECOVERY



Implement:



\* database backups

\* configuration backups

\* backup encryption

\* restore scripts

\* restore testing



A backup that has never been successfully restored is not considered validated.



\---



\# PHASE 41 — PRODUCTION DEPLOYMENT



Deploy on:



\* Linux

\* Docker

\* Docker Compose

\* PostgreSQL

\* TimescaleDB

\* Redis

\* backend

\* workers

\* frontend

\* reverse proxy

\* TLS



\---



\# PHASE 42 — PILOT NETWORK



Do not connect the entire ISP immediately.



Start with:



```text

1 router

1 OLT

1-2 PONs

small subscriber group

```



Validate the complete pipeline.



\---



\# PHASE 43 — REAL DATA VALIDATION



Compare NetHealth data against:



\* router CLI

\* OLT CLI

\* existing monitoring tools

\* RADIUS

\* known outage history



Investigate discrepancies.



Do not simply adjust thresholds to hide incorrect behavior.



\---



\# PHASE 44 — GRADUAL PRODUCTION EXPANSION



Expand:



```text

Pilot

&#x20; ↓

One POP

&#x20; ↓

Several POPs

&#x20; ↓

One Region

&#x20; ↓

Full Network

```



Monitor:



\* collector load

\* DB growth

\* queue depth

\* API performance

\* alert volume



\---



\# PHASE 45 — FINAL OPERATIONAL ACCEPTANCE



Before the project is considered complete, verify all major capabilities.



\---



\## Monitoring



\* routers

\* switches

\* OLTs

\* PONs

\* ONUs

\* subscribers



\---



\## Metrics



\* latency

\* packet loss

\* CPU

\* RAM

\* traffic

\* optical levels

\* session data



\---



\## Intelligence



\* thresholds

\* anomaly detection

\* topology correlation

\* root-cause classification

\* subscriber health scoring



\---



\## Operations



\* incidents

\* alerts

\* escalation

\* technician tasks

\* maintenance windows



\---



\## Analytics



\* outage history

\* reliability

\* capacity

\* subscriber stability

\* optical degradation



\---



\## Security



\* RBAC

\* audit logs

\* secret protection

\* encryption

\* network segmentation



\---



\## Platform Reliability



\* backups

\* restore test

\* platform monitoring

\* load testing

\* scalability testing



\---



\# 46. Final Application Navigation



Recommended:



```text

Dashboard



Network

&#x20;├── Topology

&#x20;├── Devices

&#x20;├── Interfaces

&#x20;├── Sites

&#x20;├── OLTs

&#x20;└── PONs



Subscribers

&#x20;├── All Subscribers

&#x20;├── Health

&#x20;├── Unstable

&#x20;└── Optical Warnings



Incidents

&#x20;├── Active

&#x20;├── History

&#x20;└── Maintenance



Capacity

&#x20;├── Links

&#x20;├── OLTs

&#x20;├── PONs

&#x20;└── Trends



Analytics

&#x20;├── Reliability

&#x20;├── Outages

&#x20;├── Performance

&#x20;└── Capacity



Field Operations

&#x20;├── Tasks

&#x20;└── Technicians



Alerts



Administration

&#x20;├── Users

&#x20;├── Roles

&#x20;├── Devices

&#x20;├── Collector Profiles

&#x20;├── Thresholds

&#x20;├── Rules

&#x20;├── Notifications

&#x20;└── Audit Log



System

&#x20;├── Collector Health

&#x20;├── Worker Health

&#x20;├── Database Health

&#x20;└── Platform Metrics

```



\---



\# 47. Major Data Model



At minimum:



```text

User

Role

Permission



Site

Device

Interface



OLT

PON

ONU



Subscriber

SubscriberSession



TopologyNode

TopologyEdge



MetricDefinition

MetricSample



Rule

RuleCondition



Alert



Incident

IncidentEvent

IncidentAffectedEntity



MaintenanceWindow



Technician

TechnicianTask



NotificationChannel

NotificationRule



AuditLog



CollectorProfile

CollectorStatus

```



\---



\# 48. Planned API Groups



```text

/api/auth

/api/users

/api/sites

/api/devices

/api/interfaces

/api/olts

/api/pons

/api/onus

/api/subscribers

/api/topology

/api/metrics

/api/incidents

/api/alerts

/api/rules

/api/anomalies

/api/capacity

/api/technicians

/api/maintenance

/api/reports

/api/admin

/api/system

```



\---



\# 49. Non-Negotiable Engineering Rules



\## Rule 1



No LLM.



\---



\## Rule 2



No hidden automatic network configuration.



\---



\## Rule 3



No arbitrary diagnosis.



Every diagnosis must include evidence.



\---



\## Rule 4



Never expose infrastructure credentials to the frontend.



\---



\## Rule 5



Never log passwords, API tokens, SNMP secrets, or infrastructure credentials.



\---



\## Rule 6



Do not collect unnecessary customer PII.



\---



\## Rule 7



Vendor-specific integrations must use vendor adapters.



\---



\## Rule 8



Correlate outages instead of creating duplicate incidents.



\---



\## Rule 9



Significant operator actions must be auditable.



\---



\## Rule 10



Any deviation from this plan must be recorded in:



```text

docs/DECISIONS.md

```



\---



\# 50. Mandatory Decision Logging



Every implementation decision that changes this plan must be recorded.



The decision entry must contain:



\* decision ID

\* date

\* phase

\* task

\* original plan

\* new decision

\* reason

\* alternatives considered

\* architecture impact

\* database impact

\* API impact

\* frontend impact

\* security impact

\* performance impact

\* deployment impact

\* affected files

\* migration requirements

\* status



Never delete decision history.



If a decision is reversed, create a new decision referencing the previous one.



\---



\# 51. Definition of Done



A task is not complete merely because code exists.



Every task must satisfy:



```text

\[ ] Implementation complete

\[ ] Error handling complete

\[ ] Unit tests added

\[ ] Integration tests added where required

\[ ] Tests pass

\[ ] Type checking passes

\[ ] Linting passes

\[ ] Security reviewed

\[ ] Documentation updated

\[ ] API documentation updated where required

\[ ] Database migration created where required

\[ ] DECISIONS.md updated if plan changed

\[ ] PROGRESS.md updated

\[ ] No secrets committed

```



\---



\# 52. Codex Working Method



Codex must work one phase or bounded task at a time.



Before each task:



1\. Read `AGENTS.md`.

2\. Read `docs/MASTER\_PLAN.md`.

3\. Read `docs/DECISIONS.md`.

4\. Read `docs/PROGRESS.md`.

5\. Read task-relevant documentation.

6\. Inspect current implementation.

7\. Implement only the requested scope.

8\. Add/update tests.

9\. Run tests.

10\. Update documentation.

11\. Update progress.

12\. Record deviations.



\---



\# 53. Codex Must Not Skip Ahead



Do not give Codex:



```text

Build NetHealth.

```



Instead give:



```text

Implement Phase 3 tasks 3.1 through 3.3 only.



Do not begin Task 3.4 or any later phase.

```



This is mandatory project management practice for NetHealth.



\---



\# 54. Required Codex Completion Report



At the end of every task, Codex must report:



1\. What was implemented

2\. Files created

3\. Files modified

4\. Database migrations created

5\. Tests added

6\. Tests executed

7\. Test results

8\. Documentation updated

9\. Decisions added

10\. Unresolved issues

11\. Next planned task



\---



\# 55. Synthetic Development Requirement



Before connecting NetHealth to the production ISP network, the project must support synthetic development data.



The simulator must be usable for:



\* UI development

\* rules

\* topology

\* incidents

\* correlation

\* health scoring

\* anomaly detection

\* load testing



Real infrastructure credentials should not be required for ordinary development.



\---



\# 56. Production Credential Requirement



Production credentials must only be introduced during approved integration phases.



Credentials should be provided through secure configuration mechanisms.



Credentials must never be embedded in:



\* code

\* commits

\* test fixtures

\* documentation

\* frontend bundles



\---



\# 57. Root Cause Philosophy



NetHealth must prioritize:



```text

Evidence

&#x20;  ↓

Correlation

&#x20;  ↓

Classification

&#x20;  ↓

Recommendation

```



not:



```text

Guess

&#x20;  ↓

Alert

```



Every displayed operational conclusion must be traceable.



\---



\# 58. Example Final Incident



```text

INCIDENT #2317



Severity:

CRITICAL



Classification:

PON\_LEVEL\_OUTAGE



OLT:

OLT-07



PON:

0/3/4



Affected Subscribers:

139



First Seen:

14:08:21



Evidence:

\- OLT responds normally

\- PON operational state is DOWN

\- 139 subscribers disconnected in 41 seconds

\- 136 of those subscribers share the same PON

\- Other PONs on the same OLT remain healthy



Recommended Checks:

1\. Verify PON port state

2\. Inspect feeder fiber

3\. Inspect splitter path

4\. Check recent maintenance/activity



Confidence:

HIGH

```



This is the type of deterministic operational output the system should ultimately produce.



\---



\# 59. Project Completion Goal



The completed NetHealth platform must continuously transform raw ISP data:



```text

SNMP

ICMP

Router APIs

OLT APIs

RADIUS

Syslog

Interface counters

ONU statistics

```



into useful operational intelligence:



```text

Network health

Subscriber health

Outage detection

Root-cause classification

Topology impact

Optical degradation

Congestion detection

Capacity warnings

Incidents

Alerts

Technician tasks

Historical analytics

Operational reports

```



without requiring an LLM and without unnecessarily collecting personally identifiable customer data.



\---



\# 60. Final Project Principle



NetHealth should not merely answer:



> Is something down?



It should answer:



> What is wrong?



> Where is it wrong?



> What network dependency is responsible?



> Who is affected?



> What evidence proves it?



> Is it one customer or a shared network fault?



> How severe is it?



> What should the operations team inspect next?



That is the final intended capability of NetHealth.



