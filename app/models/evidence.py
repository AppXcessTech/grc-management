from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import EvidenceReviewStatus, EvidenceSourceType, EvidenceType

if TYPE_CHECKING:
    from .control import Control
    from .requirement import Requirement
    from .user import User


class EvidenceSource(Base):
    __tablename__ = "evidence_sources"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True, index=True)
    source_type: Mapped[EvidenceSourceType] = mapped_column(
        Enum(EvidenceSourceType, name="evidence_source_type", native_enum=False),
        nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    config_schema: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Evidence(Base):
    __tablename__ = "evidence"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int | None] = mapped_column(
        ForeignKey("evidence_sources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    evidence_type: Mapped[EvidenceType] = mapped_column(
        Enum(EvidenceType, name="evidence_type", native_enum=False),
        nullable=False,
        default=EvidenceType.document,
    )
    collected_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    collected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    source: Mapped["EvidenceSource"] = relationship()
    collector: Mapped["User"] = relationship()
    files: Mapped[list["EvidenceFile"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")
    reviews: Mapped[list["EvidenceReview"]] = relationship(back_populates="evidence", cascade="all, delete-orphan")
    controls: Mapped[list["Control"]] = relationship(
        secondary="evidence_control_links", back_populates="evidence_items"
    )
    requirements: Mapped[list["Requirement"]] = relationship(
        secondary="evidence_requirement_links", back_populates="evidence_items"
    )

    @property
    def control_ids(self) -> list[int]:
        return [c.id for c in self.controls]

    @property
    def requirement_ids(self) -> list[int]:
        return [r.id for r in self.requirements]


class EvidenceFile(Base):
    __tablename__ = "evidence_files"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    file_path: Mapped[str] = mapped_column(String(512), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    uploaded_by: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evidence: Mapped["Evidence"] = relationship(back_populates="files")
    uploader: Mapped["User"] = relationship()


class EvidenceReview(Base):
    __tablename__ = "evidence_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[EvidenceReviewStatus] = mapped_column(
        Enum(EvidenceReviewStatus, name="evidence_review_status", native_enum=False),
        nullable=False,
        default=EvidenceReviewStatus.pending,
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    evidence: Mapped["Evidence"] = relationship(back_populates="reviews")
    reviewer: Mapped["User"] = relationship()


class EvidenceControlLink(Base):
    __tablename__ = "evidence_control_links"

    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )
    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )


class EvidenceRequirementLink(Base):
    __tablename__ = "evidence_requirement_links"

    evidence_id: Mapped[int] = mapped_column(
        ForeignKey("evidence.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )
