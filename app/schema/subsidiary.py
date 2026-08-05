from datetime import datetime
from pydantic import BaseModel, ConfigDict

class SubsidiaryBase(BaseModel):
    parent_organization_id: int
    child_organization_id: int
    relationship_type: str

class SubsidiaryCreate(SubsidiaryBase):
    pass

class SubsidiaryUpdate(BaseModel):
    parent_organization_id: int | None = None
    child_organization_id: int | None = None
    relationship_type: str | None = None

class SubsidiaryRead(SubsidiaryBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
