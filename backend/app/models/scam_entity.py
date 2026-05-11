from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ScamEntity(Base):
    __tablename__ = "scam_entities"
    __table_args__ = (
        UniqueConstraint("entity_type", "normalized_value", name="uq_scam_entity_type_normalized"),
        Index("ix_scam_entities_normalized_value", "normalized_value"),
        Index("ix_scam_entities_type_risk", "entity_type", "risk_level"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    entity_type: Mapped[str] = mapped_column(String(50), nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    display_name: Mapped[Optional[str]] = mapped_column(String(255))
    bank_name: Mapped[Optional[str]] = mapped_column(String(120))
    risk_level: Mapped[str] = mapped_column(String(30), default="low", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="under_review", nullable=False)
    report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    verified_report_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    first_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_reported_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    reports = relationship("ScamReport", back_populates="scam_entity")
