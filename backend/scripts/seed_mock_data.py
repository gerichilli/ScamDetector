from __future__ import annotations

import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import Base, SessionLocal, engine
from app.core.security import hash_password
from app.models import (
    CallRecord,
    Notification,
    ScamAlert,
    ScamDatabaseEntry,
    ScamEntity,
    ScamReport,
    User,
)
from app.services.normalization_service import normalize_entity_value


MOCK_USERS = [
    {
        "email": "elder@example.com",
        "password": "StrongPass123",
        "full_name": "Bác Minh",
        "role": "user",
    },
    {
        "email": "relative@example.com",
        "password": "StrongPass123",
        "full_name": "Con gái của bác Minh",
        "role": "user",
    },
    {
        "email": "admin@example.com",
        "password": "AdminPass123",
        "full_name": "Quản trị viên",
        "role": "admin",
    },
]

SCAM_PATTERNS = [
    {
        "phone_number": "0987654321",
        "pattern": "Giả danh ngân hàng xin mã OTP",
        "description": "Người gọi nói tài khoản gặp sự cố và yêu cầu bác đọc mã OTP để xử lý.",
        "risk_level": "critical",
    },
    {
        "phone_number": "0901122334",
        "pattern": "Giả danh công an, dọa liên quan vụ án",
        "description": "Người gọi dọa bác liên quan đến vụ án và yêu cầu chuyển tiền để xác minh.",
        "risk_level": "high",
    },
    {
        "phone_number": "0919988776",
        "pattern": "Thông báo trúng thưởng, yêu cầu đóng phí",
        "description": "Người gọi nói bác đã trúng quà và yêu cầu đóng phí vận chuyển hoặc phí hồ sơ.",
        "risk_level": "medium",
    },
    {
        "phone_number": "0934455667",
        "pattern": "Mời đầu tư lợi nhuận cao",
        "description": "Người gọi hứa lợi nhuận cao, rút tiền nhanh, sau đó yêu cầu bác nạp thêm tiền.",
        "risk_level": "high",
    },
]

CALL_SAMPLES = [
    {
        "phone_number": "0987654321",
        "duration_seconds": 180,
        "transcript": "Tôi là nhân viên ngân hàng. Bác đọc mã OTP để tôi mở khóa tài khoản.",
        "risk_level": "critical",
        "message": "Thưa bác, số điện thoại này đã có trong dữ liệu cảnh báo lừa đảo của hệ thống.",
        "recommended_action": "Bác vui lòng không đọc mã OTP. Bác nên gọi lại ngân hàng bằng số chính thức và báo người thân ạ.",
        "days_ago": 1,
    },
    {
        "phone_number": "0901122334",
        "duration_seconds": 240,
        "transcript": "Đây là công an. Tài khoản của bác liên quan vụ án, cần chuyển tiền xác minh.",
        "risk_level": "high",
        "message": "Thưa bác, cuộc gọi có dấu hiệu giả danh cơ quan và yêu cầu chuyển tiền.",
        "recommended_action": "Bác nên dừng cuộc gọi, không chuyển tiền, và báo người thân kiểm tra giúp ạ.",
        "days_ago": 2,
    },
    {
        "phone_number": "0919988776",
        "duration_seconds": 95,
        "transcript": "Bác đã trúng thưởng, chỉ cần đóng phí nhận quà.",
        "risk_level": "medium",
        "message": "Thưa bác, cuộc gọi có dấu hiệu quà tặng hoặc khoản phí bất thường.",
        "recommended_action": "Bác vui lòng không đóng phí trước. Bác nên kiểm tra lại với người thân ạ.",
        "days_ago": 4,
    },
    {
        "phone_number": "0934455667",
        "duration_seconds": 300,
        "transcript": "Đầu tư gói này lời cao, nạp tiền hôm nay sẽ nhận lại gấp đôi.",
        "risk_level": "high",
        "message": "Thưa bác, cuộc gọi có dấu hiệu đầu tư lợi nhuận cao bất thường.",
        "recommended_action": "Bác không nên nạp tiền. Bác nên hỏi người có kinh nghiệm tài chính trước ạ.",
        "days_ago": 7,
    },
    {
        "phone_number": "0977001122",
        "duration_seconds": 60,
        "transcript": "Shipper gọi xác nhận đơn hàng, không yêu cầu OTP hay chuyển tiền.",
        "risk_level": "low",
        "message": "Thưa bác, hiện chưa thấy dấu hiệu lừa đảo rõ ràng.",
        "recommended_action": "Bác vẫn nên cẩn thận, không chia sẻ mã OTP hoặc mật khẩu qua điện thoại ạ.",
        "days_ago": 10,
    },
]


def get_or_create_user(db, item: dict) -> User:
    user = db.scalar(select(User).where(User.email == item["email"]))
    if user:
        user.full_name = item["full_name"]
        user.role = item["role"]
        user.status = "active"
        return user
    user = User(
        email=item["email"],
        password_hash=hash_password(item["password"]),
        full_name=item["full_name"],
        role=item["role"],
        status="active",
    )
    db.add(user)
    db.flush()
    return user


def upsert_scam_database_entry(db, item: dict) -> ScamDatabaseEntry:
    normalized = normalize_entity_value("phone", item["phone_number"])
    entry = db.scalar(
        select(ScamDatabaseEntry).where(
            ScamDatabaseEntry.normalized_phone_number == normalized,
            ScamDatabaseEntry.pattern == item["pattern"],
        )
    )
    if not entry:
        entry = ScamDatabaseEntry(
            phone_number=item["phone_number"],
            normalized_phone_number=normalized,
            pattern=item["pattern"],
            description=item["description"],
            risk_level=item["risk_level"],
        )
        db.add(entry)
    else:
        entry.description = item["description"]
        entry.risk_level = item["risk_level"]
    return entry


def upsert_scam_entity(db, item: dict) -> ScamEntity:
    normalized = normalize_entity_value("phone", item["phone_number"])
    entity = db.scalar(
        select(ScamEntity).where(
            ScamEntity.entity_type == "phone",
            ScamEntity.normalized_value == normalized,
        )
    )
    if not entity:
        now = datetime.now(timezone.utc) - timedelta(days=12)
        entity = ScamEntity(
            entity_type="phone",
            value=item["phone_number"],
            normalized_value=normalized,
            risk_level=item["risk_level"],
            status="active",
            report_count=3,
            verified_report_count=2,
            first_reported_at=now,
            last_reported_at=datetime.now(timezone.utc),
        )
        db.add(entity)
        db.flush()
    else:
        entity.risk_level = item["risk_level"]
        entity.status = "active"
    return entity


def seed_calls(db, user: User) -> None:
    existing_count = db.scalar(select(CallRecord).where(CallRecord.elderly_user_id == user.id).limit(1))
    if existing_count:
        return

    now = datetime.now(timezone.utc)
    for sample in CALL_SAMPLES:
        call = CallRecord(
            elderly_user_id=user.id,
            phone_number=sample["phone_number"],
            normalized_phone_number=normalize_entity_value("phone", sample["phone_number"]),
            call_time=now - timedelta(days=sample["days_ago"]),
            duration_seconds=sample["duration_seconds"],
            transcript=sample["transcript"],
            note="Dữ liệu mẫu để demo theo system design.",
        )
        db.add(call)
        db.flush()
        alert = ScamAlert(
            call_id=call.id,
            risk_level=sample["risk_level"],
            message=sample["message"],
            recommended_action=sample["recommended_action"],
            timestamp=call.call_time,
        )
        db.add(alert)
        db.flush()
        if sample["risk_level"] in {"high", "critical"}:
            db.add(Notification(alert_id=alert.id, target_user_id=user.id, channel="in_app", sent=True))


def update_existing_call_samples(db, user: User) -> None:
    for sample in CALL_SAMPLES:
        normalized = normalize_entity_value("phone", sample["phone_number"])
        rows = db.execute(
            select(CallRecord, ScamAlert)
            .join(ScamAlert, ScamAlert.call_id == CallRecord.id)
            .where(
                CallRecord.elderly_user_id == user.id,
                CallRecord.normalized_phone_number == normalized,
            )
        ).all()
        for call, alert in rows:
            call.transcript = sample["transcript"]
            call.note = "Dữ liệu mẫu để demo theo system design."
            alert.message = sample["message"]
            alert.recommended_action = sample["recommended_action"]
            alert.risk_level = sample["risk_level"]


def seed_reports(db, user: User) -> None:
    for item in SCAM_PATTERNS[:3]:
        entity = upsert_scam_entity(db, item)
        existing = db.scalar(
            select(ScamReport).where(
                ScamReport.reporter_id == user.id,
                ScamReport.scam_entity_id == entity.id,
                ScamReport.scam_type == item["pattern"],
            )
        )
        if existing:
            continue
        db.add(
            ScamReport(
                reporter_id=user.id,
                scam_entity_id=entity.id,
                scam_type=item["pattern"],
                title=item["pattern"],
                description=item["description"],
                status="approved",
            )
        )


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        users = {item["email"]: get_or_create_user(db, item) for item in MOCK_USERS}
        for pattern in SCAM_PATTERNS:
            upsert_scam_database_entry(db, pattern)
            upsert_scam_entity(db, pattern)
        seed_calls(db, users["elder@example.com"])
        update_existing_call_samples(db, users["elder@example.com"])
        seed_reports(db, users["elder@example.com"])
        db.commit()
        print("Mock database seeded.")
        print("User: elder@example.com / StrongPass123")
        print("Admin: admin@example.com / AdminPass123")
    finally:
        db.close()


if __name__ == "__main__":
    main()
