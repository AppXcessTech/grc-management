from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class AssetSuggestionCreate(BaseModel):
    name: str
    description: Optional[str] = None
    category_id: int
    department: Optional[str] = None
    criticality: Optional[str] = "Medium"
    risk_level: Optional[str] = "Medium"
    owner_id: Optional[int] = None
    tags: Optional[List[dict]] = None


class AssetSuggestionReview(BaseModel):
    status: str
    review_notes: Optional[str] = None


class AssetSuggestionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    suggested_by_id: int
    suggested_data: dict
    status: str
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    suggested_by_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None
    category_name: Optional[str] = None
