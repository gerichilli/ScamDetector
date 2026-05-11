from datetime import date, datetime, timezone
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.core.config import get_settings
from app.core.database import get_db
from app.models.evidence import ReportEvidence
from app.models.scam_entity import ScamEntity
from app.models.scam_report import ScamReport
from app.models.user import User
from app.schemas.report import ReportCreateResponse, ReportListItem
from app.services.normalization_service import infer_file_type, normalize_entity_value

router = APIRouter(prefix="/reports", tags=["reports"])


def get_or_create_entity(db: Session, entity_type: str, entity_value: str) -> ScamEntity:
    normalized = normalize_entity_value(entity_type, entity_value)
    entity = db.scalar(
        select(ScamEntity).where(
            ScamEntity.entity_type == entity_type,
            ScamEntity.normalized_value == normalized,
        )
    )
    now = datetime.now(timezone.utc)
    if entity:
        entity.report_count += 1
        entity.last_reported_at = now
        return entity

    entity = ScamEntity(
        entity_type=entity_type,
        value=entity_value,
        normalized_value=normalized,
        report_count=1,
        first_reported_at=now,
        last_reported_at=now,
    )
    db.add(entity)
    db.flush()
    return entity


@router.post("", response_model=ReportCreateResponse)
async def create_report(
    entity_type: str = Form(pattern="^(phone|bank_account|e_wallet|social_account)$"),
    entity_value: str = Form(min_length=2),
    scam_type: str = Form(min_length=2),
    title: str | None = Form(default=None),
    description: str = Form(min_length=10),
    amount_lost: Decimal | None = Form(default=None),
    currency: str = Form(default="VND"),
    incident_date: date | None = Form(default=None),
    evidence_files: list[UploadFile] | None = File(default=None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReportCreateResponse:
    entity = get_or_create_entity(db, entity_type, entity_value)
    report = ScamReport(
        reporter_id=user.id,
        scam_entity_id=entity.id,
        scam_type=scam_type,
        title=title,
        description=description,
        amount_lost=amount_lost,
        currency=currency,
        incident_date=incident_date,
    )
    db.add(report)
    db.flush()

    settings = get_settings()
    upload_dir = Path(settings.upload_dir)
    upload_dir.mkdir(parents=True, exist_ok=True)
    for file in evidence_files or []:
        if not file.filename:
            continue
        safe_name = f"{uuid4()}-{Path(file.filename).name}"
        target = upload_dir / safe_name
        target.write_bytes(await file.read())
        db.add(
            ReportEvidence(
                report_id=report.id,
                file_url=f"/uploads/{safe_name}",
                file_type=infer_file_type(file.filename),
            )
        )

    db.commit()
    db.refresh(report)
    return ReportCreateResponse(id=report.id, status=report.status, scam_entity_id=entity.id, created_at=report.created_at)


@router.get("/my")
def my_reports(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
) -> dict:
    base = select(ScamReport, ScamEntity).join(ScamEntity, ScamReport.scam_entity_id == ScamEntity.id).where(
        ScamReport.reporter_id == user.id
    )
    total = db.scalar(select(func.count()).select_from(base.subquery())) or 0
    rows = db.execute(base.order_by(ScamReport.created_at.desc()).offset((page - 1) * page_size).limit(page_size)).all()
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
