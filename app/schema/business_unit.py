from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class BusinessUnitBase(BaseModel):
    name: str
    description: Optional[str] = None

class BusinessUnitCreate(BusinessUnitBase):
    pass

class BusinessUnitUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class BusinessUnitRead(BusinessUnitBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    created_at: datetime
