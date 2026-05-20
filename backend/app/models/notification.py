from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    alert_id: Mapped[str] = mapped_column(ForeignKey("scam_alerts.id"), nullable=False)
    target_user_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    target_email: Mapped[Optional[str]] = mapped_column(String(255))
    channel: Mapped[str] = mapped_column(String(30), default="in_app", nullable=False)
    sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    alert = relationship("ScamAlert", back_populates="notifications")
