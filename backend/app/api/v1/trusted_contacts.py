from datetime import datetime, timezone
from secrets import token_urlsafe
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.trusted_contact import TrustedContact
from app.models.user import User
from app.schemas.trusted_contact import TrustedContactCreateRequest, TrustedContactResponse
from app.services.email_service import send_trusted_contact_confirmation_email, smtp_enabled

router = APIRouter(prefix="/trusted-contacts", tags=["trusted-contacts"])


def build_confirmation_url(token: str) -> str:
    return f"http://localhost:8000/api/v1/trusted-contacts/confirm?{urlencode({'token': token})}"


def serialize_contact(contact: TrustedContact, include_preview: bool = False) -> TrustedContactResponse:
    return TrustedContactResponse(
        id=contact.id,
        full_name=contact.full_name,
        email=contact.email,
        phone_number=contact.phone_number,
        status=contact.status,
        confirmed_at=contact.confirmed_at,
        created_at=contact.created_at,
        confirmation_preview_url=build_confirmation_url(contact.confirmation_token) if include_preview and contact.confirmation_token else None,
    )


def get_owned_contact(contact_id: str, user_id: str, db: Session) -> TrustedContact:
    contact = db.scalar(select(TrustedContact).where(TrustedContact.id == contact_id, TrustedContact.user_id == user_id))
    if not contact:
        raise HTTPException(status_code=404, detail="Trusted contact not found")
    return contact


@router.get("", response_model=list[TrustedContactResponse])
def list_trusted_contacts(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[TrustedContactResponse]:
    contacts = db.scalars(select(TrustedContact).where(TrustedContact.user_id == user.id).order_by(TrustedContact.created_at.desc())).all()
    show_preview = not smtp_enabled()
    return [serialize_contact(contact, include_preview=show_preview) for contact in contacts]


@router.post("", response_model=TrustedContactResponse, status_code=status.HTTP_201_CREATED)
def create_trusted_contact(
    payload: TrustedContactCreateRequest,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrustedContactResponse:
    existing = db.scalar(select(TrustedContact).where(TrustedContact.user_id == user.id, TrustedContact.email == payload.email.lower()))
    if existing:
        raise HTTPException(status_code=409, detail="Trusted contact email already added")

    contact = TrustedContact(
        user_id=user.id,
        full_name=payload.full_name.strip(),
        email=payload.email.lower(),
        phone_number=(payload.phone_number or "").strip() or None,
        status="pending",
        confirmation_token=token_urlsafe(32),
    )
    db.add(contact)
    db.commit()
    db.refresh(contact)

    if smtp_enabled():
        try:
            send_trusted_contact_confirmation_email(contact.email, contact.full_name, build_confirmation_url(contact.confirmation_token or ""))
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Failed to send confirmation email: {exc}") from exc

    return serialize_contact(contact, include_preview=not smtp_enabled())


@router.post("/{contact_id}/resend-confirmation", response_model=TrustedContactResponse)
def resend_confirmation(
    contact_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrustedContactResponse:
    contact = get_owned_contact(contact_id, user.id, db)
    if contact.status == "confirmed":
        return serialize_contact(contact, include_preview=False)

    contact.confirmation_token = token_urlsafe(32)
    db.commit()
    db.refresh(contact)

    if smtp_enabled():
        try:
            send_trusted_contact_confirmation_email(contact.email, contact.full_name, build_confirmation_url(contact.confirmation_token or ""))
        except Exception as exc:
            raise HTTPException(status_code=503, detail=f"Failed to send confirmation email: {exc}") from exc

    return serialize_contact(contact, include_preview=not smtp_enabled())


@router.delete("/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trusted_contact(
    contact_id: str,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    contact = get_owned_contact(contact_id, user.id, db)
    db.delete(contact)
    db.commit()


@router.get("/confirm")
def confirm_trusted_contact(token: str = Query(...), db: Session = Depends(get_db)) -> RedirectResponse:
    settings = get_settings()
    contact = db.scalar(select(TrustedContact).where(TrustedContact.confirmation_token == token))
    if not contact:
        return RedirectResponse(f"{settings.frontend_url}/trusted-contact-confirm?status=invalid")

    contact.status = "confirmed"
    contact.confirmed_at = datetime.now(timezone.utc)
    contact.confirmation_token = None
    db.commit()
    return RedirectResponse(f"{settings.frontend_url}/trusted-contact-confirm?status=success&email={contact.email}")
