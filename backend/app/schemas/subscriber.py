import re
from datetime import datetime
from ipaddress import ip_address
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

SUBSCRIBER_ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._:-]{0,119}$")
MAC_ADDRESS_PATTERN = re.compile(r"^(?:[0-9A-F]{2}:){5}[0-9A-F]{2}$")


class SubscriberResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscriber_id: str
    external_reference: str | None
    package_speed: int | None
    status: str
    nas_id: str | None
    olt_id: str | None
    pon_id: str | None
    onu_id: str | None
    current_ip: str | None
    mac_address: str | None
    created_at: datetime
    updated_at: datetime


class SubscriberSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    subscriber_id: str
    session_start: datetime
    session_end: datetime | None
    nas: str
    ip_address: str | None
    disconnect_reason: str | None
    duration: int | None


class SubscriberRecord(BaseModel):
    subscriber_id: str = Field(min_length=1, max_length=120)
    external_reference: str | None = Field(default=None, max_length=255)
    package_speed: int | None = Field(default=None, ge=0)
    status: str = Field(default="UNKNOWN", min_length=1, max_length=32)
    nas_id: str | None = Field(default=None, max_length=120)
    olt_id: str | None = Field(default=None, max_length=120)
    pon_id: str | None = Field(default=None, max_length=120)
    onu_id: str | None = Field(default=None, max_length=120)
    current_ip: str | None = Field(default=None, max_length=64)
    mac_address: str | None = Field(default=None, max_length=32)

    @field_validator("subscriber_id")
    @classmethod
    def validate_subscriber_id(cls, value: str) -> str:
        normalized = value.strip()
        if not SUBSCRIBER_ID_PATTERN.fullmatch(normalized):
            raise ValueError("subscriber_id must be a pseudonymous operational identifier")
        return normalized

    @field_validator("external_reference", "nas_id", "olt_id", "pon_id", "onu_id")
    @classmethod
    def strip_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str) -> str:
        normalized = value.strip().upper()
        if not normalized:
            raise ValueError("status must not be blank")
        return normalized

    @field_validator("current_ip")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(ip_address(value.strip()))

    @field_validator("mac_address")
    @classmethod
    def validate_mac(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().replace("-", ":").upper()
        if not MAC_ADDRESS_PATTERN.fullmatch(normalized):
            raise ValueError("mac_address must contain six hexadecimal octets")
        return normalized


class SubscriberSessionRecord(BaseModel):
    subscriber_id: str = Field(min_length=1, max_length=120)
    session_start: datetime
    session_end: datetime | None = None
    nas: str = Field(min_length=1, max_length=120)
    ip_address: str | None = Field(default=None, max_length=64)
    disconnect_reason: str | None = Field(default=None, max_length=255)
    duration: int | None = Field(default=None, ge=0)

    @field_validator("subscriber_id")
    @classmethod
    def validate_subscriber_id(cls, value: str) -> str:
        normalized = value.strip()
        if not SUBSCRIBER_ID_PATTERN.fullmatch(normalized):
            raise ValueError("subscriber_id must be a pseudonymous operational identifier")
        return normalized

    @field_validator("nas")
    @classmethod
    def validate_nas(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("nas must not be blank")
        return normalized

    @field_validator("ip_address")
    @classmethod
    def validate_ip(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return str(ip_address(value.strip()))

    @model_validator(mode="after")
    def validate_times(self) -> "SubscriberSessionRecord":
        if self.session_end is not None and self.session_end < self.session_start:
            raise ValueError("session_end must not precede session_start")
        if self.session_end is not None:
            calculated = int((self.session_end - self.session_start).total_seconds())
            if self.duration is None:
                self.duration = calculated
            elif abs(self.duration - calculated) > 1:
                raise ValueError("duration must match the session time range")
        return self
