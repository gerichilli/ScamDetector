from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_optional_user
from app.core.database import get_db
from app.models.lookup_history import LookupHistory
from app.models.scam_entity import ScamEntity
from app.models.scam_report import ScamReport
from app.models.user import User
from app.schemas.lookup import LookupResponse, ScamEntityResponse, ScamTypeCount
from app.services.normalization_service import normalize_entity_value

router = APIRouter(prefix="/lookup", tags=["lookup"])


@router.get("", response_model=LookupResponse)
def lookup(
    type: str = Query(..., pattern="^(phone|bank_account|e_wallet|social_account)$"),
    value: str = Query(..., min_length=2),
    db: Session = Depends(get_db),
    user: User | None = Depends(get_optional_user),
) -> LookupResponse:
    normalized = normalize_entity_value(type, value)
    entity = db.scalar(
        select(ScamEntity).where(
            ScamEntity.entity_type == type,
            ScamEntity.normalized_value == normalized,
        )
    )

    if user:
        db.add(
            LookupHistory(
                user_id=user.id,
                query_type=type,
                query_value=value,
                normalized_value=normalized,
                result_entity_id=entity.id if entity else None,
                result_risk_level=entity.risk_level if entity else None,
                result_found=entity is not None,
            )
        )
        db.commit()

    if not entity:
        return LookupResponse(found=False, message="No scam record found for this query.")

    rows = db.execute(
        select(ScamReport.scam_type, func.count(ScamReport.id))
        .where(ScamReport.scam_entity_id == entity.id, ScamReport.status == "approved")
        .group_by(ScamReport.scam_type)
        .order_by(func.count(ScamReport.id).desc())
        .limit(5)
    ).all()

    return LookupResponse(
        found=True,
        entity=ScamEntityResponse(
            id=entity.id,
            entity_type=entity.entity_type,
            value=entity.value,
            risk_level=entity.risk_level,
            status=entity.status,
            report_count=entity.report_count,
            verified_report_count=entity.verified_report_count,
            first_reported_at=entity.first_reported_at,
            last_reported_at=entity.last_reported_at,
        ),
        summary={"top_scam_types": [ScamTypeCount(scam_type=row[0], count=row[1]) for row in rows]},
    )
