from pydantic import BaseModel, ConfigDict

class RoleBase(BaseModel):
    name: str
    display_name: str
    is_system: bool = False

class RoleCreate(RoleBase):
    organization_id: int | None = None

class RoleUpdate(BaseModel):
    name: str | None = None
    display_name: str | None = None

class RoleSchema(RoleBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int | None
