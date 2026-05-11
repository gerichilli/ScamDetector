import re


def normalize_entity_value(entity_type: str, value: str) -> str:
    cleaned = value.strip().lower()
    cleaned = re.sub(r"[\s\-_.]", "", cleaned)

    if entity_type == "phone":
        digits = re.sub(r"\D", "", cleaned)
        if digits.startswith("84") and len(digits) >= 10:
            return "0" + digits[2:]
        return digits

    if entity_type in {"bank_account", "e_wallet"}:
        return re.sub(r"\D", "", cleaned)

    return cleaned


def infer_file_type(filename: str) -> str:
    lower = filename.lower()
    if lower.endswith((".png", ".jpg", ".jpeg", ".webp")):
        return "image"
    if lower.endswith(".pdf"):
        return "pdf"
    return "file"
