\# NetHealth Architecture



\## Core architecture



Frontend

&#x20;  |

&#x20;  v

Backend API

&#x20;  |

&#x20;  +-------------------+

&#x20;  |                   |

PostgreSQL         TimescaleDB

&#x20;  |

Analysis Services

&#x20;  |

&#x20;  +---------------------+

&#x20;  |                     |

Rule Engine       Correlation Engine

&#x20;  |

Incident Engine

&#x20;  |

Notification Engine





Collector Services

&#x20;  |

&#x20;  v

ISP Management Network

&#x20;  |

&#x20;  +-- Routers

&#x20;  +-- Switches

&#x20;  +-- OLTs

&#x20;  +-- ONUs

&#x20;  +-- RADIUS



\## Security boundary



The browser/frontend must never communicate directly with ISP

network infrastructure.



Only collector services may communicate with network devices.



Network credentials must remain within secure backend/collector

infrastructure.



\## Backend



\- Python 3.12

\- FastAPI

\- SQLAlchemy

\- Alembic

\- PostgreSQL

\- TimescaleDB

\- Redis



\## Frontend



\- Next.js

\- React

\- TypeScript



\## Workers



\- Celery

\- Redis



unless a documented decision changes this architecture.



\## Deployment



Initial deployment:



\- Linux

\- Docker

\- Docker Compose

\- reverse proxy

\- PostgreSQL/TimescaleDB

\- Redis

\- backend

\- workers

\- frontend

