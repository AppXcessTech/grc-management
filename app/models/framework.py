from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from . import Base


class Framework(Base):
    __tablename__ = "frameworks"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    version: Mapped[str | None] = mapped_column(String(64), nullable=True)

    requirements: Mapped[list["Requirement"]] = relationship(back_populates="framework", cascade="all, delete-orphan")
