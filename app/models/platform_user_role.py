from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class PlatformUserRole(Base):
    __tablename__ = "platform_user_roles"

    user_id: Mapped[int] = mapped_column(
        ForeignKey("platform_users.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
    role_id: Mapped[int] = mapped_column(
        ForeignKey("platform_roles.id", ondelete="CASCADE"), primary_key=True, nullable=False
    )
