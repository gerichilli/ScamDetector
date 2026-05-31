import csv
import random
import unicodedata
from pathlib import Path

random.seed(42)

BASE_DIR = Path(__file__).resolve().parents[1]
DATASET_DIR = BASE_DIR / "datasets"
PROCESSED_DIR = DATASET_DIR / "processed"
TEST_SUITE_DIR = DATASET_DIR / "test_suites"
DOCS_DIR = DATASET_DIR / "docs"

PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
TEST_SUITE_DIR.mkdir(parents=True, exist_ok=True)
DOCS_DIR.mkdir(parents=True, exist_ok=True)

FIELDS = [
    "id",
    "base_case_id",
    "text",
    "label",
    "scam_type",
    "severity",
    "reason",
    "evidence_span",
    "recommended_action",
    "risk_factor",
    "harm_type",
    "target_group",
    "region_variant",
    "noise_type",
    "source",
    "license",
    "is_synthetic",
    "privacy_level",
    "split",
]


def remove_accents(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
    return text.replace("đ", "d").replace("Đ", "D")


def add_typo(text: str) -> str:
    replacements = {
        "tài khoản": "tai khoang",
        "xác minh": "xac mih",
        "chuyển": "chuyen",
        "ngân hàng": "ngan hang",
        "khẩn cấp": "khan cap",
        "ngay": "ngai",
        "mã": "ma",
        "tiền": "tien",
    }
    for src, dst in replacements.items():
        if src in text:
            text = text.replace(src, dst, 1)
            break
    return text


def add_abbreviation(text: str) -> str:
    replacements = {
        "chuyển khoản": "ck",
        "chuyển tiền": "ck",
        "số tài khoản": "stk",
        "tài khoản": "tk",
        "5 triệu": "5tr",
        "10 triệu": "10tr",
        "xác minh": "xm",
        "ngân hàng": "NH",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def add_obfuscation(text: str) -> str:
    replacements = {
        "OTP": "OT P",
        "mã xác nhận": "dãy 6 số",
        "chuyển tiền": "gửi tiền qua giúp",
        "bấm link": "mở đường dẫn",
        "tài khoản": "t.khoản",
    }
    for src, dst in replacements.items():
        text = text.replace(src, dst)
    return text


def add_code_switching(text: str) -> str:
    if "xác minh" in text:
        return text.replace("xác minh", "verify")
    if "tài khoản" in text:
        return text.replace("tài khoản", "account")
    return text + " please check now"


def apply_noise(text: str, noise_type: str) -> str:
    if noise_type == "NO_DIACRITICS":
        return remove_accents(text)
    if noise_type == "TYPO":
        return add_typo(remove_accents(text))
    if noise_type == "ABBREVIATION":
        return add_abbreviation(text)
    if noise_type == "OBFUSCATION":
        return add_obfuscation(text)
    if noise_type == "CODE_SWITCHING":
        return add_code_switching(text)
    if noise_type == "LONG_CONTEXT":
        return "Cô/chú cứ bình tĩnh, bên cháu hỗ trợ nhanh thôi. " + text + " Làm ngay để tránh bị khóa dịch vụ."
    if noise_type == "MIXED_INTENT":
        return "Con hỏi thăm sức khỏe chút. " + text
    return text


def get_split(base_case_id: str) -> str:
    value = sum(ord(c) for c in base_case_id) % 100
    if value < 70:
        return "train"
    if value < 85:
        return "valid"
    return "test"


PRONOUNS = {
    "STANDARD": ["Cô", "Chú", "Bác"],
    "NORTH": ["Bác", "Cô", "Chú"],
    "CENTRAL": ["O", "Mệ", "Bác"],
    "SOUTH": ["Cô", "Chú", "Má", "Ba"],
}

NOISE_TYPES = [
    "NONE",
    "NO_DIACRITICS",
    "TYPO",
    "ABBREVIATION",
    "OBFUSCATION",
    "CODE_SWITCHING",
    "LONG_CONTEXT",
    "MIXED_INTENT",
]

SCAM_TEMPLATES = [
    {
        "scam_type": "OTP_BANK",
        "severity": "HIGH",
        "templates": [
            "{p} gửi mã OTP vừa nhận được để ngân hàng xác minh tài khoản ngay nhé.",
            "Tài khoản của {p_lower} đang bị khóa, gửi mã xác nhận để mở lại.",
            "{p} đọc giúp cháu dãy 6 số vừa gửi về điện thoại để hoàn tất xác minh.",
            "Ngân hàng cần kiểm tra bảo mật, {p_lower} cung cấp mã OTP ngay để tránh khóa tài khoản.",
        ],
        "reason": "Yêu cầu cung cấp OTP hoặc mã xác nhận ngân hàng.",
        "evidence_span": "mã OTP; mã xác nhận; dãy 6 số",
        "recommended_action": "Không cung cấp OTP hoặc mã xác nhận. Gọi trực tiếp ngân hàng để kiểm tra.",
        "risk_factor": "urgency; technical_confusion",
        "harm_type": "credential_theft",
    },
    {
        "scam_type": "FAKE_POLICE",
        "severity": "HIGH",
        "templates": [
            "Chúng tôi là công an, {p_lower} đang liên quan đến vụ án rửa tiền, cần chuyển tiền để điều tra.",
            "{p} không được nói với ai, hãy chuyển tiền vào tài khoản tạm giữ để phục vụ xác minh.",
            "Bên viện kiểm sát yêu cầu {p_lower} hợp tác ngay, nếu không sẽ bị phong tỏa tài sản.",
            "{p} đang bị nghi ngờ liên quan đường dây lừa đảo, cần làm theo hướng dẫn ngay.",
        ],
        "reason": "Giả danh cơ quan chức năng, đe dọa và yêu cầu chuyển tiền.",
        "evidence_span": "công an; viện kiểm sát; vụ án; chuyển tiền",
        "recommended_action": "Không chuyển tiền. Gọi người thân hoặc cơ quan công an địa phương để xác minh.",
        "risk_factor": "authority_impersonation; fear; secrecy",
        "harm_type": "financial_loss",
    },
    {
        "scam_type": "EMERGENCY_MONEY",
        "severity": "HIGH",
        "templates": [
            "Mẹ ơi con đang cấp cứu, chuyển gấp cho con 5 triệu, đừng gọi lại.",
            "{p} ơi con bị tai nạn, gửi tiền ngay vào số tài khoản này giúp con.",
            "Con đang gặp chuyện gấp, {p_lower} chuyển khoản liền cho con 10 triệu nha.",
            "{p} đừng hỏi nhiều, con cần tiền xử lý việc khẩn cấp, chuyển ngay giúp con.",
        ],
        "reason": "Giả danh người thân, tạo tình huống khẩn cấp và yêu cầu chuyển tiền.",
        "evidence_span": "cấp cứu; chuyển gấp; đừng gọi lại; khẩn cấp",
        "recommended_action": "Không chuyển tiền vội. Gọi trực tiếp cho người thân qua số quen thuộc để xác minh.",
        "risk_factor": "urgency; trust_abuse; secrecy",
        "harm_type": "financial_loss",
    },
    {
        "scam_type": "PHISHING_LINK",
        "severity": "HIGH",
        "templates": [
            "{p} bấm link <LINK> để xác minh tài khoản trước khi bị khóa.",
            "Đơn hàng của {p_lower} gặp lỗi, bấm vào <LINK> để cập nhật thông tin nhận hàng.",
            "Vui lòng truy cập <LINK> để nhận hỗ trợ hoàn tiền.",
            "{p} cần đăng nhập vào <LINK> để kiểm tra giao dịch bất thường.",
        ],
        "reason": "Dụ người dùng bấm link lạ để đánh cắp thông tin.",
        "evidence_span": "<LINK>; bấm link; đăng nhập",
        "recommended_action": "Không bấm link lạ. Chỉ truy cập website hoặc ứng dụng chính thức.",
        "risk_factor": "technical_confusion; urgency",
        "harm_type": "credential_theft; malware_install",
    },
    {
        "scam_type": "PRIZE_GIFT",
        "severity": "HIGH",
        "templates": [
            "Chúc mừng {p_lower} đã trúng xe máy, bấm <LINK> để nhận quà.",
            "{p} được chọn nhận phần thưởng 20 triệu, vui lòng đóng phí hồ sơ trước.",
            "Bên em tặng {p_lower} phần quà tri ân, cần cung cấp thông tin cá nhân để nhận.",
            "{p} trúng thưởng may mắn, chuyển phí vận chuyển để nhận quà ngay hôm nay.",
        ],
        "reason": "Dùng quà tặng hoặc trúng thưởng để dụ cung cấp thông tin hoặc chuyển phí.",
        "evidence_span": "trúng thưởng; nhận quà; đóng phí; chuyển phí",
        "recommended_action": "Không chuyển phí hoặc cung cấp thông tin cá nhân để nhận quà không rõ nguồn.",
        "risk_factor": "greed; urgency",
        "harm_type": "financial_loss; privacy_leak",
    },
    {
        "scam_type": "INVESTMENT",
        "severity": "HIGH",
        "templates": [
            "{p} đầu tư 3 triệu hôm nay, cam kết nhận lãi 30% sau một tuần.",
            "Bên em có sàn đầu tư lợi nhuận cao, {p_lower} nạp tiền sớm để giữ suất.",
            "Cơ hội sinh lời bảo đảm, {p_lower} chỉ cần chuyển tiền là có chuyên gia hỗ trợ.",
            "{p} tham gia nhóm đầu tư nội bộ, lợi nhuận chắc chắn không rủi ro.",
        ],
        "reason": "Hứa lợi nhuận cao bất thường và yêu cầu nạp/chuyển tiền.",
        "evidence_span": "lãi 30%; lợi nhuận cao; nạp tiền; chuyển tiền",
        "recommended_action": "Không chuyển tiền vào kênh đầu tư không rõ pháp lý. Hỏi người thân hoặc chuyên gia tài chính.",
        "risk_factor": "greed; false_promise",
        "harm_type": "financial_loss",
    },
    {
        "scam_type": "JOB_SCAM",
        "severity": "MEDIUM",
        "templates": [
            "{p} chỉ cần làm nhiệm vụ online, nạp trước 300 nghìn để nhận việc.",
            "Việc nhẹ lương cao, {p_lower} đóng phí hồ sơ là có thể bắt đầu ngay.",
            "Bên em tuyển cộng tác viên tại nhà, cần chuyển tiền kích hoạt tài khoản.",
            "{p} nhận job online, hoàn thành đơn đầu tiên sẽ được hoàn tiền và thưởng.",
        ],
        "reason": "Lừa việc làm online, yêu cầu đóng phí hoặc nạp tiền trước.",
        "evidence_span": "nạp trước; đóng phí; kích hoạt tài khoản",
        "recommended_action": "Không đóng phí để nhận việc. Kiểm tra công ty và hợp đồng rõ ràng.",
        "risk_factor": "financial_pressure; false_promise",
        "harm_type": "financial_loss",
    },
    {
        "scam_type": "LOAN_SCAM",
        "severity": "HIGH",
        "templates": [
            "{p} được duyệt vay 50 triệu, cần đóng phí bảo hiểm trước để giải ngân.",
            "Hồ sơ vay của {p_lower} đã được chấp nhận, chuyển phí xác minh để nhận tiền.",
            "{p} muốn vay nhanh không cần gặp mặt thì gửi CCCD và phí hồ sơ trước.",
            "Bên em hỗ trợ vay gấp, {p_lower} đóng phí mở hồ sơ là nhận tiền trong ngày.",
        ],
        "reason": "Lừa vay tiền, yêu cầu đóng phí trước hoặc gửi giấy tờ cá nhân.",
        "evidence_span": "đóng phí; giải ngân; gửi CCCD; phí hồ sơ",
        "recommended_action": "Không gửi giấy tờ cá nhân hoặc đóng phí trước cho dịch vụ vay không rõ nguồn.",
        "risk_factor": "financial_pressure; urgency",
        "harm_type": "financial_loss; identity_theft",
    },
]


SAFE_TEMPLATES = [
    "Mai con về nhà ăn cơm với ba mẹ.",
    "{p} nhớ uống thuốc đúng giờ nha.",
    "Con đã chuyển tiền mua thuốc cho mẹ rồi.",
    "Mã đơn hàng của {p_lower} là 123456, hàng sẽ giao trong hôm nay.",
    "Ngân hàng thông báo bảo trì hệ thống vào tối nay, không yêu cầu cung cấp thông tin.",
    "{p} kiểm tra giúp con lịch hẹn khám bệnh ngày mai nhé.",
    "Con gửi link bài báo này cho {p_lower} đọc thử.",
    "Hôm nay trời mưa, {p_lower} nhớ mang áo mưa.",
    "Con đặt xe cho {p_lower} rồi, tài xế sẽ đến trong 10 phút.",
    "{p} ơi, tối nay cả nhà gọi video nhé.",
]


SUSPICIOUS_TEMPLATES = [
    "{p} xác minh tài khoản giúp bên em trong hôm nay nhé.",
    "Bên em cần kiểm tra thông tin cá nhân của {p_lower} để hỗ trợ.",
    "{p} bấm vào đường dẫn này để xem chi tiết chương trình.",
    "Em có cơ hội đầu tư muốn giới thiệu cho {p_lower}.",
    "Tài khoản của {p_lower} có dấu hiệu bất thường, vui lòng phản hồi sớm.",
    "{p} gửi thông tin để bên em cập nhật hồ sơ.",
    "Bên em cần {p_lower} xác nhận giao dịch này ngay hôm nay.",
]


def build_row(
    idx,
    base_case_id,
    text,
    label,
    scam_type,
    severity,
    reason,
    evidence_span,
    recommended_action,
    risk_factor,
    harm_type,
    target_group,
    region_variant,
    noise_type,
):
    return {
        "id": f"VN_{idx:06d}",
        "base_case_id": base_case_id,
        "text": text,
        "label": label,
        "scam_type": scam_type,
        "severity": severity,
        "reason": reason,
        "evidence_span": evidence_span,
        "recommended_action": recommended_action,
        "risk_factor": risk_factor,
        "harm_type": harm_type,
        "target_group": target_group,
        "region_variant": region_variant,
        "noise_type": noise_type,
        "source": "vietnamese_synthetic",
        "license": "self-created",
        "is_synthetic": "true",
        "privacy_level": "no_pii",
        "split": get_split(base_case_id),
    }


def generate_dataset(total_scam=600, total_safe=400, total_suspicious=200):
    rows = []
    seen_texts = set()
    idx = 1

    scam_count = 0
    safe_count = 0
    suspicious_count = 0

    def make_unique(text: str, label: str, idx_value: int) -> str:
        """
        Avoid infinite loop when templates are limited.
        If duplicated, add a natural short suffix.
        """
        text = text.strip()

        if text not in seen_texts:
            seen_texts.add(text)
            return text

        base = text[:-1] if text.endswith(".") else text

        if label == "SAFE":
            suffixes = [
                " nha.",
                " nhé.",
                " ạ.",
                " khi nào rảnh nha.",
                " cho con biết nhé.",
                " để con yên tâm nha.",
                " chiều nay cũng được nha.",
                " tối con gọi lại nhé.",
            ]
        elif label == "SCAM":
            suffixes = [
                " Làm ngay giúp bên cháu.",
                " Xử lý trong hôm nay giúp cháu.",
                " Bên cháu đang chờ phản hồi.",
                " Nếu chậm trễ tài khoản có thể bị khóa.",
                " Vui lòng làm ngay để tránh mất quyền lợi.",
                " Không nên chia sẻ việc này với ai.",
                " Đây là yêu cầu khẩn cấp.",
                " Hoàn tất sớm giúp bên em.",
            ]
        else:
            suffixes = [
                " giúp bên em nhé.",
                " trong hôm nay giúp em.",
                " để bên em kiểm tra lại.",
                " nếu cần em sẽ hướng dẫn thêm.",
                " phản hồi sớm giúp em nha.",
            ]

        for suffix in suffixes:
            candidate = base + suffix
            if candidate not in seen_texts:
                seen_texts.add(candidate)
                return candidate

        candidate = f"{base} Mã tham chiếu {idx_value}."
        seen_texts.add(candidate)
        return candidate

    # Generate SCAM rows
    max_attempts = total_scam * 50
    attempts = 0

    while scam_count < total_scam and attempts < max_attempts:
        attempts += 1

        scam = random.choice(SCAM_TEMPLATES)
        region = random.choice(list(PRONOUNS.keys()))
        p = random.choice(PRONOUNS[region])
        text_template = random.choice(scam["templates"])
        text = text_template.format(p=p, p_lower=p.lower())

        noise = random.choices(
            NOISE_TYPES,
            weights=[45, 15, 10, 8, 8, 5, 5, 4],
            k=1,
        )[0]

        noisy_text = apply_noise(text, noise)
        noisy_text = make_unique(noisy_text, "SCAM", idx)

        scam_count += 1
        base_case_id = f"{scam['scam_type']}_{scam_count:04d}"

        row = build_row(
            idx=idx,
            base_case_id=base_case_id,
            text=noisy_text,
            label="SCAM",
            scam_type=scam["scam_type"],
            severity=scam["severity"],
            reason=scam["reason"],
            evidence_span=scam["evidence_span"],
            recommended_action=scam["recommended_action"],
            risk_factor=scam["risk_factor"],
            harm_type=scam["harm_type"],
            target_group="elderly",
            region_variant=region,
            noise_type=noise,
        )
        rows.append(row)
        idx += 1

    # Generate SAFE rows
    max_attempts = total_safe * 50
    attempts = 0

    while safe_count < total_safe and attempts < max_attempts:
        attempts += 1

        region = random.choice(list(PRONOUNS.keys()))
        p = random.choice(PRONOUNS[region])
        text_template = random.choice(SAFE_TEMPLATES)
        text = text_template.format(p=p, p_lower=p.lower())

        noise = random.choices(
            ["NONE", "NO_DIACRITICS", "TYPO", "ABBREVIATION"],
            weights=[70, 15, 10, 5],
            k=1,
        )[0]

        noisy_text = apply_noise(text, noise)
        noisy_text = make_unique(noisy_text, "SAFE", idx)

        safe_count += 1
        base_case_id = f"SAFE_{safe_count:04d}"

        row = build_row(
            idx=idx,
            base_case_id=base_case_id,
            text=noisy_text,
            label="SAFE",
            scam_type="NONE",
            severity="LOW",
            reason="Nội dung bình thường hoặc không có yêu cầu nguy hiểm.",
            evidence_span="",
            recommended_action="Không cần cảnh báo. Có thể tiếp tục trò chuyện bình thường.",
            risk_factor="none",
            harm_type="none",
            target_group="general",
            region_variant=region,
            noise_type=noise,
        )
        rows.append(row)
        idx += 1

    # Generate SUSPICIOUS rows
    max_attempts = total_suspicious * 50
    attempts = 0

    while suspicious_count < total_suspicious and attempts < max_attempts:
        attempts += 1

        region = random.choice(list(PRONOUNS.keys()))
        p = random.choice(PRONOUNS[region])
        text_template = random.choice(SUSPICIOUS_TEMPLATES)
        text = text_template.format(p=p, p_lower=p.lower())

        noise = random.choices(
            ["NONE", "NO_DIACRITICS", "TYPO", "ABBREVIATION", "OBFUSCATION"],
            weights=[55, 15, 10, 10, 10],
            k=1,
        )[0]

        noisy_text = apply_noise(text, noise)
        noisy_text = make_unique(noisy_text, "SUSPICIOUS", idx)

        suspicious_count += 1
        base_case_id = f"SUSPICIOUS_{suspicious_count:04d}"

        row = build_row(
            idx=idx,
            base_case_id=base_case_id,
            text=noisy_text,
            label="SUSPICIOUS",
            scam_type="UNKNOWN",
            severity="MEDIUM",
            reason="Nội dung có yêu cầu xác minh hoặc cung cấp thông tin nhưng chưa đủ bằng chứng kết luận lừa đảo.",
            evidence_span="xác minh; thông tin cá nhân; đường dẫn; phản hồi sớm",
            recommended_action="Cần kiểm tra nguồn gửi. Không cung cấp thông tin nhạy cảm nếu chưa xác minh.",
            risk_factor="uncertainty; possible_social_engineering",
            harm_type="privacy_leak",
            target_group="general",
            region_variant=region,
            noise_type=noise,
        )
        rows.append(row)
        idx += 1

    random.shuffle(rows)

    print(f"Generated SCAM: {scam_count}")
    print(f"Generated SAFE: {safe_count}")
    print(f"Generated SUSPICIOUS: {suspicious_count}")

    return rows

def write_csv(path: Path, rows):
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def main():
    rows = generate_dataset()

    full_path = PROCESSED_DIR / "vietnamese_synthetic_full.csv"
    write_csv(full_path, rows)

    train_rows = [r for r in rows if r["split"] == "train"]
    valid_rows = [r for r in rows if r["split"] == "valid"]
    test_rows = [r for r in rows if r["split"] == "test"]

    write_csv(PROCESSED_DIR / "train.csv", train_rows)
    write_csv(PROCESSED_DIR / "valid.csv", valid_rows)
    write_csv(PROCESSED_DIR / "test.csv", test_rows)

    fairness_rows = [
        r for r in rows
        if r["region_variant"] in ["NORTH", "CENTRAL", "SOUTH"]
    ][:150]

    robustness_rows = [
        r for r in rows
        if r["noise_type"] != "NONE"
    ][:150]

    explainability_rows = [
        r for r in rows
        if r["label"] in ["SCAM", "SUSPICIOUS"] and r["evidence_span"]
    ][:100]

    write_csv(TEST_SUITE_DIR / "fairness_test.csv", fairness_rows)
    write_csv(TEST_SUITE_DIR / "robustness_test.csv", robustness_rows)
    write_csv(TEST_SUITE_DIR / "explainability_test.csv", explainability_rows)

    print("Generated dataset successfully.")
    print(f"Full dataset: {full_path}")
    print(f"Total rows: {len(rows)}")
    print(f"Train rows: {len(train_rows)}")
    print(f"Valid rows: {len(valid_rows)}")
    print(f"Test rows: {len(test_rows)}")
    print(f"Fairness test rows: {len(fairness_rows)}")
    print(f"Robustness test rows: {len(robustness_rows)}")
    print(f"Explainability test rows: {len(explainability_rows)}")


if __name__ == "__main__":
    main()