from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["healthy"]
    service: str


class DependencyHealthResponse(BaseModel):
    status: Literal["healthy"]
    dependency: Literal["database", "redis"]
    version: str | None = None
