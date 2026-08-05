from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class AssetImportRequestCreate(BaseModel):
    role_arn: str
    account_name: Optional[str] = None
    region: str = "us-east-1"


class AssetImportRequestReview(BaseModel):
    status: str
    review_notes: Optional[str] = None


class AssetImportRequestRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    requested_by_id: int
    role_arn: str
    account_name: Optional[str] = None
    region: str
    status: str
    reviewed_by_id: Optional[int] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    requested_by_name: Optional[str] = None
    reviewed_by_name: Optional[str] = None
