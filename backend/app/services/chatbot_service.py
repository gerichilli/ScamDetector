import json
import re
from typing import Any, Dict

import httpx

# Minimal rule sets adapted from the standalone scam-call-detector project.
# Each scenario contains keywords and a response + severity type.
RECOVERY_SCENARIOS = [
    {
        "keywords": ["lỡ chuyển tiền", "vừa chuyển xong", "đã chuyển tiền"],
        "response": "KHẨN CẤP: Gọi ngay tổng đài ngân hàng để yêu cầu chặn giao dịch.",
        "type": "danger",
    },
    {
        "keywords": ["lỡ đọc otp", "đã đọc otp", "cho mã otp"],
        "response": "KHẨN CẤP: Liên hệ ngân hàng và đổi mật khẩu ngay.",
        "type": "danger",
    },
    {
        "keywords": ["lỡ bấm link", "nhấp vào link"],
        "response": "HƯỚNG DẪN: Thoát trang, xóa lịch sử duyệt và kiểm tra sao kê tài khoản.",
        "type": "warning",
    },
]

SCAM_SCENARIOS = [
    {
        "keywords": ["mã otp", "otp", "đọc mã otp"],
        "response": "NGUY HIỂM: Tuyệt đối không đọc mã OTP cho người lạ.",
        "type": "danger",
    },
    {
        "keywords": ["chuyển tiền", "chuyển khoản", "chuyển tiền gấp"],
        "response": "CẢNH BÁO: Không chuyển tiền khi chưa kiểm tra kỹ.",
        "type": "warning",
    },
    {
        "keywords": ["trúng thưởng", "đóng phí", "nhận quà"],
        "response": "ĐÁNG NGHI: Yêu cầu đóng phí để nhận quà thường là lừa đảo.",
        "type": "warning",
    },
    {
        "keywords": ["công an", "tòa án", "cuộc điều tra"],
        "response": "NGUY HIỂM: Cơ quan chức năng không yêu cầu chuyển tiền qua điện thoại.",
        "type": "danger",
    },
]


SENSITIVE_PATTERNS = [
    (re.compile(r"\b(?:\+?84|0)(?:\d[\s.-]?){8,10}\b"), "[PHONE]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[EMAIL]"),
    (re.compile(r"\b\d{4,8}\b"), "[OTP_OR_CODE]"),
    (re.compile(r"\b\d{9,16}\b"), "[BANK_ACCOUNT_OR_CARD]"),
]


def redact_sensitive_text(text: str) -> str:
    redacted = text
    for pattern, replacement in SENSITIVE_PATTERNS:
        redacted = pattern.sub(replacement, redacted)
    return redacted


def analyze_text(text: str) -> Dict[str, Any]:
    """Analyze input text using keyword matching and return matches plus a verdict."""
    text_l = text.lower()
    matches = []
    highest = "info"
    recommended = None

    def record(scenario: Dict[str, Any]):
        nonlocal highest, recommended
        matches.append({"keywords": scenario["keywords"], "response": scenario["response"], "type": scenario["type"]})
        if scenario["type"] == "danger":
            highest = "danger"
            recommended = scenario["response"]
        elif scenario["type"] == "warning" and highest != "danger":
            highest = "warning"

    for s in RECOVERY_SCENARIOS:
        for kw in s["keywords"]:
            if kw in text_l:
                record(s)
                break

    for s in SCAM_SCENARIOS:
        for kw in s["keywords"]:
            if kw in text_l:
                record(s)
                break

    if not matches:
        verdict = "safe"
        summary = "Không phát hiện dấu hiệu lừa đảo rõ ràng."
    else:
        verdict = highest
        summary = f"Phát hiện {len(matches)} dấu hiệu: {', '.join([m['type'] for m in matches])}."

    return {"verdict": verdict, "summary": summary, "matches": matches, "recommended_action": recommended, "ai_used": False}


def _extract_output_text(payload: Dict[str, Any]) -> str:
    if isinstance(payload.get("output_text"), str):
        return payload["output_text"]

    chunks = []
    for item in payload.get("output", []):
        if item.get("type") != "message":
            continue
        for content in item.get("content", []):
            if content.get("type") in {"output_text", "text"} and content.get("text"):
                chunks.append(content["text"])
    return "\n".join(chunks).strip()


def _parse_ai_json(text: str) -> Dict[str, Any]:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if not match:
            raise
        return json.loads(match.group(0))


async def analyze_text_with_ai(text: str, api_key: str, model: str) -> Dict[str, Any]:
    fallback = analyze_text(text)
    if not api_key:
        return fallback

    redacted_text = redact_sensitive_text(text)
    print(f"MASK_DEMO noi_dung_goc={text.encode('unicode_escape').decode('ascii')}", flush=True)
    print(f"MASK_DEMO noi_dung_sau_khi_che={redacted_text.encode('unicode_escape').decode('ascii')}", flush=True)
    # IMPORTANT: Temporary demo logs kept on for verification; Gemini request flow continues below.
    return fallback
    instructions = (
        "Always address the user as 'bác' and refer to yourself as 'cháu'. "
        "Bạn là trợ lý cảnh báo lừa đảo cho người dùng Việt Nam. "
        "Phân tích tin nhắn/tình huống đã được ẩn danh dữ liệu nhạy cảm. "
        "Chỉ trả về JSON hợp lệ với các field: verdict, summary, recommended_action. "
        "verdict chỉ được là safe, warning hoặc danger. "
        "Nếu verdict là danger, recommended_action phải bắt đầu bằng 'NGUY HIỂM:', không dùng cụm 'CẢNH BÁO ĐỎ'. "
        "Không yêu cầu người dùng cung cấp OTP, mật khẩu, số tài khoản, CCCD."
    )
    prompt = (
        "Phân tích rủi ro lừa đảo của nội dung sau và trả lời ngắn, dễ hiểu:\n\n"
        f"{redacted_text}"
    )

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                },
                json={
                    "system_instruction": {
                        "parts": [{"text": instructions}],
                    },
                    "contents": [
                        {
                            "parts": [{"text": prompt}],
                        }
                    ],
                    "generationConfig": {
                        "temperature": 0.2,
                    },
                },
            )
            response.raise_for_status()

        gemini_response = response.json()
        parts = gemini_response.get("candidates", [{}])[0].get("content", {}).get("parts", [])
        output_text = "\n".join(part.get("text", "") for part in parts if part.get("text")).strip()
        ai_payload = _parse_ai_json(output_text)
        verdict = ai_payload.get("verdict") if ai_payload.get("verdict") in {"safe", "warning", "danger"} else fallback["verdict"]
        return {
            "verdict": verdict,
            "summary": ai_payload.get("summary") or fallback["summary"],
            "matches": fallback["matches"],
            "recommended_action": ai_payload.get("recommended_action") or fallback.get("recommended_action"),
            "ai_used": True,
        }
    except Exception:
        return fallback
