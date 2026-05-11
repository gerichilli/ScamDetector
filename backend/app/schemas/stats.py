from pydantic import BaseModel


class OverviewStats(BaseModel):
    total_reports: int
    approved_reports: int
    total_scam_entities: int
    high_risk_entities: int
    reports_last_7_days: int


class TypeStats(BaseModel):
    scam_type: str
    count: int


class TrendStats(BaseModel):
    date: str
    reports: int
    new_entities: int
