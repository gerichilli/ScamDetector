import re
import unicodedata


def _strip_obfuscation_chars(text: str) -> str:
    cleaned_chars = []
    for char in text:
        category = unicodedata.category(char)
        if category in {"Cf", "Cs"}:
            continue
        if category in {"Cc", "So", "Sk"}:
            cleaned_chars.append(" ")
            continue
        cleaned_chars.append(char)
    return "".join(cleaned_chars)


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = unicodedata.normalize("NFKC", str(text))
    text = _strip_obfuscation_chars(text).strip()
    text = re.sub(r"\s+", " ", text)

    # Mask dữ liệu nhạy cảm nếu user nhập thật
    text = re.sub(r"http\S+|www\.\S+", "<LINK>", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "<EMAIL>", text)
    text = re.sub(r"\b0\d{8,10}\b", "<PHONE>", text)
    text = re.sub(r"\b\d{9,16}\b", "<NUMBER>", text)

    return text
