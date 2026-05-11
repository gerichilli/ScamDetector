from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Optional
from uuid import uuid4

from sqlalchemy import Date, DateTime, ForeignKey, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScamReport(Base):
    __tablename__ = "scam_reports"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    reporter_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    scam_entity_id: Mapped[str] = mapped_column(ForeignKey("scam_entities.id"), nullable=False)
    scam_type: Mapped[str] = mapped_column(String(80), nullable=False)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    description: Mapped[str] = mapped_column(Text, nullable=False)
    amount_lost: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(10), default="VND", nullable=False)
    incident_date: Mapped[Optional[date]] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String(30), default="pending", nullable=False)
    moderator_id: Mapped[Optional[str]] = mapped_column(ForeignKey("users.id"))
    moderator_note: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reporter = relationship("User", foreign_keys=[reporter_id], back_populates="reports")
    scam_entity = relationship("ScamEntity", back_populates="reports")
    evidence = relationship("ReportEvidence", back_populates="report", cascade="all, delete-orphan")
