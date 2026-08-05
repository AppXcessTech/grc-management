from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, DBSessionDep
from app.models.subsidiary import Subsidiary
from app.schema.subsidiary import SubsidiaryCreate, SubsidiaryRead, SubsidiaryUpdate

router = APIRouter(prefix="/api/subsidiaries", tags=["subsidiaries"])


def _org_filter(stmt, org_id):
    return stmt.where(
        or_(
            Subsidiary.parent_organization_id == org_id,
            Subsidiary.child_organization_id == org_id,
        )
    )


@router.post("/", response_model=SubsidiaryRead, status_code=status.HTTP_201_CREATED)
async def create_subsidiary(payload: SubsidiaryCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Subsidiary:
    subsidiary = Subsidiary(**payload.model_dump())
    db.add(subsidiary)
    await db.commit()
    await db.refresh(subsidiary)
    return subsidiary


@router.get("/", response_model=List[SubsidiaryRead])
async def list_subsidiaries(current_user: CurrentUserDep, db: DBSessionDep) -> List[Subsidiary]:
    stmt = _org_filter(select(Subsidiary), current_user.organization_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.get("/{sub_id}", response_model=SubsidiaryRead)
async def get_subsidiary(sub_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> Subsidiary:
    stmt = _org_filter(select(Subsidiary).where(Subsidiary.id == sub_id), current_user.organization_id)
    result = await db.execute(stmt)
    subsidiary = result.scalar_one_or_none()
    if subsidiary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subsidiary not found")
    return subsidiary


@router.patch("/{sub_id}", response_model=SubsidiaryRead)
async def update_subsidiary(sub_id: int, payload: SubsidiaryUpdate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Subsidiary:
    result = await db.execute(select(Subsidiary).where(Subsidiary.id == sub_id))
    subsidiary = result.scalar_one_or_none()
    if subsidiary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subsidiary not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subsidiary, field, value)
    await db.commit()
    await db.refresh(subsidiary)
    return subsidiary


@router.delete("/{sub_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subsidiary(sub_id: int, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> None:
    result = await db.execute(select(Subsidiary).where(Subsidiary.id == sub_id))
    subsidiary = result.scalar_one_or_none()
    if subsidiary is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Subsidiary not found")
    await db.delete(subsidiary)
    await db.commit()
