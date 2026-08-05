from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, EmailStr
from app.models.enums import UserStatus, SSOProvider

class UserBase(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    organization_id: int
    department_id: Optional[int] = None
    status: UserStatus = UserStatus.invited
    mfa_enabled: bool = False
    sso_provider: Optional[SSOProvider] = None

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    department_id: Optional[int] = None
    status: Optional[UserStatus] = None
    mfa_enabled: Optional[bool] = None

from app.schema.role import RoleSchema

class UserRead(UserBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    last_login_at: Optional[datetime] = None
    roles: List[RoleSchema] = []

class UserBulkImport(BaseModel):
    users: List[UserCreate]


class UserInviteResponse(UserRead):
    generated_password: str
