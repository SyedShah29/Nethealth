from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator

from app.models.enums import RoleName


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    local, separator, domain = normalized.partition("@")
    if not separator or not local or "." not in domain or len(normalized) > 320:
        raise ValueError("Enter a valid email address.")
    return normalized


class PermissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    code: str
    description: str


class RoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    description: str
    permissions: list[PermissionResponse]


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    email: str
    role: RoleResponse
    active: bool
    created_at: datetime
    updated_at: datetime
    last_login: datetime | None


class LoginRequest(BaseModel):
    email: str
    password: SecretStr

    _normalize_email = field_validator("email")(normalize_email)


class LoginResponse(BaseModel):
    user: UserResponse
    expires_at: datetime


class UserCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    email: str
    password: SecretStr = Field(min_length=12, max_length=1024)
    role: RoleName

    _normalize_email = field_validator("email")(normalize_email)

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be blank.")
        return normalized


class UserUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    role: RoleName | None = None
    active: bool | None = None

    @field_validator("name")
    @classmethod
    def normalize_name(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("Name must not be blank.")
        return normalized


class AuditLogResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    event_type: str
    actor_user_id: UUID | None
    target_user_id: UUID | None
    success: bool
    request_id: str | None
    subject_fingerprint: str | None
    event_metadata: dict[str, object]
    occurred_at: datetime
