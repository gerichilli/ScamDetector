from datetime import datetime

from pydantic import BaseModel


class ScamEntityResponse(BaseModel):
    id: str
    entity_type: str
    value: str
    risk_level: str
    status: str
    report_count: int
    verified_report_count: int
    first_reported_at: datetime | None
    last_reported_at: datetime | None


class ScamTypeCount(BaseModel):
    scam_type: str
    count: int


class LookupResponse(BaseModel):
    found: bool
    entity: ScamEntityResponse | None = None
    summary: dict[str, list[ScamTypeCount]] | None = None
    message: str | None = None
