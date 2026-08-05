from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class EndpointDeviceBase(BaseModel):
    name: str
    asset_type: str
    status: Optional[str] = "Active"
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_to: Optional[int] = None
    department: Optional[str] = None
    acquisition_date: Optional[datetime] = None

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def coerce_to_aware(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        if isinstance(v, str):
            dt = datetime.fromisoformat(v)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return v


class EndpointDeviceCreate(EndpointDeviceBase):
    pass


class EndpointDeviceUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    status: Optional[str] = None
    manufacturer: Optional[str] = None
    model: Optional[str] = None
    serial_number: Optional[str] = None
    assigned_to: Optional[int] = None
    department: Optional[str] = None
    acquisition_date: Optional[datetime] = None

    @field_validator("acquisition_date", mode="before")
    @classmethod
    def coerce_to_aware(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        if isinstance(v, str):
            dt = datetime.fromisoformat(v)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return v


class EndpointDeviceRead(EndpointDeviceBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    mdm_device_id: Optional[str] = None
    mdm_payload: Optional[str] = None
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None


class EndpointDeviceDetail(EndpointDeviceRead):
    assigned_to_name: Optional[str] = None
