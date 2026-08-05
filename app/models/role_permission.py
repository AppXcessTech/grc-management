from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class RolePermission(Base):
    __tablename__ = "role_permissions"

    role_id: Mapped[int] = mapped_column(
        ForeignKey("roles.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )
    permission_id: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="CASCADE"), primary_key=True, nullable=False, index=True
    )
