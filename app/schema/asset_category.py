from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetCategoryBase(BaseModel):
    name: str
    description: Optional[str] = None


class AssetCategoryCreate(AssetCategoryBase):
    pass


class AssetCategoryRead(AssetCategoryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime
