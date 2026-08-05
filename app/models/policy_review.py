from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Enum, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from .enums import ReviewStatus

if TYPE_CHECKING:
    from .policy import Policy
    from .user import User


class PolicyReview(Base):
    __tablename__ = "policy_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    policy_id: Mapped[int] = mapped_column(
        ForeignKey("policies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewer_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[ReviewStatus] = mapped_column(
        Enum(ReviewStatus, name="review_status", native_enum=False),
        nullable=False,
        default=ReviewStatus.pending,
    )
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    policy: Mapped["Policy"] = relationship(back_populates="reviews")
    reviewer: Mapped["User"] = relationship()
