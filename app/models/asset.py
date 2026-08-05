from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    category_id: Mapped[int] = mapped_column(
        ForeignKey("asset_categories.id", ondelete="RESTRICT"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(String(2048), nullable=True)
    source: Mapped[str] = mapped_column(String(50), nullable=False, default="Manual")
    external_id: Mapped[str | None] = mapped_column(String(1024), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="Active")
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    department: Mapped[str | None] = mapped_column(String(255), nullable=True)
    criticality: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    risk_level: Mapped[str] = mapped_column(String(50), nullable=False, default="Medium")
    compliance_scope: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    discovered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    organization = relationship("Organization")
    category = relationship("AssetCategory")
    owner = relationship("User")
    tags = relationship("AssetTag", back_populates="asset", cascade="all, delete-orphan")
    asset_owners = relationship("AssetOwner", back_populates="asset", cascade="all, delete-orphan")

    @property
    def owner_name(self) -> str | None:
        if self.owner:
            return f"{self.owner.first_name} {self.owner.last_name}".strip() or self.owner.email
        return None
