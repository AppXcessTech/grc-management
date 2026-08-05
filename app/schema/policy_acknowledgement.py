from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PolicyAcknowledgementCreate(BaseModel):
    policy_version_id: int


class PolicyAcknowledgement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    policy_version_id: int
    user_id: int
    acknowledged_at: datetime
