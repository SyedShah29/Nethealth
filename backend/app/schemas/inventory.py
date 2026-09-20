# ruff: noqa
from datetime import datetime
from decimal import Decimal
from ipaddress import ip_address
from uuid import UUID
from pydantic import BaseModel, ConfigDict, Field, field_validator
from app.models.enums import DeviceType

def text(value: str) -> str:
    value = value.strip()
    if not value: raise ValueError("Value must not be blank.")
    return value

class SiteBase(BaseModel):
    name: str = Field(min_length=1, max_length=120); code: str = Field(min_length=1, max_length=32); region: str = Field(min_length=1, max_length=120)
    latitude: Decimal | None = None; longitude: Decimal | None = None; description: str | None = Field(default=None, max_length=500)
    _name = field_validator("name", "region", "description")(lambda v: text(v) if v is not None else v)
    @field_validator("code")
    @classmethod
    def norm_code(cls, v: str) -> str: return text(v).upper()
class SiteCreate(SiteBase): pass
class SiteUpdate(BaseModel):
    name: str | None = None; code: str | None = None; region: str | None = None; latitude: Decimal | None = None; longitude: Decimal | None = None; description: str | None = None
    @field_validator("name", "code", "region", "description")
    @classmethod
    def clean(cls, v: str | None) -> str | None: return text(v) if v is not None else v
class SiteResponse(SiteBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; created_at: datetime; updated_at: datetime

class DeviceBase(BaseModel):
    name: str = Field(min_length=1, max_length=120); hostname: str = Field(min_length=1, max_length=255); management_ip: str; device_type: DeviceType; vendor: str | None = None; model: str | None = None; site_id: UUID; monitoring_enabled: bool = True; collector_profile_id: UUID | None = None; status: str = "UNKNOWN"
    @field_validator("name", "hostname", "device_type", "status", "vendor", "model")
    @classmethod
    def clean_text(cls, v: str | None) -> str | None: return text(v) if v is not None else v
    @field_validator("management_ip")
    @classmethod
    def valid_ip(cls, v: str) -> str: ip_address(v); return v
class DeviceCreate(DeviceBase): pass
class DeviceUpdate(BaseModel):
    name: str | None = None; hostname: str | None = None; management_ip: str | None = None; device_type: DeviceType | None = None; vendor: str | None = None; model: str | None = None; site_id: UUID | None = None; monitoring_enabled: bool | None = None; collector_profile_id: UUID | None = None; status: str | None = None
    @field_validator("management_ip")
    @classmethod
    def valid_ip(cls, v: str | None) -> str | None: ip_address(v) if v else None; return v
class DeviceResponse(DeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: UUID; created_at: datetime; updated_at: datetime

class InterfaceCreate(BaseModel):
    device_id: UUID; name: str = Field(min_length=1, max_length=120); description: str | None = None; speed: int | None = Field(default=None, ge=0); mac_address: str | None = None; admin_status: str | None = None; oper_status: str | None = None
class InterfaceUpdate(BaseModel):
    name: str | None = None; description: str | None = None; speed: int | None = Field(default=None, ge=0); mac_address: str | None = None; admin_status: str | None = None; oper_status: str | None = None
class InterfaceResponse(InterfaceCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID

class CollectorProfileCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120); description: str | None = None; enabled: bool = True; collector_type: str = Field(default="ICMP", pattern="^(ICMP|SNMP)$"); configuration_key: str | None = None; interval_seconds: int = Field(default=60, ge=1, le=86400); failure_threshold: int = Field(default=3, ge=1, le=100)
class CollectorProfileUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120); description: str | None = None; enabled: bool | None = None; collector_type: str | None = Field(default=None, pattern="^(ICMP|SNMP)$"); configuration_key: str | None = None; interval_seconds: int | None = Field(default=None, ge=1, le=86400); failure_threshold: int | None = Field(default=None, ge=1, le=100)
class CollectorProfileResponse(CollectorProfileCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
class CollectorAssignmentCreate(BaseModel):
    device_id: UUID; collector_profile_id: UUID; enabled: bool = True
class CollectorAssignmentUpdate(BaseModel):
    collector_profile_id: UUID | None = None; enabled: bool | None = None
class CollectorAssignmentResponse(CollectorAssignmentCreate):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
