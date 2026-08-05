from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, DBSessionDep
from app.models.vendor import Vendor
from app.schema.vendor import VendorCreate, VendorRead

router = APIRouter(prefix="/api/vendors", tags=["vendors"])


@router.post("/", response_model=VendorRead, status_code=status.HTTP_201_CREATED)
async def create_vendor(payload: VendorCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Vendor:
    vendor = Vendor(**payload.model_dump())
    db.add(vendor)
    await db.commit()
    await db.refresh(vendor)
    return vendor


@router.get("/", response_model=List[VendorRead])
async def list_vendors(current_user: CurrentUserDep, db: DBSessionDep) -> List[Vendor]:
    result = await db.execute(select(Vendor).where(Vendor.organization_id == current_user.organization_id))
    return result.scalars().all()


@router.get("/{vendor_id}", response_model=VendorRead)
async def get_vendor(vendor_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> Vendor:
    result = await db.execute(select(Vendor).where(Vendor.id == vendor_id, Vendor.organization_id == current_user.organization_id))
    vendor = result.scalar_one_or_none()
    if vendor is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Vendor not found")
    return vendor
