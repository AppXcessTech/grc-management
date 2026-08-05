from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .enums import RelationshipType


class AssetRelationship(Base):
    __tablename__ = "asset_relationships"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_asset_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    target_asset_id: Mapped[int] = mapped_column(
        ForeignKey("canonical_assets.id", ondelete="CASCADE"), nullable=False, index=True
    )
    relationship_type: Mapped[str] = mapped_column(
        Enum(RelationshipType, name="relationship_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    extras: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
