from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr


class VendorBase(BaseModel):
    organization_id: int
    name: str
    contact_name: Optional[str] = None
    contact_email: Optional[EmailStr] = None
    contact_phone: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorRead(VendorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
