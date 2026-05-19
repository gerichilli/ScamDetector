from secrets import token_urlsafe
from urllib.parse import urlencode

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.core.security import create_access_token, decode_access_token, hash_password, verify_password
from app.models.user import User
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse, UserResponse
from app.services.normalization_service import normalize_entity_value

router = APIRouter(prefix="/auth", tags=["auth"])


def serialize_user(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        phone_number=user.phone_number,
        full_name=user.full_name,
        role=user.role,
        status=user.status,
    )


def parse_identifier(raw_value: str | None) -> tuple[str, str]:
    value = (raw_value or "").strip()
    if not value:
        raise HTTPException(status_code=422, detail="Email or phone number is required")
    if "@" in value:
        return "email", value.lower()
    normalized_phone = normalize_entity_value("phone", value)
    if not normalized_phone.isdigit() or len(normalized_phone) < 9 or len(normalized_phone) > 11:
        raise HTTPException(status_code=422, detail="Invalid email or phone number")
    return "phone", normalized_phone


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> UserResponse:
    raw_identifier = payload.identifier or payload.email or payload.phone_number
    identifier_type, identifier = parse_identifier(raw_identifier)
    email = identifier if identifier_type == "email" else None
    phone_number = (payload.phone_number or raw_identifier or "").strip() if identifier_type == "phone" else None
    normalized_phone_number = identifier if identifier_type == "phone" else None

    existing = db.scalar(
        select(User).where(
            User.email == email if email else User.normalized_phone_number == normalized_phone_number
        )
    )
    if existing:
        raise HTTPException(status_code=409, detail="Account already registered")

    user = User(
        email=email,
        phone_number=phone_number,
        normalized_phone_number=normalized_phone_number,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return serialize_user(user)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    identifier_type, identifier = parse_identifier(payload.identifier or payload.email)
    user = db.scalar(
        select(User).where(
            User.email == identifier if identifier_type == "email" else User.normalized_phone_number == identifier
        )
    )
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid account or password")
    if user.status != "active":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not active")

    return TokenResponse(
        access_token=create_access_token(user.id, {"role": user.role}),
        user=serialize_user(user),
    )


@router.get("/google/login")
def google_login() -> RedirectResponse:
    settings = get_settings()
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Google OAuth is not configured")

    state = create_access_token("google-oauth", {"purpose": "google_oauth"})
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
            "state": state,
            "prompt": "select_account",
        }
    )
    return RedirectResponse(f"https://accounts.google.com/o/oauth2/v2/auth?{query}")


@router.get("/google/callback")
def google_callback(
    code: str = Query(...),
    state: str = Query(...),
    db: Session = Depends(get_db),
) -> RedirectResponse:
    settings = get_settings()
    state_payload = decode_access_token(state)
    if not state_payload or state_payload.get("purpose") != "google_oauth":
        return RedirectResponse(f"{settings.frontend_url}/auth/google/callback?error=invalid_state")

    try:
        token_response = httpx.post(
            "https://oauth2.googleapis.com/token",
            data={
                "code": code,
                "client_id": settings.google_client_id,
                "client_secret": settings.google_client_secret,
                "redirect_uri": settings.google_redirect_uri,
                "grant_type": "authorization_code",
            },
            timeout=10,
        )
        token_response.raise_for_status()
        access_token = token_response.json().get("access_token")
        if not access_token:
            raise ValueError("Google token response did not include access_token")

        userinfo_response = httpx.get(
            "https://openidconnect.googleapis.com/v1/userinfo",
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )
        userinfo_response.raise_for_status()
        userinfo = userinfo_response.json()
    except Exception:
        return RedirectResponse(f"{settings.frontend_url}/auth/google/callback?error=google_auth_failed")

    email = str(userinfo.get("email") or "").lower()
    google_sub = str(userinfo.get("sub") or "")
    full_name = userinfo.get("name")
    if not email or not google_sub or userinfo.get("email_verified") is False:
        return RedirectResponse(f"{settings.frontend_url}/auth/google/callback?error=email_not_verified")

    user = db.scalar(select(User).where(User.google_sub == google_sub))
    if not user:
        user = db.scalar(select(User).where(User.email == email))

    if user:
        user.google_sub = google_sub
        if user.auth_provider == "local":
            user.auth_provider = "local_google"
        if not user.full_name and full_name:
            user.full_name = str(full_name)
    else:
        user = User(
            email=email,
            google_sub=google_sub,
            auth_provider="google",
            password_hash=hash_password(token_urlsafe(32)),
            full_name=str(full_name) if full_name else None,
        )
        db.add(user)

    db.commit()
    db.refresh(user)
    app_token = create_access_token(user.id, {"role": user.role})
    query = urlencode({"access_token": app_token})
    return RedirectResponse(f"{settings.frontend_url}/auth/google/callback?{query}")


@router.get("/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return serialize_user(user)
