"""
AssetImportRequest model with encrypted credential storage.
Uses our crypto utilities for secure storage of AWS credentials.
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base
from ..utils.crypto import encrypt_value, decrypt_value


class AssetImportRequest(Base):
    __tablename__ = "asset_import_requests"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    organization_id: Mapped[int] = mapped_column(
        ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False, index=True
    )
    requested_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    role_arn_encrypted: Mapped[str] = mapped_column(
        String(2048), nullable=False
    )
    account_name_encrypted: Mapped[Optional[str]] = mapped_column(
        String(255), nullable=True, default=None
    )
    region_encrypted: Mapped[str] = mapped_column(
        String(64), nullable=False, default="us-east-1"
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    reviewed_by_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    review_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), server_onupdate=func.now(), nullable=False
    )

    # Relationships
    requested_by = relationship("User", foreign_keys=[requested_by_id])
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])

    # Property methods for encrypted fields
    @property
    def role_arn(self) -> str:
        return decrypt_value(self.role_arn_encrypted)

    @role_arn.setter
    def role_arn(self, value: str) -> None:
        self.role_arn_encrypted = encrypt_value(value)

    @property
    def account_name(self) -> Optional[str]:
        return decrypt_value(self.account_name_encrypted)

    @account_name.setter
    def account_name(self, value: Optional[str]) -> None:
        self.account_name_encrypted = encrypt_value(value)

    @property
    def region(self) -> str:
        return decrypt_value(self.region_encrypted)

    @region.setter
    def region(self, value: str) -> None:
        self.region_encrypted = encrypt_value(value)

    def __repr__(self):
        return f"<AssetImportRequest {self.role_arn} - {self.region}>"