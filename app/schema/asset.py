from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict

from .asset_category import AssetCategoryRead


class AssetTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    key: str
    value: Optional[str] = None


class AssetBase(BaseModel):
    category_id: int
    name: str
    description: Optional[str] = None
    source: Optional[str] = "Manual"
    external_id: Optional[str] = None
    status: Optional[str] = "Active"
    owner_id: Optional[int] = None
    department: Optional[str] = None
    criticality: Optional[str] = "Medium"
    risk_level: Optional[str] = "Medium"
    compliance_scope: Optional[dict] = None


class AssetCreate(AssetBase):
    tags: Optional[List[dict]] = None


class AssetUpdate(BaseModel):
    category_id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    source: Optional[str] = None
    external_id: Optional[str] = None
    status: Optional[str] = None
    owner_id: Optional[int] = None
    department: Optional[str] = None
    criticality: Optional[str] = None
    risk_level: Optional[str] = None
    compliance_scope: Optional[dict] = None
    tags: Optional[List[dict]] = None


class AssetRead(AssetBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    created_at: datetime
    updated_at: datetime
    discovered_at: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    category: Optional[AssetCategoryRead] = None
    owner_name: Optional[str] = None
    tags: List[AssetTagRead] = []
