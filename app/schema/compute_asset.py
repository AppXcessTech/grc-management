from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class ComputeAssetBase(BaseModel):
    name: str
    asset_type: str
    status: Optional[str] = "Active"
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    owner_id: Optional[int] = None
    provisioned_date: Optional[datetime] = None

    @field_validator("provisioned_date", mode="before")
    @classmethod
    def coerce_to_aware(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        if isinstance(v, str):
            if v == "":
                return None
            dt = datetime.fromisoformat(v)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return v


class ComputeAssetCreate(ComputeAssetBase):
    pass


class ComputeAssetUpdate(BaseModel):
    name: Optional[str] = None
    asset_type: Optional[str] = None
    status: Optional[str] = None
    hostname: Optional[str] = None
    operating_system: Optional[str] = None
    owner_id: Optional[int] = None
    provisioned_date: Optional[datetime] = None

    @field_validator("provisioned_date", mode="before")
    @classmethod
    def coerce_to_aware(cls, v):
        if v is None:
            return None
        if isinstance(v, datetime):
            if v.tzinfo is None:
                return v.replace(tzinfo=timezone.utc)
            return v
        if isinstance(v, str):
            if v == "":
                return None
            dt = datetime.fromisoformat(v)
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt
        return v


class ComputeAssetRead(ComputeAssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None


class ComputeAssetDetail(ComputeAssetRead):
    owner_name: Optional[str] = None
