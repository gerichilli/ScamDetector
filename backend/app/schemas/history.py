from datetime import datetime

from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: str
    query_type: str
    query_value: str
    result_found: bool
    result_risk_level: str | None
    created_at: datetime
