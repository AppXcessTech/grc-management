from typing import Optional

from pydantic import BaseModel


class AssetTagCreate(BaseModel):
    key: str
    value: Optional[str] = None
