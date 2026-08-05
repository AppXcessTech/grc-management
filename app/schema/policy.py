from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict

from app.models.enums import PolicyCategory, PolicyStatus


class PolicyBase(BaseModel):
    name: str
    description: Optional[str] = None
    category: PolicyCategory = PolicyCategory.other


class PolicyCreate(PolicyBase):
    organization_id: int


class PolicyUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    category: Optional[PolicyCategory] = None
    status: Optional[PolicyStatus] = None


from app.schema.policy_version import PolicyVersion


class Policy(PolicyBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    status: PolicyStatus
    created_at: datetime
    updated_at: datetime
    versions: List[PolicyVersion] = []
