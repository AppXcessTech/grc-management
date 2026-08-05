from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    user_id: int
    title: str
    message: Optional[str] = None
    notification_type: str
    reference_type: Optional[str] = None
    reference_id: Optional[int] = None
    is_read: bool
    created_at: datetime
