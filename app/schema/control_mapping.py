from pydantic import BaseModel, ConfigDict


class ControlMappingBase(BaseModel):
    control_id: int
    requirement_id: int


class ControlMappingCreate(ControlMappingBase):
    pass


class ControlMapping(ControlMappingBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
