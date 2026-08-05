from typing import Dict, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, delete
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep
from app.core.tenant import add_org_filter, get_current_org_id
from app.models.role import Role
from app.models.permission import Permission
from app.models.role_permission import RolePermission
from pydantic import BaseModel
from app.schema.role import RoleSchema, RoleCreate, RoleUpdate
from app.models.enums import PermissionAction, RoleName
from app.models.user_role import UserRole

router = APIRouter(prefix="/api/roles", tags=["roles"])


@router.post("/", response_model=RoleSchema, status_code=status.HTTP_201_CREATED)
async def create_role(payload: RoleCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    if payload.organization_id and payload.organization_id != current_user.organization_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot create roles for another organization")
    role_data = payload.model_dump()
    role_data["organization_id"] = current_user.organization_id
    role = Role(**role_data)
    db.add(role)
    await db.commit()
    await db.refresh(role)
    return role


@router.patch("/{role_id}", response_model=RoleSchema)
async def update_role(role_id: int, payload: RoleUpdate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.organization_id == current_user.organization_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(role, key, value)
    await db.commit()
    await db.refresh(role)
    return role


@router.delete("/{role_id}", status_code=status.HTTP_200_OK)
async def delete_role(role_id: int, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    result = await db.execute(
        select(Role).where(Role.id == role_id, Role.organization_id == current_user.organization_id)
    )
    role = result.scalar_one_or_none()
    if not role:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    await db.execute(delete(RolePermission).where(RolePermission.role_id == role_id))
    await db.execute(delete(UserRole).where(UserRole.role_id == role_id))
    await db.delete(role)
    await db.commit()
    return {"message": "Role deleted successfully"}


@router.get("/", response_model=List[RoleSchema])
async def list_roles(current_user: CurrentUserDep, db: DBSessionDep, org_id: int | None = None):
    query = select(Role)
    # Default to current user's org; platform admins can pass org_id to see all
    filter_org = org_id or get_current_org_id()
    if filter_org is not None:
        query = query.where((Role.organization_id == filter_org) | (Role.organization_id.is_(None)))
    else:
        query = query.where(Role.organization_id == current_user.organization_id)
    result = await db.execute(query)
    return result.scalars().all()


class PermissionSchema(BaseModel):
    id: int
    resource: str
    action: PermissionAction
    category: str | None = None
    description: str | None

    class Config:
        from_attributes = True


class PermissionCreate(BaseModel):
    resource: str
    action: PermissionAction
    category: str | None = None
    description: str | None = None


@router.post("/permissions", response_model=PermissionSchema, status_code=status.HTTP_201_CREATED)
async def create_permission(payload: PermissionCreate, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    perm = Permission(**payload.model_dump())
    db.add(perm)
    await db.commit()
    await db.refresh(perm)
    return perm


@router.get("/permissions", response_model=List[PermissionSchema])
async def list_permissions(current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(select(Permission))
    return result.scalars().all()


class RolePermissionAssign(BaseModel):
    role_id: int
    permission_id: int


class RolePermissionSync(BaseModel):
    role_id: int
    permission_ids: List[int]


async def _assert_role_in_org(role_id: int, org_id: int, db: AsyncSession) -> Role:
    result = await db.execute(
        select(Role).where(Role.id == role_id, (Role.organization_id == org_id) | (Role.organization_id.is_(None)))
    )
    role = result.scalar_one_or_none()
    if role is None and not (await db.execute(select(Role).where(Role.id == role_id))).scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Role not found")
    return role or None


@router.post("/sync-permissions", status_code=status.HTTP_200_OK)
async def sync_role_permissions(payload: RolePermissionSync, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    await _assert_role_in_org(payload.role_id, current_user.organization_id, db)
    await db.execute(delete(RolePermission).where(RolePermission.role_id == payload.role_id))
    new_assignments = [
        RolePermission(role_id=payload.role_id, permission_id=p_id)
        for p_id in payload.permission_ids
    ]
    db.add_all(new_assignments)
    await db.commit()
    return {"message": "Permissions synced successfully"}


@router.post("/assign-permission", status_code=status.HTTP_201_CREATED)
async def assign_permission_to_role(payload: RolePermissionAssign, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    await _assert_role_in_org(payload.role_id, current_user.organization_id, db)
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == payload.role_id,
            RolePermission.permission_id == payload.permission_id
        )
    )
    if result.scalar_one_or_none():
        return {"message": "Permission already assigned"}
    rp = RolePermission(role_id=payload.role_id, permission_id=payload.permission_id)
    db.add(rp)
    await db.commit()
    return {"message": "Permission assigned to role successfully"}


@router.delete("/remove-permission", status_code=status.HTTP_200_OK)
async def remove_permission_from_role(payload: RolePermissionAssign, current_user: CurrentSuperAdminDep, db: DBSessionDep):
    await _assert_role_in_org(payload.role_id, current_user.organization_id, db)
    result = await db.execute(
        select(RolePermission).where(
            RolePermission.role_id == payload.role_id,
            RolePermission.permission_id == payload.permission_id
        )
    )
    rp = result.scalar_one_or_none()
    if not rp:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Assignment not found")
    await db.delete(rp)
    await db.commit()
    return {"message": "Permission removed from role successfully"}


@router.get("/{role_id}/permissions", response_model=List[PermissionSchema])
async def list_role_permissions(role_id: int, current_user: CurrentUserDep, db: DBSessionDep):
    await _assert_role_in_org(role_id, current_user.organization_id, db)
    result = await db.execute(
        select(Permission)
        .join(RolePermission, RolePermission.permission_id == Permission.id)
        .where(RolePermission.role_id == role_id)
    )
    return result.scalars().all()


RBAC_MATRIX: List[Dict] = [
    # category, resource, action, description, roles_with_access
    # User & Organization Management
    {"category": "User & Organization Management", "resource": "organization", "action": "edit", "description": "Manage Organization Settings (departments, business units, subsidiaries)", "roles": [RoleName.super_admin]},
    {"category": "User & Organization Management", "resource": "users", "action": "create", "description": "Invite / Deactivate Users", "roles": [RoleName.super_admin]},
    {"category": "User & Organization Management", "resource": "roles", "action": "edit", "description": "Manage Roles & Permissions", "roles": [RoleName.super_admin]},
    {"category": "User & Organization Management", "resource": "users", "action": "bulk_import", "description": "Bulk Import Users", "roles": [RoleName.super_admin]},
    {"category": "User & Organization Management", "resource": "profile", "action": "view", "description": "View Own Profile", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.employee, RoleName.vendor_user, RoleName.read_only]},
    {"category": "User & Organization Management", "resource": "asset_inventory", "action": "view", "description": "View Asset Inventory", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.read_only]},
    {"category": "User & Organization Management", "resource": "asset_inventory", "action": "edit", "description": "Edit Asset Inventory", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager]},
    {"category": "User & Organization Management", "resource": "assets", "action": "delete", "description": "Delete / Archive Assets", "roles": [RoleName.super_admin, RoleName.security_manager]},
    # Asset Inventory
    {"category": "Asset Inventory", "resource": "control", "action": "view", "description": "View Controls", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.read_only]},
    {"category": "Asset Inventory", "resource": "control", "action": "edit", "description": "Edit Controls / Frameworks", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    # Compliance Frameworks
    {"category": "Compliance Frameworks", "resource": "control", "action": "map", "description": "Map Controls to Requirements", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Compliance Frameworks", "resource": "policy", "action": "view", "description": "View Policies", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.employee, RoleName.read_only]},
    {"category": "Compliance Frameworks", "resource": "policy", "action": "edit", "description": "Edit / Publish Policies", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Compliance Frameworks", "resource": "policy", "action": "approve", "description": "Approve Policy Versions", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    # Policy Management
    {"category": "Policy Management", "resource": "policy", "action": "acknowledge", "description": "Acknowledge Policies", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.employee]},
    {"category": "Policy Management", "resource": "evidence", "action": "create", "description": "Upload Evidence", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor]},
    {"category": "Policy Management", "resource": "evidence", "action": "approve", "description": "Approve / Review Evidence", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager]},
    {"category": "Policy Management", "resource": "evidence", "action": "export", "description": "Export / Download Evidence", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    # Evidence Collection
    {"category": "Evidence Collection", "resource": "evidence", "action": "configure", "description": "Configure Evidence Sources / Connectors", "roles": [RoleName.super_admin, RoleName.security_manager]},
    {"category": "Evidence Collection", "resource": "integrations", "action": "configure", "description": "Configure Cloud Integrations (AWS/Azure/GCP)", "roles": [RoleName.super_admin, RoleName.security_manager]},
    {"category": "Evidence Collection", "resource": "monitoring", "action": "view", "description": "View Security Monitoring Dashboard", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.read_only]},
    # Cloud & Security Monitoring
    {"category": "Cloud & Security Monitoring", "resource": "violations", "action": "resolve", "description": "Acknowledge / Resolve Violations", "roles": [RoleName.super_admin, RoleName.security_manager]},
    # Audit Management
    {"category": "Audit Management", "resource": "audits", "action": "plan", "description": "Plan / Schedule Audits", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Audit Management", "resource": "audits", "action": "conduct", "description": "Conduct Audit / Review Evidence", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.auditor]},
    {"category": "Audit Management", "resource": "audits", "action": "findings", "description": "Create Findings & Observations", "roles": [RoleName.super_admin, RoleName.auditor]},
    {"category": "Audit Management", "resource": "audits", "action": "remediate", "description": "Manage Remediation Plans", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager]},
    {"category": "Audit Management", "resource": "audits", "action": "close", "description": "Close Audit", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    # Risk Management
    {"category": "Risk Management", "resource": "risks", "action": "view", "description": "View Risk Register", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.read_only]},
    {"category": "Risk Management", "resource": "risks", "action": "create", "description": "Create Risks", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager]},
    {"category": "Risk Management", "resource": "risks", "action": "score", "description": "Score Risks", "roles": [RoleName.super_admin, RoleName.security_manager]},
    {"category": "Risk Management", "resource": "risks", "action": "treat", "description": "Accept / Treat Risks", "roles": [RoleName.super_admin, RoleName.security_manager]},
    # Vendor Management
    {"category": "Vendor Management", "resource": "vendors", "action": "view", "description": "View Vendor Records", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.security_manager, RoleName.auditor, RoleName.read_only]},
    {"category": "Vendor Management", "resource": "vendors", "action": "edit", "description": "Onboard / Edit Vendors", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Vendor Management", "resource": "vendors", "action": "approve", "description": "Approve Vendors", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Vendor Management", "resource": "vendors", "action": "upload_docs", "description": "Upload Vendor Documents (own vendor only)", "roles": [RoleName.super_admin, RoleName.compliance_admin, RoleName.vendor_user]},
    # Security Questionnaires
    {"category": "Security Questionnaires", "resource": "questionnaires", "action": "manage_templates", "description": "Manage Questionnaire Templates (CAIQ/SIG/Custom)", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Security Questionnaires", "resource": "questionnaires", "action": "manage_answers", "description": "Manage Answer Library / Auto-fill Responses", "roles": [RoleName.super_admin, RoleName.compliance_admin]},
    {"category": "Security Questionnaires", "resource": "questionnaires", "action": "respond", "description": "Respond to Assigned Questionnaire", "roles": [RoleName.super_admin, RoleName.vendor_user]},
]


@router.post("/seed-rbac", status_code=status.HTTP_200_OK)
async def seed_rbac(current_user: CurrentSuperAdminDep, db: DBSessionDep):
    await db.execute(delete(RolePermission))
    await db.execute(delete(Permission))

    role_map: Dict[str, int] = {}
    result = await db.execute(select(Role))
    for role in result.scalars().all():
        role_map[role.name] = role.id

    for entry in RBAC_MATRIX:
        perm = Permission(
            resource=entry["resource"],
            action=PermissionAction(entry["action"]),
            category=entry["category"],
            description=entry["description"],
        )
        db.add(perm)
        await db.flush()

        for role_name in entry["roles"]:
            role_id = role_map.get(role_name.value)
            if role_id is not None:
                db.add(RolePermission(role_id=role_id, permission_id=perm.id))

    await db.commit()
    return {"message": "RBAC matrix seeded successfully"}
