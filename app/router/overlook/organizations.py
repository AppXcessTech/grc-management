import secrets
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_password_hash
from app.models.organization import Organization
from app.models.user import User
from app.models.user_role import UserRole
from app.models.department import Department
from app.models.business_unit import BusinessUnit
from app.models.subsidiary import Subsidiary
from app.models.platform_audit_log import PlatformAuditLog
from app.models.enums import UserStatus
from app.models.role import Role
from app.models.enums import RoleName
from app.core.dependencies import CurrentPlatformUserDep
from pydantic import BaseModel


router = APIRouter(prefix="/organizations", tags=["overlook-organizations"])


class OverlookOrganizationUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: Optional[str] = None
    settings: Optional[dict] = None


class OverlookOrganizationCreate(BaseModel):
    name: str
    slug: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: str = "startup"
    settings: Optional[dict] = {}
    admin_email: str
    admin_first_name: Optional[str] = None
    admin_last_name: Optional[str] = None


class OrganizationCreateResponse(BaseModel):
    id: int
    name: str
    slug: str
    domain: Optional[str] = None
    industry: Optional[str] = None
    size: str
    admin_email: str
    generated_password: str


@router.post("/", response_model=OrganizationCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_organization(
    payload: OverlookOrganizationCreate,
    request: Request,
    current_user: CurrentPlatformUserDep,
    db: AsyncSession = Depends(get_db)
):
    existing_slug = await db.execute(select(Organization).where(Organization.slug == payload.slug))
    if existing_slug.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization with this slug already exists")

    existing_email = await db.execute(select(User).where(User.email == payload.admin_email))
    if existing_email.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User with this email already exists")

    org = Organization(
        name=payload.name,
        slug=payload.slug,
        domain=payload.domain,
        industry=payload.industry,
        size=payload.size,
        settings=payload.settings,
    )
    db.add(org)
    await db.flush()

    password = secrets.token_urlsafe(12)
    hashed = get_password_hash(password)

    admin = User(
        email=payload.admin_email,
        first_name=payload.admin_first_name or payload.name.split()[0],
        last_name=payload.admin_last_name or "Admin",
        organization_id=org.id,
        status=UserStatus.active,
        hashed_password=hashed,
    )
    db.add(admin)
    await db.flush()

    super_admin_role = await db.execute(select(Role).where(Role.name == RoleName.super_admin))
    super_admin = super_admin_role.scalar_one_or_none()
    if not super_admin:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Super admin role not found")
    ur = UserRole(user_id=admin.id, role_id=super_admin.id)
    db.add(ur)

    db.add(PlatformAuditLog(
        platform_user_id=current_user.id,
        action="created_organization_with_admin",
        resource_type="organization",
        resource_id=str(org.id),
        new_values={**payload.model_dump(exclude={"admin_email", "admin_first_name", "admin_last_name"})},
        ip_address=request.client.host if request.client else None,
    ))

    await db.commit()

    return OrganizationCreateResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        domain=org.domain,
        industry=org.industry,
        size=org.size,
        admin_email=admin.email,
        generated_password=password,
    )


class OrganizationStats(BaseModel):
    id: int
    name: str
    external_id: str
    user_count: int
    department_count: int
    business_unit_count: int
    subsidiary_count: int


@router.get("/", response_model=List[OrganizationStats])
async def list_organizations(
    request: Request,
    current_user: CurrentPlatformUserDep,
    db: AsyncSession = Depends(get_db)
):
    db.add(PlatformAuditLog(
        platform_user_id=current_user.id,
        action="viewed_organizations_list",
        ip_address=request.client.host if request.client else None,
    ))

    result = await db.execute(select(Organization))
    orgs = result.scalars().all()

    stats = []
    for org in orgs:
        user_count = (await db.execute(select(func.count()).select_from(User).where(User.organization_id == org.id))).scalar() or 0
        dept_count = (await db.execute(select(func.count()).select_from(Department).where(Department.organization_id == org.id))).scalar() or 0
        bu_count = (await db.execute(select(func.count()).select_from(BusinessUnit).where(BusinessUnit.organization_id == org.id))).scalar() or 0
        sub_count = (await db.execute(select(func.count()).select_from(Subsidiary).where(
            (Subsidiary.parent_organization_id == org.id) | (Subsidiary.child_organization_id == org.id)
        ))).scalar() or 0

        stats.append(OrganizationStats(
            id=org.id,
            name=org.name,
            external_id=org.external_id,
            user_count=user_count,
            department_count=dept_count,
            business_unit_count=bu_count,
            subsidiary_count=sub_count,
        ))

    return stats


@router.patch("/{org_id}", response_model=OrganizationCreateResponse)
async def update_organization(
    org_id: int,
    payload: OverlookOrganizationUpdate,
    request: Request,
    current_user: CurrentPlatformUserDep,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    if payload.slug is not None and payload.slug != org.slug:
        existing = await db.execute(select(Organization).where(Organization.slug == payload.slug))
        if existing.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Organization with this slug already exists")

    old_values = {
        "name": org.name,
        "slug": org.slug,
        "domain": org.domain,
        "industry": org.industry,
        "size": org.size,
    }

    if payload.name is not None:
        org.name = payload.name
    if payload.slug is not None:
        org.slug = payload.slug
    if payload.domain is not None:
        org.domain = payload.domain
    if payload.industry is not None:
        org.industry = payload.industry
    if payload.size is not None:
        org.size = payload.size
    if payload.settings is not None:
        org.settings = payload.settings

    db.add(PlatformAuditLog(
        platform_user_id=current_user.id,
        action="updated_organization",
        resource_type="organization",
        resource_id=str(org.id),
        old_values=old_values,
        new_values=payload.model_dump(exclude_none=True),
        ip_address=request.client.host if request.client else None,
    ))

    await db.commit()
    await db.refresh(org)

    return OrganizationCreateResponse(
        id=org.id,
        name=org.name,
        slug=org.slug,
        domain=org.domain,
        industry=org.industry,
        size=org.size,
        admin_email="",
        generated_password="",
    )


@router.delete("/{org_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_organization(
    org_id: int,
    request: Request,
    current_user: CurrentPlatformUserDep,
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(Organization).where(Organization.id == org_id))
    org = result.scalar_one_or_none()
    if not org:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")

    db.add(PlatformAuditLog(
        platform_user_id=current_user.id,
        action="deleted_organization",
        resource_type="organization",
        resource_id=str(org.id),
        old_values={"name": org.name, "slug": org.slug},
        ip_address=request.client.host if request.client else None,
    ))

    await db.delete(org)
    await db.commit()
