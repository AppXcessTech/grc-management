from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import select, func, or_
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.audit_log import AuditLog
from app.models.endpoint_device import EndpointDevice
from app.models.user import User
from app.schema.endpoint_device import (
    EndpointDeviceCreate,
    EndpointDeviceDetail,
    EndpointDeviceRead,
    EndpointDeviceUpdate,
)

router = APIRouter(prefix="/api/endpoint-devices", tags=["endpoint-devices"])


@router.get("/", response_model=List[EndpointDeviceDetail])
async def list_endpoint_devices(
    current_user: CurrentUserDep,
    db: DBSessionDep,
    search: Optional[str] = Query(None),
    asset_type: Optional[str] = Query(None),
    department: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    include_archived: bool = Query(False),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    sort_by: str = Query("name"),
    sort_order: str = Query("asc"),
):
    query = select(EndpointDevice).where(EndpointDevice.organization_id == current_user.organization_id)

    if not include_archived:
        query = query.where(EndpointDevice.archived_at.is_(None))

    if search:
        search_term = f"%{search}%"
        query = query.where(
            or_(
                EndpointDevice.name.ilike(search_term),
                EndpointDevice.manufacturer.ilike(search_term),
                EndpointDevice.model.ilike(search_term),
                EndpointDevice.serial_number.ilike(search_term),
            )
        )

    if asset_type:
        query = query.where(EndpointDevice.asset_type == asset_type)

    if department:
        query = query.where(EndpointDevice.department == department)

    if status:
        query = query.where(EndpointDevice.status == status)

    valid_sort_columns = {
        "name": EndpointDevice.name,
        "asset_type": EndpointDevice.asset_type,
        "status": EndpointDevice.status,
        "department": EndpointDevice.department,
        "assigned_to": EndpointDevice.assigned_to,
        "created_at": EndpointDevice.created_at,
        "updated_at": EndpointDevice.updated_at,
    }

    sort_column = valid_sort_columns.get(sort_by, EndpointDevice.name)
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
    devices = result.scalars().all()

    # Resolve assigned_to names
    assigned_ids = {d.assigned_to for d in devices if d.assigned_to is not None}
    user_map = {}
    if assigned_ids:
        user_result = await db.execute(
            select(User).where(User.id.in_(assigned_ids))
        )
        for u in user_result.scalars().all():
            user_map[u.id] = (u.first_name or '') + ' ' + (u.last_name or '') if u.first_name or u.last_name else u.email

    items = []
    for d in devices:
        item = EndpointDeviceDetail(
            id=d.id,
            organization_id=d.organization_id,
            name=d.name,
            asset_type=d.asset_type,
            status=d.status,
            manufacturer=d.manufacturer,
            model=d.model,
            serial_number=d.serial_number,
            assigned_to=d.assigned_to,
            department=d.department,
            acquisition_date=d.acquisition_date,
            mdm_device_id=d.mdm_device_id,
            mdm_payload=d.mdm_payload,
            created_by=d.created_by,
            created_at=d.created_at,
            updated_at=d.updated_at,
            archived_at=d.archived_at,
            assigned_to_name=user_map.get(d.assigned_to) if d.assigned_to else None,
        )
        items.append(item)

    return items


@router.get("/types", response_model=List[str])
async def get_endpoint_device_types():
    return [
        "Windows Laptop",
        "macOS Laptop",
        "Linux Workstation",
        "Desktop Computer",
        "iPhone",
        "Android Phone",
        "Tablet",
        "Rugged Device",
        "Kiosk",
        "Point-of-Sale System",
        "Meeting Room System",
        "Executive Device",
    ]


@router.get("/counts")
async def get_endpoint_device_counts(
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    org_id = current_user.organization_id
    query = select(EndpointDevice).where(EndpointDevice.organization_id == org_id)

    all_devices = await db.execute(query.where(EndpointDevice.archived_at.is_(None)))
    total = len(all_devices.scalars().all())

    active_count_query = select(func.count(EndpointDevice.id)).where(
        EndpointDevice.organization_id == org_id,
        EndpointDevice.status == "Active",
        EndpointDevice.archived_at.is_(None),
    )
    active_result = await db.execute(active_count_query)
    active = active_result.scalar() or 0

    # Count by asset_type category
    laptop_types = ["Windows Laptop", "macOS Laptop", "Linux Workstation", "Desktop Computer"]
    mobile_types = ["iPhone", "Android Phone", "Tablet", "Rugged Device"]
    specialized_types = ["Kiosk", "Point-of-Sale System", "Meeting Room System", "Executive Device"]

    async def count_by_types(type_list):
        ct = select(func.count(EndpointDevice.id)).where(
            EndpointDevice.organization_id == org_id,
            EndpointDevice.asset_type.in_(type_list),
            EndpointDevice.archived_at.is_(None),
        )
        r = await db.execute(ct)
        return r.scalar() or 0

    laptops = await count_by_types(laptop_types)
    mobile = await count_by_types(mobile_types)
    specialized = await count_by_types(specialized_types)

    return {
        "total": total,
        "active": active,
        "laptops_workstations": laptops,
        "mobile_devices": mobile,
        "specialized_devices": specialized,
    }


@router.get("/departments", response_model=List[str])
async def get_endpoint_departments(
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice.department).where(
        EndpointDevice.organization_id == current_user.organization_id,
        EndpointDevice.department.isnot(None),
        EndpointDevice.department != "",
    ).distinct().order_by(EndpointDevice.department)
    result = await db.execute(query)
    return [row[0] for row in result]


@router.get("/{device_id}", response_model=EndpointDeviceDetail)
async def get_endpoint_device(
    device_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice).where(
        EndpointDevice.id == device_id,
        EndpointDevice.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Endpoint device not found")

    assigned_name = None
    if device.assigned_to:
        u_result = await db.execute(
            select(User).where(User.id == device.assigned_to)
        )
        user = u_result.scalar_one_or_none()
        if user:
            assigned_name = (user.first_name or '') + ' ' + (user.last_name or '') if user.first_name or user.last_name else user.email

    return EndpointDeviceDetail(
        id=device.id,
        organization_id=device.organization_id,
        name=device.name,
        asset_type=device.asset_type,
        status=device.status,
        manufacturer=device.manufacturer,
        model=device.model,
        serial_number=device.serial_number,
        assigned_to=device.assigned_to,
        department=device.department,
        acquisition_date=device.acquisition_date,
        mdm_device_id=device.mdm_device_id,
        mdm_payload=device.mdm_payload,
        created_by=device.created_by,
        created_at=device.created_at,
        updated_at=device.updated_at,
        archived_at=device.archived_at,
        assigned_to_name=assigned_name,
    )


@router.post("/", response_model=EndpointDeviceRead, status_code=201)
async def create_endpoint_device(
    payload: EndpointDeviceCreate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    device_data = payload.model_dump()
    device = EndpointDevice(
        **device_data,
        organization_id=current_user.organization_id,
        created_by=current_user.id,
    )
    db.add(device)
    await db.flush()

    # Audit log
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Created",
        resource_type="endpoint_device",
        resource_id=str(device.id),
        new_values=payload.model_dump(mode="json"),
    )
    db.add(audit)
    await db.commit()
    await db.refresh(device)
    return device


@router.patch("/{device_id}", response_model=EndpointDeviceRead)
async def update_endpoint_device(
    device_id: int,
    payload: EndpointDeviceUpdate,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice).where(
        EndpointDevice.id == device_id,
        EndpointDevice.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Endpoint device not found")

    old_values = {}
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        old_val = getattr(device, field)
        if isinstance(old_val, datetime):
            old_values[field] = old_val.isoformat() if old_val else None
        else:
            old_values[field] = old_val
        setattr(device, field, value)

    device.updated_at = datetime.now(timezone.utc)
    await db.flush()

    # Audit log
    new_values = payload.model_dump(mode="json")
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Updated",
        resource_type="endpoint_device",
        resource_id=str(device.id),
        old_values=old_values,
        new_values=new_values,
    )
    db.add(audit)
    await db.commit()
    await db.refresh(device)
    return device


@router.delete("/{device_id}", status_code=204)
async def delete_endpoint_device(
    device_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice).where(
        EndpointDevice.id == device_id,
        EndpointDevice.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Endpoint device not found")

    await db.delete(device)
    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Deleted",
        resource_type="endpoint_device",
        resource_id=str(device.id),
    )
    db.add(audit)
    await db.commit()


@router.post("/{device_id}/archive", response_model=EndpointDeviceRead)
async def archive_endpoint_device(
    device_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice).where(
        EndpointDevice.id == device_id,
        EndpointDevice.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Endpoint device not found")

    old_status = device.status
    device.status = "Archived"
    device.archived_at = datetime.now(timezone.utc)
    device.updated_at = datetime.now(timezone.utc)
    await db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Archived",
        resource_type="endpoint_device",
        resource_id=str(device.id),
        old_values={"status": old_status},
        new_values={"status": "Archived", "archived_at": device.archived_at.isoformat()},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(device)
    return device


@router.post("/{device_id}/restore", response_model=EndpointDeviceRead)
async def restore_endpoint_device(
    device_id: int,
    current_user: CurrentUserDep,
    db: DBSessionDep,
):
    query = select(EndpointDevice).where(
        EndpointDevice.id == device_id,
        EndpointDevice.organization_id == current_user.organization_id,
    )
    result = await db.execute(query)
    device = result.scalar_one_or_none()

    if not device:
        raise HTTPException(status_code=404, detail="Endpoint device not found")

    device.status = "Active"
    device.archived_at = None
    device.updated_at = datetime.now(timezone.utc)
    await db.flush()

    audit = AuditLog(
        organization_id=current_user.organization_id,
        user_id=current_user.id,
        action="Asset Restored",
        resource_type="endpoint_device",
        resource_id=str(device.id),
        old_values={"status": "Archived"},
        new_values={"status": "Active", "archived_at": None},
    )
    db.add(audit)
    await db.commit()
    await db.refresh(device)
    return device
