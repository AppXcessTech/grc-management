from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import CurrentSuperAdminDep, CurrentUserDep, DBSessionDep, PermissionRequired
from app.core.tenant import add_org_filter, get_current_org_id
from app.models.control_mapping import ControlMapping
from app.models.control import Control
from app.models.user import User
from app.schema.control_mapping import ControlMapping as ControlMappingSchema, ControlMappingCreate

router = APIRouter(prefix="/api/control-mappings", tags=["control-mappings"])


@router.post("/", response_model=ControlMappingSchema, status_code=status.HTTP_201_CREATED)
async def create_control_mapping(
    payload: ControlMappingCreate,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
) -> ControlMapping:
    # Verify the control belongs to the user's org
    ctrl = await db.execute(
        select(Control).where(Control.id == payload.control_id, Control.organization_id == current_user.organization_id)
    )
    if not ctrl.scalar_one_or_none():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Control not found")

    mapping = ControlMapping(**payload.model_dump())
    db.add(mapping)
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.get("/", response_model=List[ControlMappingSchema])
async def list_control_mappings(
    db: DBSessionDep,
    control_id: int | None = None,
    current_user: User = Depends(PermissionRequired("control", "view")),
    requirement_id: int | None = None,
) -> List[ControlMapping]:
    stmt = select(ControlMapping)
    if control_id:
        stmt = stmt.where(ControlMapping.control_id == control_id)
    if requirement_id:
        stmt = stmt.where(ControlMapping.requirement_id == requirement_id)
    result = await db.execute(stmt)
    return result.scalars().all()


@router.delete("/{mapping_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_control_mapping(
    mapping_id: int,
    current_user: CurrentSuperAdminDep,
    db: DBSessionDep,
):
    result = await db.execute(select(ControlMapping).where(ControlMapping.id == mapping_id))
    mapping = result.scalar_one_or_none()
    if mapping is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Mapping not found")
    await db.delete(mapping)
    await db.commit()
    return None
