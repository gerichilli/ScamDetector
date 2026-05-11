from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.scam_alert import ScamAlert
from app.models.scam_database_entry import ScamDatabaseEntry
from app.models.scam_entity import ScamEntity
from app.models.scam_report import ScamReport
from app.schemas.stats import OverviewStats, TrendStats, TypeStats

router = APIRouter(prefix="/stats", tags=["stats"])


@router.get("/overview", response_model=OverviewStats)
def overview(db: Session = Depends(get_db)) -> OverviewStats:
    since = datetime.now(timezone.utc) - timedelta(days=7)
    total_reports = (db.scalar(select(func.count(ScamReport.id))) or 0) + (db.scalar(select(func.count(ScamAlert.id))) or 0)
    high_risk_alerts = (
        db.scalar(select(func.count(ScamAlert.id)).where(ScamAlert.risk_level.in_(["high", "critical"]))) or 0
    )
    high_risk_entities = (
        db.scalar(select(func.count(ScamEntity.id)).where(ScamEntity.risk_level.in_(["high", "critical"]))) or 0
    )
    return OverviewStats(
        total_reports=total_reports,
        approved_reports=(db.scalar(select(func.count(ScamReport.id)).where(ScamReport.status == "approved")) or 0)
        + high_risk_alerts,
        total_scam_entities=(db.scalar(select(func.count(ScamEntity.id))) or 0)
        + (db.scalar(select(func.count(ScamDatabaseEntry.id))) or 0),
        high_risk_entities=high_risk_entities + high_risk_alerts,
        reports_last_7_days=(db.scalar(select(func.count(ScamReport.id)).where(ScamReport.created_at >= since)) or 0)
        + (db.scalar(select(func.count(ScamAlert.id)).where(ScamAlert.timestamp >= since)) or 0),
    )


@router.get("/by-type")
def by_type(db: Session = Depends(get_db)) -> dict:
    report_rows = db.execute(
        select(ScamReport.scam_type, func.count(ScamReport.id))
        .group_by(ScamReport.scam_type)
        .order_by(func.count(ScamReport.id).desc())
    ).all()
    pattern_rows = db.execute(
        select(ScamDatabaseEntry.pattern, func.count(ScamDatabaseEntry.id))
        .group_by(ScamDatabaseEntry.pattern)
        .order_by(func.count(ScamDatabaseEntry.id).desc())
    ).all()
    call_rows = db.execute(
        select(ScamAlert.risk_level, func.count(ScamAlert.id))
        .group_by(ScamAlert.risk_level)
        .order_by(func.count(ScamAlert.id).desc())
    ).all()
    merged: dict[str, int] = {}
    for key, count in [*report_rows, *pattern_rows]:
        merged[key] = merged.get(key, 0) + count
    for key, count in call_rows:
        merged[f"call_{key}"] = merged.get(f"call_{key}", 0) + count
    return {"items": [TypeStats(scam_type=key, count=count).model_dump() for key, count in merged.items()]}


@router.get("/trend")
def trend(range: str = Query(default="30d", pattern="^(7d|30d|90d)$"), db: Session = Depends(get_db)) -> dict:
    days = int(range.removesuffix("d"))
    since = datetime.now(timezone.utc) - timedelta(days=days)
    report_day = func.date(ScamReport.created_at)
    alert_day = func.date(ScamAlert.timestamp)
    entity_day = func.date(ScamEntity.created_at)

    report_rows = db.execute(
        select(report_day, func.count(ScamReport.id))
        .where(ScamReport.created_at >= since)
        .group_by(report_day)
    ).all()
    alert_rows = db.execute(
        select(alert_day, func.count(ScamAlert.id))
        .where(ScamAlert.timestamp >= since)
        .group_by(alert_day)
    ).all()
    entity_rows = db.execute(
        select(entity_day, func.count(ScamEntity.id))
        .where(ScamEntity.created_at >= since)
        .group_by(entity_day)
    ).all()
    reports = {str(day): count for day, count in report_rows}
    for day, count in alert_rows:
        reports[str(day)] = reports.get(str(day), 0) + count
    entities = {str(day): count for day, count in entity_rows}
    items = []
    for offset in range_days(days):
        day = (datetime.now(timezone.utc).date() - timedelta(days=offset)).isoformat()
        items.append(TrendStats(date=day, reports=reports.get(day, 0), new_entities=entities.get(day, 0)).model_dump())
    return {"items": items}


def range_days(days: int) -> range:
    return range(days - 1, -1, -1)
