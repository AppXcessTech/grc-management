from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.asset_tag import AssetTag
from app.schema.asset_tag import AssetTagCreate


class AssetTagRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    key: str
    value: Optional[str] = None


router = APIRouter(prefix="/api/asset-tags", tags=["asset-tags"])


@router.post("/", response_model=AssetTagRead, status_code=status.HTTP_201_CREATED)
async def create_tag(payload: AssetTagCreate, db: DBSessionDep) -> AssetTag:
    tag = AssetTag(**payload.model_dump())
    db.add(tag)
    await db.commit()
    await db.refresh(tag)
    return tag


@router.get("/", response_model=List[AssetTagRead])
async def list_tags(current_user: CurrentUserDep, db: DBSessionDep) -> List[AssetTag]:
    result = await db.execute(select(AssetTag))
    return result.scalars().all()
