from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.lookup_history import LookupHistory
from app.models.user import User
from app.schemas.history import HistoryItem

router = APIRouter(prefix="/history", tags=["history"])


@router.get("")
def list_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = Query(default=None),
    risk_level: str | None = Query(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    query = select(LookupHistory).where(LookupHistory.user_id == user.id)
    if type:
        query = query.where(LookupHistory.query_type == type)
    if risk_level:
        query = query.where(LookupHistory.result_risk_level == risk_level)

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(LookupHistory.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        HistoryItem(
            id=item.id,
            query_type=item.query_type,
            query_value=item.query_value,
            result_found=item.result_found,
            result_risk_level=item.result_risk_level,
            created_at=item.created_at,
        ).model_dump()
        for item in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}
