from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class PlatformRoleBase(BaseModel):
    name: str
    description: Optional[str] = None


class PlatformRoleCreate(PlatformRoleBase):
    pass


class PlatformRoleRead(PlatformRoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
