from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LookupHistory(Base):
    __tablename__ = "lookup_history"
    __table_args__ = (
        Index("ix_lookup_history_user_created", "user_id", "created_at"),
        Index("ix_lookup_history_normalized", "normalized_value"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), nullable=False)
    query_type: Mapped[str] = mapped_column(String(50), nullable=False)
    query_value: Mapped[str] = mapped_column(String(255), nullable=False)
    normalized_value: Mapped[str] = mapped_column(String(255), nullable=False)
    result_entity_id: Mapped[Optional[str]] = mapped_column(ForeignKey("scam_entities.id"))
    result_risk_level: Mapped[Optional[str]] = mapped_column(String(30))
    result_found: Mapped[bool] = mapped_column(Boolean, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="lookup_history")
