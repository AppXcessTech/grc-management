from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, JSON, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .enums import CanonicalType, Provider


class CanonicalAsset(Base):
    __tablename__ = "canonical_assets"

    __table_args__ = (
        UniqueConstraint("organization_id", "provider", "provider_resource_id", name="uq_asset_per_provider"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    provider: Mapped[str] = mapped_column(
        Enum(Provider, name="provider_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    provider_resource_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    canonical_type: Mapped[str] = mapped_column(
        Enum(CanonicalType, name="canonical_type_enum", native_enum=False),
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(512), nullable=True)
    account_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    owner: Mapped[str | None] = mapped_column(String(255), nullable=True)
    tags: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str | None] = mapped_column(String(50), nullable=True)
    environment: Mapped[str | None] = mapped_column(String(50), nullable=True)
    data_classification: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_connection_id: Mapped[str | None] = mapped_column(String(255), nullable=True, index=True)
    details: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    raw_resource_id: Mapped[int | None] = mapped_column(
        ForeignKey("raw_resources.id", ondelete="SET NULL"), nullable=True, index=True
    )
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
