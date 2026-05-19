from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3, max_length=255)
    email: EmailStr | None = None
    phone_number: str | None = Field(default=None, max_length=40)
    password: str = Field(min_length=8)
    full_name: str | None = Field(default=None, max_length=255)


class LoginRequest(BaseModel):
    identifier: str | None = Field(default=None, min_length=3, max_length=255)
    email: str | None = None
    password: str


class UserResponse(BaseModel):
    id: str
    email: EmailStr | None
    phone_number: str | None = None
    full_name: str | None
    role: str
    status: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
