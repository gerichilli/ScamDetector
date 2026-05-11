from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel


class ReportCreateResponse(BaseModel):
    id: str
    status: str
    scam_entity_id: str
    created_at: datetime


class ReportListItem(BaseModel):
    id: str
    entity_type: str
    entity_value: str
    scam_type: str
    status: str
    created_at: datetime


class ReportDetail(BaseModel):
    id: str
    reporter_id: str
    scam_entity_id: str
    entity_type: str
    entity_value: str
    scam_type: str
    title: str | None
    description: str
    amount_lost: Decimal | None
    currency: str
    incident_date: date | None
    status: str
    moderator_note: str | None
    evidence_urls: list[str]
    created_at: datetime
