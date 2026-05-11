from pydantic import BaseModel, Field


class ModerationRequest(BaseModel):
    status: str = Field(pattern="^(approved|rejected)$")
    moderator_note: str | None = None
    risk_level: str | None = Field(default=None, pattern="^(low|medium|high|critical)$")
