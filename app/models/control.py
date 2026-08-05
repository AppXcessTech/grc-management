from typing import TYPE_CHECKING

from sqlalchemy import Enum, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import ComplianceStatus

if TYPE_CHECKING:
    from .control_mapping import ControlMapping
    from .evidence import Evidence


class Control(Base):
    __tablename__ = "controls"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[ComplianceStatus] = mapped_column(
        Enum(ComplianceStatus, name="compliance_status", native_enum=False),
        nullable=False,
        default=ComplianceStatus.not_applicable,
    )

    control_mappings: Mapped[list["ControlMapping"]] = relationship(back_populates="control", cascade="all, delete-orphan")
    evidence_items: Mapped[list["Evidence"]] = relationship(
        secondary="evidence_control_links", back_populates="controls"
    )
