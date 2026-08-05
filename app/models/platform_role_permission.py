from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class PlatformRolePermission(Base):
    __tablename__ = "platform_role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey("platform_roles.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("platform_permissions.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
