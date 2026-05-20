from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class TrustedContactCreateRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)
    email: EmailStr
    phone_number: str | None = Field(default=None, max_length=40)


class TrustedContactResponse(BaseModel):
    id: str
    full_name: str
    email: EmailStr
    phone_number: str | None
    status: str
    confirmed_at: datetime | None
    created_at: datetime
    confirmation_preview_url: str | None = None
