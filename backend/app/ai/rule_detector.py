from typing import Dict, List, Any


RULES = [
    {
        "name": "Yêu cầu cung cấp OTP hoặc mã xác nhận",
        "scam_type": "OTP_BANK",
        "keywords": ["otp", "mã otp", "mã xác nhận", "dãy 6 số", "ma xac nhan", "verification code"],
        "weight": 0.95,
    },
    {
        "name": "Yêu cầu chuyển tiền gấp",
        "scam_type": "EMERGENCY_MONEY",
        "keywords": ["chuyển gấp", "chuyển tiền", "ck gấp", "ck gap", "5tr", "10tr", "gửi tiền ngay"],
        "weight": 0.85,
    },
    {
        "name": "Tạo cảm giác khẩn cấp",
        "scam_type": "UNKNOWN",
        "keywords": ["gấp", "ngay lập tức", "trong hôm nay", "khẩn cấp", "ngay bây giờ", "gap"],
        "weight": 0.5,
    },
    {
        "name": "Giả danh công an/cơ quan chức năng",
        "scam_type": "FAKE_POLICE",
        "keywords": ["công an", "viện kiểm sát", "tòa án", "vụ án", "rửa tiền", "điều tra", "phong tỏa tài sản"],
        "weight": 0.95,
    },
    {
        "name": "Dụ bấm link lạ",
        "scam_type": "PHISHING_LINK",
        "keywords": ["<link>", "bấm link", "nhấp link", "truy cập", "đường dẫn", "click", "link"],
        "weight": 0.85,
    },
    {
        "name": "Thông báo trúng thưởng/nhận quà",
        "scam_type": "PRIZE_GIFT",
        "keywords": ["trúng thưởng", "nhận quà", "phần thưởng", "quà tặng", "đóng phí nhận quà"],
        "weight": 0.8,
    },
    {
        "name": "Yêu cầu giữ bí mật hoặc ngăn xác minh",
        "scam_type": "UNKNOWN",
        "keywords": ["đừng gọi lại", "không được nói với ai", "giữ bí mật", "đừng báo công an", "dung goi lai"],
        "weight": 0.8,
    },
    {
        "name": "Đầu tư lợi nhuận cao bất thường",
        "scam_type": "INVESTMENT",
        "keywords": ["lãi 30%", "lợi nhuận cao", "đầu tư", "cam kết lợi nhuận", "không rủi ro"],
        "weight": 0.75,
    },
    {
        "name": "Việc làm online yêu cầu nạp tiền",
        "scam_type": "JOB_SCAM",
        "keywords": ["việc online", "nhiệm vụ online", "nạp trước", "đóng phí hồ sơ", "kích hoạt tài khoản"],
        "weight": 0.75,
    },
]


def detect_by_rules(text: str) -> Dict[str, Any]:
    lower_text = text.lower()

    triggered_rules: List[str] = []
    scam_types: List[str] = []
    score = 0.0

    for rule in RULES:
        matched = any(keyword.lower() in lower_text for keyword in rule["keywords"])

        if matched:
            triggered_rules.append(rule["name"])
            scam_types.append(rule["scam_type"])
            score += rule["weight"]

    # Normalize score về 0-1
    score = min(score, 1.0)

    # Chọn scam_type xuất hiện đầu tiên khác UNKNOWN
    final_scam_type = "UNKNOWN"
    for scam_type in scam_types:
        if scam_type != "UNKNOWN":
            final_scam_type = scam_type
            break

    return {
        "rule_score": float(score),
        "triggered_rules": triggered_rules,
        "rule_scam_type": final_scam_type,
    }