from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.scam_database_entry import ScamDatabaseEntry
from app.models.scam_entity import ScamEntity
from app.services.normalization_service import normalize_entity_value


HIGH_RISK_WORDS = [
    "otp",
    "ma xac minh",
    "mã xác minh",
    "chuyen tien",
    "chuyển tiền",
    "cong an",
    "công an",
    "khoa tai khoan",
    "khóa tài khoản",
    "rut tien",
    "rút tiền",
]

MEDIUM_RISK_WORDS = [
    "trung thuong",
    "trúng thưởng",
    "nhan qua",
    "nhận quà",
    "phi",
    "phí",
    "dat coc",
    "đặt cọc",
    "dau tu",
    "đầu tư",
]


def classify_call_risk(db: Session, phone_number: str, transcript: str | None) -> tuple[str, str, str]:
    normalized = normalize_entity_value("phone", phone_number)
    existing_entity = db.scalar(
        select(ScamEntity).where(
            ScamEntity.entity_type == "phone",
            ScamEntity.normalized_value == normalized,
            ScamEntity.risk_level.in_(["high", "critical"]),
        )
    )
    database_entry = db.scalar(
        select(ScamDatabaseEntry).where(ScamDatabaseEntry.normalized_phone_number == normalized).order_by(
            ScamDatabaseEntry.updated_at.desc()
        )
    )

    if existing_entity or database_entry:
        return (
            database_entry.risk_level if database_entry else existing_entity.risk_level,
            "Thưa bác, số điện thoại này đã có trong dữ liệu cảnh báo lừa đảo của hệ thống.",
            "Bác vui lòng không chuyển tiền, không đọc mã OTP, và nên gọi người thân hoặc ngân hàng chính thức để kiểm tra lại ạ.",
        )

    text = (transcript or "").lower()
    if any(word in text for word in HIGH_RISK_WORDS):
        return (
            "high",
            "Thưa bác, nội dung cuộc gọi có dấu hiệu yêu cầu mã OTP, chuyển tiền, hoặc giả danh cơ quan.",
            "Bác nên dừng cuộc gọi, không cung cấp thông tin cá nhân, và nhờ người thân kiểm tra trước khi làm tiếp ạ.",
        )
    if any(word in text for word in MEDIUM_RISK_WORDS):
        return (
            "medium",
            "Thưa bác, cuộc gọi có một số dấu hiệu đáng nghi như quà tặng, phí, đặt cọc hoặc đầu tư.",
            "Bác đừng vội làm theo. Bác nên hỏi người thân hoặc tra cứu số điện thoại trước ạ.",
        )
    return (
        "low",
        "Thưa bác, hiện chưa thấy dấu hiệu lừa đảo rõ ràng từ thông tin đã nhập.",
        "Bác vẫn nên cẩn thận và không chia sẻ mã OTP, mật khẩu, hoặc thông tin ngân hàng qua điện thoại ạ.",
    )
