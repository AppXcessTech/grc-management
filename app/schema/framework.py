from pydantic import BaseModel, ConfigDict


class FrameworkBase(BaseModel):
    name: str
    description: str | None = None
    version: str | None = None


class FrameworkCreate(FrameworkBase):
    pass


class FrameworkUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    version: str | None = None


class Framework(FrameworkBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
