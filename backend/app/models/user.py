from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    email: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    phone_number: Mapped[Optional[str]] = mapped_column(String(40), unique=True, index=True)
    normalized_phone_number: Mapped[Optional[str]] = mapped_column(String(40), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    google_sub: Mapped[Optional[str]] = mapped_column(String(255), unique=True, index=True)
    auth_provider: Mapped[str] = mapped_column(String(30), default="local", nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="user", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reports = relationship("ScamReport", back_populates="reporter", foreign_keys="ScamReport.reporter_id")
    lookup_history = relationship("LookupHistory", back_populates="user")
