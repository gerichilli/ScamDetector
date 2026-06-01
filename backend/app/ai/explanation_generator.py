from typing import Dict, Any, List


ACTION_BY_SCAM_TYPE = {
    "OTP_BANK": "Không cung cấp OTP, mã xác nhận, mật khẩu hoặc thông tin ngân hàng. Hãy gọi trực tiếp ngân hàng qua số chính thức để kiểm tra.",
    "EMERGENCY_MONEY": "Không chuyển tiền vội. Hãy gọi trực tiếp cho người thân qua số quen thuộc để xác minh.",
    "FAKE_POLICE": "Không chuyển tiền và không làm theo hướng dẫn qua điện thoại. Hãy liên hệ công an địa phương hoặc người thân để kiểm tra.",
    "PHISHING_LINK": "Không bấm vào link lạ. Chỉ truy cập website hoặc ứng dụng chính thức.",
    "PRIZE_GIFT": "Không chuyển phí nhận thưởng và không cung cấp thông tin cá nhân cho nguồn không rõ ràng.",
    "INVESTMENT": "Không chuyển tiền vào kênh đầu tư cam kết lợi nhuận cao bất thường. Hãy hỏi người thân hoặc chuyên gia tài chính.",
    "JOB_SCAM": "Không nạp tiền hoặc đóng phí để nhận việc online. Hãy kiểm tra thông tin công ty và hợp đồng rõ ràng.",
    "UNKNOWN": "Không cung cấp thông tin cá nhân, không chuyển tiền và nên hỏi người thân hoặc tổ chức chính thức để xác minh.",
}


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

    if label == "SAFE":
        explanation = "Nội dung này chưa có dấu hiệu lừa đảo rõ ràng."
        recommended_action = "Có thể tiếp tục trò chuyện bình thường, nhưng vẫn nên cẩn thận nếu đối phương yêu cầu tiền, OTP hoặc thông tin cá nhân."
    elif triggered_rules:
        explanation = "Nội dung này có dấu hiệu rủi ro vì: " + "; ".join(triggered_rules) + "."
        recommended_action = ACTION_BY_SCAM_TYPE.get(scam_type, ACTION_BY_SCAM_TYPE["UNKNOWN"])
    else:
        explanation = (
            "Mô hình AI đánh giá nội dung này có dấu hiệu đáng ngờ. "
            "Tuy chưa phát hiện từ khóa nguy hiểm rõ ràng, nội dung vẫn nên được kiểm tra thêm."
        )
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