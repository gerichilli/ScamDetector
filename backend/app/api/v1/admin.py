from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import require_admin
from app.core.database import get_db
from app.models.evidence import ReportEvidence
from app.models.scam_entity import ScamEntity
from app.models.scam_report import ScamReport
from app.models.user import User
from app.schemas.admin import ModerationRequest
from app.schemas.report import ReportDetail, ReportListItem

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reports")
def reports_queue(
    status: str | None = Query(default="pending"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    query = select(ScamReport, ScamEntity).join(ScamEntity, ScamReport.scam_entity_id == ScamEntity.id)
    if status:
        query = query.where(ScamReport.status == status)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.execute(query.order_by(ScamReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    items = [
        ReportListItem(
            id=report.id,
            entity_type=entity.entity_type,
            entity_value=entity.value,
            scam_type=report.scam_type,
            status=report.status,
            created_at=report.created_at,
        ).model_dump()
        for report, entity in rows
    ]
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.get("/reports/{report_id}", response_model=ReportDetail)
def report_detail(
    report_id: str,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> ReportDetail:
    row = db.execute(
        select(ScamReport, ScamEntity).join(ScamEntity, ScamReport.scam_entity_id == ScamEntity.id).where(ScamReport.id == report_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    report, entity = row
    evidence = db.scalars(select(ReportEvidence).where(ReportEvidence.report_id == report.id)).all()
    return ReportDetail(
        id=report.id,
        reporter_id=report.reporter_id,
        scam_entity_id=report.scam_entity_id,
        entity_type=entity.entity_type,
        entity_value=entity.value,
        scam_type=report.scam_type,
        title=report.title,
        description=report.description,
        amount_lost=report.amount_lost,
        currency=report.currency,
        incident_date=report.incident_date,
        status=report.status,
        moderator_note=report.moderator_note,
        evidence_urls=[item.file_url for item in evidence],
        created_at=report.created_at,
    )


@router.patch("/reports/{report_id}/moderate", response_model=ReportDetail)
def moderate_report(
    report_id: str,
    payload: ModerationRequest,
    db: Session = Depends(get_db),
    moderator: User = Depends(require_admin),
) -> ReportDetail:
    row = db.execute(
        select(ScamReport, ScamEntity).join(ScamEntity, ScamReport.scam_entity_id == ScamEntity.id).where(ScamReport.id == report_id)
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Report not found")
    report, entity = row

    was_approved = report.status == "approved"
    report.status = payload.status
    report.moderator_id = moderator.id
    report.moderator_note = payload.moderator_note

    if payload.status == "approved" and not was_approved:
        entity.verified_report_count += 1
        entity.status = "active"
    if payload.status == "rejected" and was_approved and entity.verified_report_count > 0:
        entity.verified_report_count -= 1
    if payload.risk_level:
        entity.risk_level = payload.risk_level
    elif entity.verified_report_count >= 10:
        entity.risk_level = "critical"
    elif entity.verified_report_count >= 5:
        entity.risk_level = "high"
    elif entity.verified_report_count >= 2:
        entity.risk_level = "medium"
    else:
        entity.risk_level = "low"

    db.commit()
    return report_detail(report_id, db, moderator)


@router.get("/entities")
def list_entities(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin),
) -> dict:
    query = select(ScamEntity)
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    rows = db.scalars(query.order_by(ScamEntity.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
    return {
        "items": [
            {
                "id": item.id,
                "entity_type": item.entity_type,
                "value": item.value,
                "risk_level": item.risk_level,
                "status": item.status,
                "report_count": item.report_count,
                "verified_report_count": item.verified_report_count,
            }
            for item in rows
        ],
        "total": total,
        "page": page,
        "page_size": page_size,
    }
