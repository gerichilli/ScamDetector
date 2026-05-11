from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CallRecord(Base):
    __tablename__ = "call_records"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    elderly_user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    phone_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    normalized_phone_number: Mapped[str] = mapped_column(String(40), nullable=False, index=True)
    call_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    duration_seconds: Mapped[Optional[int]] = mapped_column(Integer)
    transcript: Mapped[Optional[str]] = mapped_column(Text)
    note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    alert = relationship("ScamAlert", back_populates="call_record", uselist=False, cascade="all, delete-orphan")
