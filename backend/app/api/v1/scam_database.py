from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.scam_database_entry import ScamDatabaseEntry
from app.models.user import User
from app.schemas.scam_database import ScamDatabaseEntryCreate, ScamDatabaseEntryResponse
from app.services.normalization_service import normalize_entity_value

router = APIRouter(prefix="/scam-database", tags=["scam-database"])


@router.get("")
def list_entries(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> dict:
    query = select(ScamDatabaseEntry)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(ScamDatabaseEntry.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [
            ScamDatabaseEntryResponse(
                id=item.id,
                phone_number=item.phone_number,
                pattern=item.pattern,
                description=item.description,
                risk_level=item.risk_level,
                updated_at=item.updated_at,
            ).model_dump()
            for item in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post("", response_model=ScamDatabaseEntryResponse)
def create_entry(
    payload: ScamDatabaseEntryCreate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ScamDatabaseEntryResponse:
    entry = ScamDatabaseEntry(
        phone_number=payload.phone_number,
        normalized_phone_number=normalize_entity_value("phone", payload.phone_number) if payload.phone_number else None,
        pattern=payload.pattern,
        description=payload.description,
        risk_level=payload.risk_level,
    )
    db.add(entry)
    db.commit()
    db.refresh(entry)
    return ScamDatabaseEntryResponse(
        id=entry.id,
        phone_number=entry.phone_number,
        pattern=entry.pattern,
        description=entry.description,
        risk_level=entry.risk_level,
        updated_at=entry.updated_at,
    )
