from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base

if TYPE_CHECKING:
    from .user import User


class PeopleAssetReview(Base):
    __tablename__ = "people_asset_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    people_asset_id: Mapped[int] = mapped_column(
        ForeignKey("people_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    reviewed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )
    reviewed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    reviewer: Mapped["User"] = relationship()
