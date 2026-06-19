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
    {
        "name": "Vay tiền nhanh yêu cầu phí trước",
        "scam_type": "LOAN_SCAM",
        "keywords": [
            "vay gấp", "vay nhanh", "duyệt vay", "duyet vay", "hồ sơ vay", "ho so vay",
            "vay tiêu dùng", "vay tieu dung", "tài khoản nhận vay", "tai khoan nhan vay",
            "giải ngân", "giai ngan", "phí hồ sơ", "phi ho so", "phí bảo hiểm",
            "phi bao hiem", "phí xác minh", "phi xac minh", "nợ xấu", "no xau",
            "hợp đồng vay", "hop dong vay", "nhập sai số", "nhap sai so", "lỗi hồ sơ",
            "loi ho so", "phí xm", "phi xm", "t.khoản nhận vay", "t.khoan nhan vay",
        ],
        "weight": 0.9,
    },
    {
        "name": "Giả danh hỗ trợ kỹ thuật/dịch vụ",
        "scam_type": "FAKE_SUPPORT",
        "keywords": [
            "hỗ trợ kỹ thuật", "ho tro ky thuat", "tổng đài", "tong dai", "nhà mạng",
            "nha mang", "chuẩn hóa sim", "chuan hoa sim", "sim bị khóa", "sim bi khoa",
            "cài ứng dụng", "cai ung dung", "app điều khiển", "app dieu khien",
            "điều khiển từ xa", "dieu khien tu xa", "chia sẻ màn hình",
            "chia se man hinh", "cấp quyền", "cap quyen", "đồng bộ dữ liệu",
            "dong bo du lieu",
        ],
        "weight": 0.92,
    },
    {
        "name": "Cuộc gọi deepfake/giả giọng người thân",
        "scam_type": "DEEPFAKE_CALL",
        "keywords": [
            "deepfake", "giả giọng", "gia giong", "giọng giống", "giong giong",
            "giống con", "giong con", "giống cháu", "giong chau", "video mờ",
            "video mo", "hình ảnh bị giật", "hinh anh bi giat", "tắt camera",
            "tat camera", "mạng yếu", "mang yeu", "account mạng xã hội mới tạo",
            "account mang xa hoi moi tao", "ảnh đại diện của người thân",
            "anh dai dien cua nguoi than", "khuôn mặt giống", "khuon mat giong",
            "cuộc gọi video", "cuoc goi video", "giống người thân", "giong nguoi than",
        ],
        "weight": 0.96,
    },
    {
        "name": "Dụ mua sản phẩm sức khỏe không rõ nguồn",
        "scam_type": "HEALTH_PRODUCT",
        "keywords": [
            "hội thảo sức khỏe", "hoi thao suc khoe", "sản phẩm sức khỏe",
            "san pham suc khoe", "thuốc chữa bệnh", "thuoc chua benh",
            "bệnh mãn tính", "benh man tinh", "suất ưu đãi dành riêng cho người cao tuổi",
            "suat uu dai danh rieng cho nguoi cao tuoi", "mua nhiều hộp",
            "mua nhieu hop", "lên hạng thành viên", "len hang thanh vien",
            "hoa hồng", "hoa hong", "thiếu căn cứ y khoa", "thieu can cu y khoa",
            "lời chứng thực", "loi chung thuc", "người lớn tuổi khác",
            "nguoi lon tuoi khac", "suất ưu đãi", "suat uu dai",
        ],
        "weight": 0.92,
    },
    {
        "name": "Combo du lịch/khách sạn giá rẻ yêu cầu đặt cọc",
        "scam_type": "TRAVEL_COMBO",
        "keywords": [
            "combo du lịch", "combo du lich", "combo nghỉ dưỡng", "combo nghi duong",
            "khách sạn đang khuyến mãi", "khach san dang khuyen mai",
            "giá rẻ hơn thị trường", "gia re hon thi truong", "ảnh phòng đẹp",
            "anh phong dep", "đánh giá ảo", "danh gia ao", "giữ phòng",
            "giu phong", "đặt cọc", "dat coc", "xuất voucher", "xuat voucher",
            "mất suất khuyến mãi", "mat suat khuyen mai", "thanh toán toàn bộ",
            "thanh toan toan bo", "ảnh voucher", "anh voucher", "hai suất",
            "hai suat", "đi cùng gia đình", "di cung gia dinh",
        ],
        "weight": 0.92,
    },
    {
        "name": "Lừa đảo tình cảm qua mạng",
        "scam_type": "ROMANCE_SCAM",
        "keywords": [
            "quen qua mạng", "quen qua mang", "lời thân mật", "loi than mat",
            "gửi quà", "gui qua", "phí hải quan", "phi hai quan",
            "sắp về việt nam", "sap ve viet nam", "sống ở nước ngoài",
            "song o nuoc ngoai", "rắc rối giấy tờ", "rac roi giay to",
            "lời lẽ tình cảm", "loi le tinh cam", "ngại từ chối", "ngai tu choi",
            "hoàn lại gấp đôi", "hoan lai gap doi", "tài khoản đang bị khóa",
            "tai khoan dang bi khoa", "nhắn tin nhiều tuần", "nhan tin nhieu tuan",
        ],
        "weight": 0.92,
    },
    {
        "name": "Lừa thanh toán/hoàn tiền qua tài khoản lạ",
        "scam_type": "PAYMENT_SCAM",
        "keywords": [
            "thanh toán thất bại", "thanh toan that bai", "xác nhận thanh toán",
            "xac nhan thanh toan", "cập nhật phương thức thanh toán",
            "cap nhat phuong thuc thanh toan", "hoàn tiền", "hoan tien",
            "phí giao dịch", "phi giao dich", "số tài khoản lạ", "so tai khoan la",
            "stk cá nhân", "stk ca nhan", "tài khoản nhận tiền", "tai khoan nhan tien",
            "chụp biên lai", "chup bien lai", "payment failed", "pay now",
        ],
        "weight": 0.9,
    },
]


def detect_by_rules(text: str) -> Dict[str, Any]:
    lower_text = text.lower()

    triggered_rules: List[str] = []
    matched_scam_types: List[tuple[str, float]] = []
    score = 0.0

    for rule in RULES:
        matched = any(keyword.lower() in lower_text for keyword in rule["keywords"])

        if matched:
            triggered_rules.append(rule["name"])
            matched_scam_types.append((rule["scam_type"], rule["weight"]))
            score += rule["weight"]

    # Normalize score về 0-1
    score = min(score, 1.0)

    # Chọn scam_type cụ thể có trọng số cao nhất để rule chung không lấn át rule chi tiết.
    final_scam_type = "UNKNOWN"
    specific_matches = [
        (scam_type, weight)
        for scam_type, weight in matched_scam_types
        if scam_type != "UNKNOWN"
    ]
    if specific_matches:
        final_scam_type = max(specific_matches, key=lambda item: item[1])[0]

    return {
        "rule_score": float(score),
        "triggered_rules": triggered_rules,
        "rule_scam_type": final_scam_type,
    }
