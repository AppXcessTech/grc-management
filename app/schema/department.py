from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, ConfigDict

class DepartmentBase(BaseModel):
    name: str
    code: Optional[str] = None
    parent_department_id: Optional[int] = None

class DepartmentCreate(DepartmentBase):
    pass

class DepartmentUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    parent_department_id: Optional[int] = None

class DepartmentRead(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    organization_id: int
    created_at: datetime

class DepartmentTree(DepartmentRead):
    children: List['DepartmentTree'] = []
