from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep, PermissionRequired
from app.models.framework import Framework
from app.models.user import User
from app.schema.framework import Framework as FrameworkSchema, FrameworkCreate, FrameworkUpdate

router = APIRouter(prefix="/api/frameworks", tags=["frameworks"])


@router.post("/", response_model=FrameworkSchema, status_code=status.HTTP_201_CREATED)
async def create_framework(
    payload: FrameworkCreate,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
) -> Framework:
    framework = Framework(**payload.model_dump())
    db.add(framework)
    await db.commit()
    await db.refresh(framework)
    return framework


@router.get("/", response_model=List[FrameworkSchema])
async def list_frameworks(
    db: DBSessionDep,
    current_user: User = Depends(PermissionRequired("control", "view")),
) -> List[Framework]:
    result = await db.execute(select(Framework))
    return result.scalars().all()


@router.get("/{framework_id}", response_model=FrameworkSchema)
async def get_framework(
    framework_id: int,
    db: DBSessionDep,
    current_user: User = Depends(PermissionRequired("control", "view")),
) -> Framework:
    result = await db.execute(select(Framework).where(Framework.id == framework_id))
    framework = result.scalar_one_or_none()
    if framework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")
    return framework


@router.patch("/{framework_id}", response_model=FrameworkSchema)
async def update_framework(
    framework_id: int,
    payload: FrameworkUpdate,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
) -> Framework:
    result = await db.execute(select(Framework).where(Framework.id == framework_id))
    framework = result.scalar_one_or_none()
    if framework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(framework, key, value)
    await db.commit()
    await db.refresh(framework)
    return framework


@router.delete("/{framework_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_framework(
    framework_id: int,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(Framework).where(Framework.id == framework_id))
    framework = result.scalar_one_or_none()
    if framework is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Framework not found")
    await db.delete(framework)
    await db.commit()
    return None
