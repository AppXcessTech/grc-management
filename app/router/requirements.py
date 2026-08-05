from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep, PermissionRequired
from app.models.requirement import Requirement
from app.models.user import User
from app.schema.requirement import Requirement as RequirementSchema, RequirementCreate, RequirementUpdate

router = APIRouter(prefix="/api/requirements", tags=["requirements"])


@router.post("/", response_model=RequirementSchema, status_code=status.HTTP_201_CREATED)
async def create_requirement(
    payload: RequirementCreate,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
) -> Requirement:
    requirement = Requirement(**payload.model_dump())
    db.add(requirement)
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.get("/", response_model=List[RequirementSchema])
async def list_requirements(
    db: DBSessionDep,
    framework_id: int | None = None,
    current_user: User = Depends(PermissionRequired("control", "view")),
) -> List[Requirement]:
    stmt = select(Requirement).order_by(Requirement.code)
    if framework_id:
        stmt = stmt.where(Requirement.framework_id == framework_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{requirement_id}", response_model=RequirementSchema)
async def get_requirement(
    requirement_id: int,
    db: DBSessionDep,
    current_user: User = Depends(PermissionRequired("control", "view")),
) -> Requirement:
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if requirement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    return requirement


@router.patch("/{requirement_id}", response_model=RequirementSchema)
async def update_requirement(
    requirement_id: int,
    payload: RequirementUpdate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
) -> Requirement:
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if requirement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(requirement, key, value)
    await db.commit()
    await db.refresh(requirement)
    return requirement


@router.delete("/{requirement_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_requirement(
    requirement_id: int,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(Requirement).where(Requirement.id == requirement_id))
    requirement = result.scalar_one_or_none()
    if requirement is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found")
    await db.delete(requirement)
    await db.commit()
    return None
