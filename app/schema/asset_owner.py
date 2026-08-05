from typing import Optional

from pydantic import BaseModel


class AssetOwnerCreate(BaseModel):
    asset_id: int
    user_id: Optional[int] = None
