from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .policy_version import PolicyVersion
    from .user import User


class PolicyAcknowledgement(Base):
    __tablename__ = "policy_acknowledgements"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_version_id: Mapped[int] = mapped_column(
        ForeignKey("policy_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    acknowledged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    policy_version: Mapped["PolicyVersion"] = relationship(back_populates="acknowledgements")
    user: Mapped["User"] = relationship()
