from typing import Dict, Any, List


ACTION_BY_SCAM_TYPE = {
    "OTP_BANK": "Không cung cấp OTP, mã xác nhận, mật khẩu hoặc thông tin ngân hàng. Hãy gọi trực tiếp ngân hàng qua số chính thức để kiểm tra.",
    "EMERGENCY_MONEY": "Không chuyển tiền vội. Hãy gọi trực tiếp cho người thân qua số quen thuộc để xác minh.",
    "FAKE_POLICE": "Không chuyển tiền và không làm theo hướng dẫn qua điện thoại. Hãy liên hệ công an địa phương hoặc người thân để kiểm tra.",
    "PHISHING_LINK": "Không bấm vào link lạ. Chỉ truy cập website hoặc ứng dụng chính thức.",
    "PRIZE_GIFT": "Không chuyển phí nhận thưởng và không cung cấp thông tin cá nhân cho nguồn không rõ ràng.",
    "INVESTMENT": "Không chuyển tiền vào kênh đầu tư cam kết lợi nhuận cao bất thường. Hãy hỏi người thân hoặc chuyên gia tài chính.",
    "JOB_SCAM": "Không nạp tiền hoặc đóng phí để nhận việc online. Hãy kiểm tra thông tin công ty và hợp đồng rõ ràng.",
    "LOAN_SCAM": "Không đóng phí trước, không gửi CCCD hoặc giấy tờ cá nhân cho dịch vụ vay không rõ nguồn. Hãy kiểm tra tổ chức cho vay qua kênh chính thức.",
    "FAKE_SUPPORT": "Không cài app lạ, không chia sẻ màn hình hoặc cấp quyền truy cập cho người tự xưng hỗ trợ. Hãy gọi lại tổng đài chính thức.",
    "DEEPFAKE_CALL": "Không chuyển tiền trong cuộc gọi chưa xác minh. Hãy gọi lại số quen thuộc hoặc hỏi câu riêng tư mà chỉ người thân biết.",
    "HEALTH_PRODUCT": "Không mua thuốc hoặc sản phẩm sức khỏe không rõ nguồn qua điện thoại. Hãy hỏi bác sĩ hoặc người thân trước khi thanh toán.",
    "TRAVEL_COMBO": "Không đặt cọc qua tài khoản cá nhân. Hãy kiểm tra website, fanpage, giấy phép kinh doanh và xác nhận trực tiếp với khách sạn.",
    "ROMANCE_SCAM": "Không chuyển tiền hoặc nhận gửi quà cho người quen qua mạng chưa từng gặp. Hãy trao đổi với người thân trước khi quyết định.",
    "PAYMENT_SCAM": "Không thanh toán qua link hoặc tài khoản lạ. Hãy kiểm tra giao dịch trong ứng dụng chính thức hoặc gọi tổng đài chính thức.",
    "UNKNOWN": "Không cung cấp thông tin cá nhân, không chuyển tiền và nên hỏi người thân hoặc tổ chức chính thức để xác minh.",
}


def _format_model_signal(ml_result: Dict[str, Any]) -> str:
    class_scores = ml_result.get("class_scores") or {}
    model_label = ml_result.get("model_label") or "UNKNOWN"

    if not class_scores:
        return "Mô hình không trả về phân phối điểm chi tiết."

    sorted_scores = sorted(class_scores.items(), key=lambda item: item[1], reverse=True)
    top_label, top_score = sorted_scores[0]
    score_text = ", ".join(
        f"{label}: {score:.0%}"
        for label, score in sorted_scores
    )

    if top_score < 0.60:
        return (
            f"Mô hình chưa chắc chắn giữa các nhãn ({score_text}); "
            "vì mức tự tin cao nhất dưới 60%, hệ thống nâng cảnh báo để người dùng xác minh thêm."
        )

    if model_label == "SCAM":
        return (
            f"Mô hình nhận diện mẫu ngôn ngữ giống nhóm lừa đảo trong dữ liệu huấn luyện "
            f"(SCAM: {class_scores.get('SCAM', top_score):.0%}; phân phối: {score_text})."
        )

    if model_label == "SUSPICIOUS":
        return (
            f"Mô hình nhận diện nội dung giống nhóm đáng nghi "
            f"(SUSPICIOUS: {class_scores.get('SUSPICIOUS', top_score):.0%}; phân phối: {score_text})."
        )

    return (
        f"Mô hình nghiêng về {top_label} với điểm {top_score:.0%}, "
        f"nhưng tổng rủi ro vẫn cần kiểm tra thêm (phân phối: {score_text})."
    )


def generate_explanation(
    text: str,
    risk_result: Dict[str, Any],
    rule_result: Dict[str, Any],
    ml_result: Dict[str, Any],
) -> Dict[str, Any]:
    label = risk_result.get("label", "SAFE")
    scam_type = risk_result.get("scam_type", "UNKNOWN")
    risk_level = risk_result.get("risk_level", "LOW")
    triggered_rules: List[str] = rule_result.get("triggered_rules", [])
    model_uncertain = bool(risk_result.get("model_uncertain", False))

    if label == "SAFE":
        explanation = "Nội dung này chưa có dấu hiệu lừa đảo rõ ràng."
        recommended_action = "Có thể tiếp tục trò chuyện bình thường, nhưng vẫn nên cẩn thận nếu đối phương yêu cầu tiền, OTP hoặc thông tin cá nhân."
    elif triggered_rules:
        explanation = "Nội dung này có dấu hiệu rủi ro vì: " + "; ".join(triggered_rules) + "."
        recommended_action = ACTION_BY_SCAM_TYPE.get(scam_type, ACTION_BY_SCAM_TYPE["UNKNOWN"])
    else:
        explanation = _format_model_signal(ml_result)
        if not model_uncertain:
            explanation += " Không có rule từ khóa nào khớp trực tiếp, nên cần xác minh thủ công trước khi hành động."
        recommended_action = ACTION_BY_SCAM_TYPE["UNKNOWN"]

    return {
        "explanation": explanation,
        "recommended_action": recommended_action,
        "triggered_rules": triggered_rules,
        "model_label": ml_result.get("model_label"),
        "class_scores": ml_result.get("class_scores"),
        "responsible_ai_note": (
            "Kết quả này chỉ mang tính hỗ trợ cảnh báo sớm, không thay thế xác minh từ người thân, ngân hàng hoặc cơ quan chức năng."
            if risk_level in ["MEDIUM", "HIGH"]
            else "Hệ thống vẫn khuyến khích người dùng thận trọng với yêu cầu cung cấp thông tin nhạy cảm."
        ),
    }
