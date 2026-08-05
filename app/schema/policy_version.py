from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PolicyVersionBase(BaseModel):
    version_number: int
    notes: Optional[str] = None


class PolicyVersionCreate(PolicyVersionBase):
    policy_id: int
    file_path: Optional[str] = None


class PolicyVersion(PolicyVersionBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_id: int
    file_path: Optional[str]
    created_by_id: Optional[int]
    created_at: datetime
    published_at: Optional[datetime]
