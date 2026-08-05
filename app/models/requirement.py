from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .control_mapping import ControlMapping
    from .evidence import Evidence
    from .framework import Framework


class Requirement(Base):
    __tablename__ = "requirements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    framework_id: Mapped[int] = mapped_column(
        ForeignKey("frameworks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    code: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str | None] = mapped_column(String(32), nullable=True, default=None)

    framework: Mapped["Framework"] = relationship(back_populates="requirements")
    control_mappings: Mapped[list["ControlMapping"]] = relationship(back_populates="requirement", cascade="all, delete-orphan")
    evidence_items: Mapped[list["Evidence"]] = relationship(
        secondary="evidence_requirement_links", back_populates="requirements"
    )
