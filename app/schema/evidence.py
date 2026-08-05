from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import EvidenceReviewStatus, EvidenceSourceType, EvidenceType


# ---- Evidence Sources ----
class EvidenceSourceCreate(BaseModel):
    name: str
    source_type: EvidenceSourceType
    description: str | None = None
    is_active: bool = True
    config_schema: dict | None = None


class EvidenceSourceUpdate(BaseModel):
    name: str | None = None
    source_type: EvidenceSourceType | None = None
    description: str | None = None
    is_active: bool | None = None
    config_schema: dict | None = None


class EvidenceSourceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    source_type: EvidenceSourceType
    description: str | None = None
    is_active: bool
    config_schema: dict | None = None
    created_at: datetime


# ---- Evidence Files ----
class EvidenceFileRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evidence_id: int
    file_path: str
    file_name: str
    file_size: int | None = None
    mime_type: str | None = None
    uploaded_by: int | None = None
    created_at: datetime


# ---- Evidence Reviews ----
class EvidenceReviewCreate(BaseModel):
    status: EvidenceReviewStatus
    comment: str | None = None


class EvidenceReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    evidence_id: int
    reviewer_id: int | None = None
    status: EvidenceReviewStatus
    comment: str | None = None
    reviewed_at: datetime | None = None
    created_at: datetime


# ---- Evidence ----
class EvidenceCreate(BaseModel):
    source_id: int | None = None
    name: str
    description: str | None = None
    evidence_type: EvidenceType = EvidenceType.document
    control_ids: list[int] = []
    requirement_ids: list[int] = []


class EvidenceUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    evidence_type: EvidenceType | None = None
    source_id: int | None = None
    control_ids: list[int] | None = None
    requirement_ids: list[int] | None = None


class EvidenceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    organization_id: int
    source_id: int | None = None
    name: str
    description: str | None = None
    evidence_type: EvidenceType
    collected_by: int | None = None
    collected_at: datetime
    created_at: datetime
    updated_at: datetime
    files: list[EvidenceFileRead] = []
    reviews: list[EvidenceReviewRead] = []
    control_ids: list[int] = []
    requirement_ids: list[int] = []
