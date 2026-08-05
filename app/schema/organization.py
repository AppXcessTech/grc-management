from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict
from app.models.enums import OrganizationSize, SubscriptionTier

class OrganizationBase(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: OrganizationSize = OrganizationSize.startup
    subscription_tier: SubscriptionTier = SubscriptionTier.starter
    settings: Optional[dict] = {}

class OrganizationCreate(OrganizationBase):
    pass

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[OrganizationSize] = None
    subscription_tier: Optional[SubscriptionTier] = None
    settings: Optional[dict] = None

class OrganizationRead(OrganizationBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    external_id: str
    created_at: datetime
    updated_at: datetime
