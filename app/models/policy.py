from datetime import datetime
from typing import TYPE_CHECKING, List

from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import PolicyCategory, PolicyStatus

if TYPE_CHECKING:
    from .organization import Organization
    from .policy_version import PolicyVersion
    from .policy_review import PolicyReview


class Policy(Base):
    __tablename__ = "policies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[PolicyCategory] = mapped_column(
        Enum(PolicyCategory, name="policy_category", native_enum=False),
        nullable=False,
        default=PolicyCategory.other,
    )
    status: Mapped[PolicyStatus] = mapped_column(
        Enum(PolicyStatus, name="policy_status", native_enum=False),
        nullable=False,
        default=PolicyStatus.draft,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    organization: Mapped["Organization"] = relationship()
    versions: Mapped[List["PolicyVersion"]] = relationship(back_populates="policy", cascade="all, delete-orphan")
    reviews: Mapped[List["PolicyReview"]] = relationship(back_populates="policy", cascade="all, delete-orphan")
