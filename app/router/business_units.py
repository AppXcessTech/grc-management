from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep
from app.models.organization import Organization
from app.models.business_unit import BusinessUnit
from app.schema.business_unit import BusinessUnitCreate, BusinessUnitRead, BusinessUnitUpdate

router = APIRouter(prefix="/api/organizations/{org_slug}/bunits", tags=["business-units"])

async def get_org_id(org_slug: str, db: AsyncSession) -> int:
    result = await db.execute(select(Organization.id).where(Organization.slug == org_slug))
    org_id = result.scalar_one_or_none()
    if org_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org_id

@router.post("", response_model=BusinessUnitRead, status_code=status.HTTP_201_CREATED)
async def create_business_unit(
    org_slug: str,
    payload: BusinessUnitCreate,
    current_user: CurrentSuperAdminDep,
    db: AsyncSession = Depends(get_db)
):
    org_id = await get_org_id(org_slug, db)
    bu = BusinessUnit(**payload.model_dump(), organization_id=org_id)
    db.add(bu)
    await db.commit()
    await db.refresh(bu)
    return bu

@router.get("", response_model=List[BusinessUnitRead])
async def list_business_units(org_slug: str, current_user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(select(BusinessUnit).where(BusinessUnit.organization_id == org_id))
    return result.scalars().all()

@router.get("/{bu_id}", response_model=BusinessUnitRead)
async def get_business_unit(org_slug: str, bu_id: int, current_user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(BusinessUnit).where(BusinessUnit.id == bu_id, BusinessUnit.organization_id == org_id)
    )
    bu = result.scalar_one_or_none()
    if bu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business Unit not found")
    return bu

@router.patch("/{bu_id}", response_model=BusinessUnitRead)
async def update_business_unit(
    org_slug: str,
    bu_id: int,
    payload: BusinessUnitUpdate,
    current_user: CurrentSuperAdminDep,
    db: AsyncSession = Depends(get_db)
):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(BusinessUnit).where(BusinessUnit.id == bu_id, BusinessUnit.organization_id == org_id)
    )
    bu = result.scalar_one_or_none()
    if bu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business Unit not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(bu, key, value)
    await db.commit()
    await db.refresh(bu)
    return bu

@router.delete("/{bu_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_business_unit(org_slug: str, bu_id: int, current_user: CurrentSuperAdminDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(BusinessUnit).where(BusinessUnit.id == bu_id, BusinessUnit.organization_id == org_id)
    )
    bu = result.scalar_one_or_none()
    if bu is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Business Unit not found")
    await db.delete(bu)
    await db.commit()
    return None