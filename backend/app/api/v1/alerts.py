from datetime import datetime, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.database import get_db
from app.models.call_record import CallRecord
from app.models.notification import Notification
from app.models.scam_alert import ScamAlert
from app.models.user import User
from app.schemas.alert import AlertHistoryItem, CallAlertCreate, CallAlertResponse, CallReportItem
from app.services.alert_service import classify_call_risk
from app.services.normalization_service import normalize_entity_value

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.post("/calls", response_model=CallAlertResponse)
def create_call_alert(
    payload: CallAlertCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> CallAlertResponse:
    risk_level, message, recommended_action = classify_call_risk(db, payload.phone_number, payload.transcript)
    call_record = CallRecord(
        elderly_user_id=user.id,
        phone_number=payload.phone_number,
        normalized_phone_number=normalize_entity_value("phone", payload.phone_number),
        duration_seconds=payload.duration_seconds,
        transcript=payload.transcript,
        note=payload.note,
    )
    db.add(call_record)
    db.flush()

    alert = ScamAlert(
        call_id=call_record.id,
        risk_level=risk_level,
        message=message,
        recommended_action=recommended_action,
    )
    db.add(alert)
    db.flush()

    if risk_level in {"high", "critical"}:
        db.add(Notification(alert_id=alert.id, target_user_id=user.id, channel="in_app", sent=True))

    db.commit()
    db.refresh(call_record)
    db.refresh(alert)
    return CallAlertResponse(
        call_id=call_record.id,
        alert_id=alert.id,
        phone_number=call_record.phone_number,
        risk_level=alert.risk_level,
        message=alert.message,
        recommended_action=alert.recommended_action,
        call_time=call_record.call_time,
    )


@router.get("/history")
def alert_history(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    query = (
        select(CallRecord, ScamAlert)
        .join(ScamAlert, ScamAlert.call_id == CallRecord.id)
        .where(CallRecord.elderly_user_id == user.id)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(CallRecord.call_time.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        AlertHistoryItem(
            call_id=call.id,
            alert_id=alert.id,
            phone_number=call.phone_number,
            risk_level=alert.risk_level,
            message=alert.message,
            recommended_action=alert.recommended_action,
            call_time=call.call_time,
            duration_seconds=call.duration_seconds,
        ).model_dump()
        for call, alert in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/calls/my")
def my_call_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    query = (
        select(CallRecord, ScamAlert)
        .join(ScamAlert, ScamAlert.call_id == CallRecord.id)
        .where(CallRecord.elderly_user_id == user.id)
    )
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(CallRecord.call_time.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        CallReportItem(
            call_id=call.id,
            alert_id=alert.id,
            phone_number=call.phone_number,
            risk_level=alert.risk_level,
            call_time=call.call_time,
            duration_seconds=call.duration_seconds,
            transcript=call.transcript,
            note=call.note,
            message=alert.message,
            recommended_action=alert.recommended_action,
            status="Đã ghi nhận và tạo cảnh báo",
        ).model_dump()
        for call, alert in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/summary")
def alert_summary(db: Session = Depends(get_db), user: User = Depends(get_current_user)) -> dict:
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    base = select(ScamAlert).join(CallRecord, ScamAlert.call_id == CallRecord.id).where(CallRecord.elderly_user_id == user.id)
    return {
        "total_alerts": db.scalar(select(func.count()).select_from(base.subquery())) or 0,
        "high_risk_alerts": db.scalar(
            select(func.count()).select_from(base.where(ScamAlert.risk_level.in_(["high", "critical"])).subquery())
        )
        or 0,
        "today_alerts": db.scalar(
            select(func.count()).select_from(base.where(CallRecord.call_time >= today_start).subquery())
        )
        or 0,
    }
