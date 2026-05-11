from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class ScamDatabaseEntry(Base):
    __tablename__ = "scam_database_entries"
    __table_args__ = (UniqueConstraint("phone_number", "pattern", name="uq_scam_database_phone_pattern"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    phone_number: Mapped[Optional[str]] = mapped_column(String(40), index=True)
    normalized_phone_number: Mapped[Optional[str]] = mapped_column(String(40), index=True)
    pattern: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    risk_level: Mapped[str] = mapped_column(String(30), default="medium", nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )
