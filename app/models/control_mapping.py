from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class ControlMapping(Base):
    __tablename__ = "control_mappings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    control_id: Mapped[int] = mapped_column(
        ForeignKey("controls.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requirement_id: Mapped[int] = mapped_column(
        ForeignKey("requirements.id", ondelete="CASCADE"), nullable=False, index=True
    )

    control: Mapped["Control"] = relationship(back_populates="control_mappings")
    requirement: Mapped["Requirement"] = relationship(back_populates="control_mappings")
