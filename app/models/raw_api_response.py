from datetime import datetime

from sqlalchemy import DateTime, Integer, JSON, String, func
from sqlalchemy.orm import Mapped, mapped_column

from . import Base


class RawApiResponse(Base):
    __tablename__ = "raw_api_responses"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    discovery_run_id: Mapped[str] = mapped_column(String(36), nullable=False, index=True)
    provider: Mapped[str] = mapped_column(String(50), nullable=False)
    account_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    region: Mapped[str | None] = mapped_column(String(100), nullable=True)
    service: Mapped[str] = mapped_column(String(100), nullable=False)
    resource_type: Mapped[str] = mapped_column(String(100), nullable=False)
    provider_resource_id: Mapped[str] = mapped_column(String(1024), nullable=False)
    api_call: Mapped[str] = mapped_column(String(100), nullable=False)
    api_response: Mapped[dict] = mapped_column(JSON, nullable=False)
    discovered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
