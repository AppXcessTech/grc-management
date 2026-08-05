from pydantic import BaseModel, ConfigDict


class RequirementBase(BaseModel):
    framework_id: int
    code: str
    name: str
    description: str | None = None
    status: str | None = None


class RequirementCreate(RequirementBase):
    pass


class RequirementUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: str | None = None


class Requirement(RequirementBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
