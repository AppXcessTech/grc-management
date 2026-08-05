from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator


class PeopleAssetBase(BaseModel):
    name: str
    email: Optional[str] = None
    asset_type: str
    department: Optional[str] = None
    job_title: Optional[str] = None
    manager: Optional[str] = None
    asset_owner: Optional[str] = None
    status: Optional[str] = "Active"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
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


class PeopleAssetCreate(PeopleAssetBase):
    pass


class PeopleAssetUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    asset_type: Optional[str] = None
    department: Optional[str] = None
    job_title: Optional[str] = None
    manager: Optional[str] = None
    asset_owner: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    description: Optional[str] = None

    @field_validator("start_date", "end_date", mode="before")
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


class PeopleAssetReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    people_asset_id: int
    reviewed_by: Optional[int] = None
    reviewed_at: datetime
    notes: Optional[str] = None


class PeopleAssetRead(PeopleAssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    created_by: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    archived_at: Optional[datetime] = None
    last_access_review: Optional[datetime] = None
    last_reviewed_by: Optional[int] = None
