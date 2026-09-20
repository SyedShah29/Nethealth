\# NetHealth Decision Log



This file records architectural, technical and product decisions

that deviate from the original MASTER\_PLAN.md.



Never delete previous decisions.



Decision IDs must be sequential:



D-0001

D-0002

D-0003



\---



\## Decision Template



\### D-XXXX — Decision title



\*\*Date:\*\*



\*\*Phase:\*\*



\*\*Task:\*\*



\### Original Plan



What did MASTER\_PLAN.md require?



\### Decision



What was changed?



\### Reason



Why was the change necessary?



\### Alternatives Considered



1\.

2\.

3\.



\### Impact



\*\*Architecture:\*\*



\*\*Database:\*\*



\*\*API:\*\*



\*\*Frontend:\*\*



\*\*Security:\*\*



\*\*Performance:\*\*



\*\*Deployment:\*\*



\### Files Affected



\- file/path



\### Migration Required



Yes / No



If yes, explain.



\### Status



Accepted / Temporary / Reverted



\---

### D-0001 — Phase 2 collector assignment metadata boundary

Phase 2 adds lightweight collector profile and assignment tables so devices can
reference future collection configuration. These records are metadata only;
collector execution and all infrastructure communication remain deferred to
Phase 3, preserving the architecture boundary.
