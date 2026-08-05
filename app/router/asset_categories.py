from typing import List
from fastapi import APIRouter, HTTPException, status
from sqlalchemy import select

from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, DBSessionDep
from app.models.asset_category import AssetCategory
from app.schema.asset_category import AssetCategoryCreate, AssetCategoryRead

router = APIRouter(prefix="/api/asset-categories", tags=["asset-categories"])


@router.post("/", response_model=AssetCategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(payload: AssetCategoryCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> AssetCategory:
    category = AssetCategory(**payload.model_dump())
    db.add(category)
    await db.commit()
    await db.refresh(category)
    return category


@router.get("/", response_model=List[AssetCategoryRead])
async def list_categories(current_user: CurrentUserDep, db: DBSessionDep) -> List[AssetCategory]:
    result = await db.execute(select(AssetCategory))
    return result.scalars().all()


@router.get("/{category_id}", response_model=AssetCategoryRead)
async def get_category(category_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> AssetCategory:
    result = await db.execute(select(AssetCategory).where(AssetCategory.id == category_id))
    category = result.scalar_one_or_none()
    if category is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category
