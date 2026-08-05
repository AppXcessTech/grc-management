from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy import select
from app.core.database import get_db
from app.core.dependencies import CurrentUserDep, DBSessionDep
from app.models.department import Department
from app.schema.department import DepartmentRead

router = APIRouter(prefix="/api/departments", tags=["departments"])


@router.get("", response_model=List[DepartmentRead])
async def list_my_departments(current_user: CurrentUserDep, db: DBSessionDep):
    result = await db.execute(
        select(Department).where(Department.organization_id == current_user.organization_id)
    )
    return result.scalars().all()
