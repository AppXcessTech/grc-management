from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep, DBSessionDep
from app.core.tenant import is_platform
from app.models.organization import Organization
from app.models.department import Department
from app.models.business_unit import BusinessUnit
from app.models.subsidiary import Subsidiary
from app.models.user import User
from app.models.enums import RoleName
from app.schema.organization import OrganizationCreate, OrganizationRead, OrganizationUpdate
from pydantic import BaseModel

router = APIRouter(prefix="/api/organizations", tags=["organizations"])


@router.post("/", response_model=OrganizationRead, status_code=status.HTTP_201_CREATED)
async def create_organization(payload: OrganizationCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Organization:
    result = await db.execute(select(Organization).where(Organization.slug == payload.slug))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Organization with this slug already exists")
    org = Organization(**payload.model_dump())
    db.add(org)
    await db.flush()

    subsidiary = Subsidiary(
        parent_organization_id=current_user.organization_id,
        child_organization_id=org.id,
        relationship_type="subsidiary",
    )
    db.add(subsidiary)

    await db.commit()
    await db.refresh(org)
    return org


@router.get("/", response_model=List[OrganizationRead])
async def list_organizations(current_user: CurrentUserDep, db: DBSessionDep) -> List[Organization]:
    if is_platform():
        result = await db.execute(select(Organization))
        return result.scalars().all()

    # Check if current user is a super admin in their tenant
    user = await db.execute(
        select(User).where(User.id == current_user.id).options(selectinload(User.roles))
    )
    user = user.scalar_one_or_none()
    is_super_admin = user and any(role.name == RoleName.super_admin for role in user.roles)

    if is_super_admin:
        child_org_ids = await db.execute(
            select(Subsidiary.child_organization_id).where(
                Subsidiary.parent_organization_id == current_user.organization_id
            )
        )
        child_ids = [row[0] for row in child_org_ids.fetchall()]
        org_ids = [current_user.organization_id] + child_ids
        result = await db.execute(select(Organization).where(Organization.id.in_(org_ids)))
    else:
        result = await db.execute(select(Organization).where(Organization.id == current_user.organization_id))

    return result.scalars().all()


@router.get("/{org_id}", response_model=OrganizationRead)
async def get_organization(org_id: int, current_user: CurrentUserDep, db: DBSessionDep) -> Organization:
    # Non-super-admin users can only access their own org
    if not is_platform() and org_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org


@router.patch("/{org_id}", response_model=OrganizationRead)
async def update_organization(org_id: int, payload: OrganizationUpdate, current_user: CurrentSuperAdminDep, db: DBSessionDep) -> Organization:
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(org, key, value)
    await db.commit()
    await db.refresh(org)
    return org


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(org_id: int, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if org is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    await db.delete(org)
    await db.commit()
    return None


class DepartmentCreate(BaseModel):
    organization_id: int
    parent_department_id: int | None = None
    name: str
    code: str | None = None


@router.post("/departments", status_code=status.HTTP_201_CREATED)
async def create_department(payload: DepartmentCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    dept = Department(**payload.model_dump())
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept


class BusinessUnitCreate(BaseModel):
    organization_id: int
    name: str
    description: str | None = None


@router.post("/business-units", status_code=status.HTTP_201_CREATED)
async def create_business_unit(payload: BusinessUnitCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    bu = BusinessUnit(**payload.model_dump())
    db.add(bu)
    await db.commit()
    await db.refresh(bu)
    return bu


class SubsidiaryCreate(BaseModel):
    parent_organization_id: int
    child_organization_id: int
    relationship_type: str


@router.post("/subsidiaries", status_code=status.HTTP_201_CREATED)
async def create_subsidiary(payload: SubsidiaryCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    sub = Subsidiary(**payload.model_dump())
    db.add(sub)
    await db.commit()
    await db.refresh(sub)
    return sub
