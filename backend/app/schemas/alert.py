from datetime import datetime

from pydantic import BaseModel, Field


class CallAlertCreate(BaseModel):
    phone_number: str = Field(min_length=8)
    duration_seconds: int | None = Field(default=None, ge=0)
    transcript: str | None = None
    note: str | None = None


class CallAlertResponse(BaseModel):
    call_id: str
    alert_id: str
    phone_number: str
    risk_level: str
    message: str
    recommended_action: str
    call_time: datetime


class AlertHistoryItem(BaseModel):
    call_id: str
    alert_id: str
    phone_number: str
    risk_level: str
    message: str
    recommended_action: str
    call_time: datetime
    duration_seconds: int | None


class CallReportItem(BaseModel):
    call_id: str
    alert_id: str
    phone_number: str
    risk_level: str
    call_time: datetime
    duration_seconds: int | None
    transcript: str | None
    note: str | None
    message: str
    recommended_action: str
    status: str
