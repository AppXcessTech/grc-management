from typing import List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, DBSessionDep
from app.models.asset_owner import AssetOwner
from app.schema.asset_owner import AssetOwnerCreate


class AssetOwnerRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    asset_id: int
    user_id: Optional[int] = None


router = APIRouter(prefix="/api/asset-owners", tags=["asset-owners"])


@router.post("/", response_model=AssetOwnerRead, status_code=status.HTTP_201_CREATED)
async def create_owner(payload: AssetOwnerCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> AssetOwner:
    owner = AssetOwner(**payload.model_dump())
    db.add(owner)
    await db.commit()
    await db.refresh(owner)
    return owner


@router.get("/", response_model=List[AssetOwnerRead])
async def list_owners(current_user: CurrentUserDep, db: DBSessionDep) -> List[AssetOwner]:
    result = await db.execute(
        select(AssetOwner)
        .options(selectinload(AssetOwner.user))
    )
    return result.scalars().all()


@router.get("/{owner_id}", response_model=AssetOwnerRead)
async def get_owner(owner_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> AssetOwner:
    result = await db.execute(
        select(AssetOwner)
        .where(AssetOwner.id == owner_id)
        .options(selectinload(AssetOwner.user))
    )
    owner = result.scalar_one_or_none()
    if owner is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Owner not found")
    return owner
