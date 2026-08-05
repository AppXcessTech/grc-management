from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.models.compute_asset import ComputeAsset
from app.models.user import User
from app.schema.compute_asset import (
    ComputeAssetCreate,
    ComputeAssetDetail,
    ComputeAssetRead,
    ComputeAssetUpdate,
)

router = APIRouter(prefix="/api/compute-assets", tags=["compute-assets"])


@router.get("/", response_model=List[ComputeAssetDetail])
async def list_compute_assets(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    search: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    owner_id: Optional[int] = Query(None),
    status: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
):
    query = select(ComputeAsset).where(ComputeAsset.organization_id == current_user.organization_id)

    if not include_archived:
        query = query.where(ComputeAsset.archived_at.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                ComputeAsset.name.ilike(search_term),
                ComputeAsset.hostname.ilike(search_term),
                ComputeAsset.operating_system.ilike(search_term),
            )
        )

    if asset_type:
        query = query.where(ComputeAsset.asset_type == asset_type)

    if owner_id is not None:
        query = query.where(ComputeAsset.owner_id == owner_id)

    if status:
        query = query.where(ComputeAsset.status == status)

    valid_sort_columns = {
        "name": ComputeAsset.name,
        "asset_type": ComputeAsset.asset_type,
        "status": ComputeAsset.status,
        "hostname": ComputeAsset.hostname,
        "owner_id": ComputeAsset.owner_id,
        "created_at": ComputeAsset.created_at,
        "updated_at": ComputeAsset.updated_at,
    }

    sort_column = valid_sort_columns.get(sort_by, ComputeAsset.name)
    order_fn = sort_column.asc if sort_order == "asc" else sort_column.desc
    query = query.order_by(order_fn())

    # Count total
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Paginate
    offset = (page - 1) * page_size
    query = query.offset(offset).limit(page_size)

    result = await db.execute(query)
    assets = result.scalars().all()

    # Resolve owner names
    owner_ids = {a.owner_id for a in assets if a.owner_id is not None}
    user_map = {}
    if owner_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(owner_ids))
        )
        for u in user_result.scalars().all():
            user_map[u.id] = f"{u.first_name or ''} {u.last_name or ''}".strip() or u.email

    items = []
    for a in assets:
        item = ComputeAssetDetail(
            id=a.id,
            organization_id=a.organization_id,
            name=a.name,
            asset_type=a.asset_type,
            status=a.status,
            hostname=a.hostname,
            operating_system=a.operating_system,
            owner_id=a.owner_id,
            provisioned_date=a.provisioned_date,
            created_by=a.created_by,
            created_at=a.created_at,
            updated_at=a.updated_at,
            archived_at=a.archived_at,
            owner_name=user_map.get(a.owner_id) if a.owner_id else None,
        )
        items.append(item)

    return items


@router.get("/types", response_model=List[str])
async def get_compute_asset_types():
    return [
        "Application Server",
        "Database Server",
        "File Server",
        "Backup Server",
        "Domain Controller",
        "VMware VM",
        "Hyper-V VM",
        "Cloud VM",
        "EC2 Instance",
        "Azure Virtual Machine",
        "Google Compute Engine",
        "Container Host"
    ]


@router.get("/counts")
async def get_compute_asset_counts(
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    org_id = current_user.organization_id
    query = select(ComputeAsset).where(ComputeAsset.organization_id == org_id)

    all_assets = await db.execute(query.where(ComputeAsset.archived_at.is_(None)))
    total = len(all_assets.scalars().all())

    active_count_query = select(func.count(ComputeAsset.id)).where(
        ComputeAsset.organization_id == org_id,
        ComputeAsset.status == "Active",
        ComputeAsset.archived_at.is_(None),
    )
    active_result = await db.execute(active_count_query)
    active = active_result.scalar() or 0

    physical_types = [
        "Application Server",
        "Database Server",
        "File Server",
        "Backup Server",
        "Domain Controller"
    ]
    vm_types = [
        "VMware VM",
        "Hyper-V VM",
        "Cloud VM"
    ]
    cloud_types = [
        "EC2 Instance",
        "Azure Virtual Machine",
        "Google Compute Engine",
        "Container Host"
    ]

    async def count_by_types(type_list):
        ct = select(func.count(ComputeAsset.id)).where(
            ComputeAsset.organization_id == org_id,
            ComputeAsset.asset_type.in_(type_list),
            ComputeAsset.archived_at.is_(None),
        )
        r = await db.execute(ct)
        return r.scalar() or 0

    physical = await count_by_types(physical_types)
    vms = await count_by_types(vm_types)
    cloud = await count_by_types(cloud_types)

    return {
        "total": total,
        "active": active,
        "physical_servers": physical,
        "virtual_machines": vms,
        "cloud_compute": cloud,
    }


@router.get("/{asset_id}", response_model=ComputeAssetDetail)
async def get_compute_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(ComputeAsset).where(
        ComputeAsset.id == asset_id,
        ComputeAsset.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Compute asset not found")

    owner_name = None
    if asset.owner_id:
        u_result = await db.execute(
            select(User).where(User.id == asset.owner_id)
        )
        user = u_result.scalar_one_or_none()
        if user:
            owner_name = f"{user.first_name or ''} {user.last_name or ''}".strip() or user.email

    return ComputeAssetDetail(
        id=asset.id,
        organization_id=asset.organization_id,
        name=asset.name,
        asset_type=asset.asset_type,
        status=asset.status,
        hostname=asset.hostname,
        operating_system=asset.operating_system,
        owner_id=asset.owner_id,
        provisioned_date=asset.provisioned_date,
        created_by=asset.created_by,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        archived_at=asset.archived_at,
        owner_name=owner_name,
    )


@router.post("/", response_model=ComputeAssetRead, status_code=201)
async def create_compute_asset(
    payload: ComputeAssetCreate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    asset_data = payload.model_dump()
    asset = ComputeAsset(
        **asset_data,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
    )
    db.add(asset)
    await db.flush()

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Created",
        resource_type="compute_asset",
        resource_id=str(asset.id),
        new_values=payload.model_dump(mode="json"),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.patch("/{asset_id}", response_model=ComputeAssetRead)
async def update_compute_asset(
    asset_id: int,
    payload: ComputeAssetUpdate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(ComputeAsset).where(
        ComputeAsset.id == asset_id,
        ComputeAsset.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Compute asset not found")

    old_values = {}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_val = getattr(asset, field)
        if isinstance(old_val, datetime):
            old_values[field] = old_val.isoformat() if old_val else None
        else:
            old_values[field] = old_val
        setattr(asset, field, value)

    asset.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Audit log
    new_values = payload.model_dump(mode="json")
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Updated",
        resource_type="compute_asset",
        resource_id=str(asset.id),
        old_values=old_values,
        new_values=new_values,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.delete("/{asset_id}", status_code=204)
async def delete_compute_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(ComputeAsset).where(
        ComputeAsset.id == asset_id,
        ComputeAsset.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Compute asset not found")

    await db.delete(asset)

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Deleted",
        resource_type="compute_asset",
        resource_id=str(asset_id),
    )
    db.add(audit)
    await db.commit()


@router.post("/{asset_id}/archive", response_model=ComputeAssetRead)
async def archive_compute_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(ComputeAsset).where(
        ComputeAsset.id == asset_id,
        ComputeAsset.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Compute asset not found")

    old_status = asset.status
    asset.status = "Archived"
    asset.archived_at = datetime.now(timezone.utc)
    asset.updated_at = datetime.now(timezone.utc)
    await db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Archived",
        resource_type="compute_asset",
        resource_id=str(asset.id),
        old_values={"status": old_status},
        new_values={"status": "Archived", "archived_at": asset.archived_at.isoformat()},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(asset)
    return asset


@router.post("/{asset_id}/restore", response_model=ComputeAssetRead)
async def restore_compute_asset(
    asset_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(ComputeAsset).where(
        ComputeAsset.id == asset_id,
        ComputeAsset.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    asset = result.scalar_one_or_none()

    if not asset:
        raise HTTPException(status_code=404, detail="Compute asset not found")

    asset.status = "Active"
    asset.archived_at = None
    asset.updated_at = datetime.now(timezone.utc)
    await db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Restored",
        resource_type="compute_asset",
        resource_id=str(asset.id),
        old_values={"status": "Archived"},
        new_values={"status": "Active", "archived_at": None},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(asset)
    return asset
