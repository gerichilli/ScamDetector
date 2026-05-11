from datetime import datetime

from pydantic import BaseModel, Field


class ScamDatabaseEntryCreate(BaseModel):
    phone_number: str | None = None
    pattern: str = Field(min_length=2)
    description: str = Field(min_length=5)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high|critical)$")


class ScamDatabaseEntryResponse(BaseModel):
    id: str
    phone_number: str | None
    pattern: str
    description: str
    risk_level: str
    updated_at: datetime
