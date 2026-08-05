from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, ConfigDict, EmailStr


class PlatformUserBase(BaseModel):
    email: EmailStr
    full_name: str
    is_active: Optional[bool] = True


class PlatformUserCreate(PlatformUserBase):
    password: str


class PlatformUserRead(PlatformUserBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
