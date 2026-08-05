from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base
from .enums import PermissionAction


class Permission(Base):
    __tablename__ = "permissions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    resource: Mapped[str] = mapped_column(String(128), nullable=False)
    action: Mapped[PermissionAction] = mapped_column(
        Enum(PermissionAction, name="permission_action", native_enum=False), nullable=False
    )
    category: Mapped[str | None] = mapped_column(String(128), nullable=True)
    description: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
