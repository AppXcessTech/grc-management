from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, CurrentSuperAdminDep
from app.models.organization import Organization
from app.models.department import Department
from app.schema.department import DepartmentCreate, DepartmentRead, DepartmentUpdate, DepartmentTree

router = APIRouter(prefix="/api/organizations/{org_slug}/departments", tags=["departments"])

async def get_org_id(org_slug: str, db: AsyncSession) -> int:
    result = await db.execute(select(Organization.id).where(Organization.slug == org_slug))
    org_id = result.scalar_one_or_none()
    if org_id is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Organization not found")
    return org_id

@router.post("", response_model=DepartmentRead, status_code=status.HTTP_201_CREATED)
async def create_department(
    org_slug: str,
    payload: DepartmentCreate,
    current_user: CurrentSuperAdminDep,
    db: AsyncSession = Depends(get_db)
):
    org_id = await get_org_id(org_slug, db)
    if payload.parent_department_id:
        parent_result = await db.execute(
            select(Department).where(
                Department.id == payload.parent_department_id,
                Department.organization_id == org_id
            )
        )
        if parent_result.scalar_one_or_none() is None:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Parent department not found in this organization")
    dept = Department(**payload.model_dump(), organization_id=org_id)
    db.add(dept)
    await db.commit()
    await db.refresh(dept)
    return dept

@router.get("", response_model=List[DepartmentRead])
async def list_departments(org_slug: str, current_user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(select(Department).where(Department.organization_id == org_id))
    return result.scalars().all()

@router.get("/tree", response_model=List[DepartmentTree])
async def get_department_tree(org_slug: str, current_user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(select(Department).where(Department.organization_id == org_id))
    all_depts = result.scalars().all()
    dept_map = {d.id: DepartmentTree.model_validate(d) for d in all_depts}
    roots = []
    for dept in all_depts:
        if dept.parent_department_id is None:
            roots.append(dept_map[dept.id])
        elif dept.parent_department_id in dept_map:
            dept_map[dept.parent_department_id].children.append(dept_map[dept.id])
    return roots

@router.get("/{dept_id}", response_model=DepartmentRead)
async def get_department(org_slug: str, dept_id: int, current_user: CurrentUserDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    return dept

@router.patch("/{dept_id}", response_model=DepartmentRead)
async def update_department(
    org_slug: str,
    dept_id: int,
    payload: DepartmentUpdate,
    current_user: CurrentSuperAdminDep,
    db: AsyncSession = Depends(get_db)
):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(dept, key, value)
    await db.commit()
    await db.refresh(dept)
    return dept

@router.delete("/{dept_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_department(org_slug: str, dept_id: int, current_user: CurrentSuperAdminDep, db: AsyncSession = Depends(get_db)):
    org_id = await get_org_id(org_slug, db)
    result = await db.execute(
        select(Department).where(Department.id == dept_id, Department.organization_id == org_id)
    )
    dept = result.scalar_one_or_none()
    if dept is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Department not found")
    await db.delete(dept)
    await db.commit()
    return None