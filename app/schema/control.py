from pydantic import BaseModel, ConfigDict
from app.models.enums import ComplianceStatus


class ControlBase(BaseModel):
    organization_id: int
    code: str
    name: str
    description: str | None = None
    status: ComplianceStatus = ComplianceStatus.not_applicable


class ControlCreate(ControlBase):
    pass


class ControlUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    description: str | None = None
    status: ComplianceStatus | None = None


class Control(ControlBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class ControlWithEvidenceCount(Control):
    evidence_count: int = 0
