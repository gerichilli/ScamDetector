import re


def normalize_text(text: str) -> str:
    if not text:
        return ""

    text = str(text).strip()
    text = re.sub(r"\s+", " ", text)

    # Mask dữ liệu nhạy cảm nếu user nhập thật
    text = re.sub(r"http\S+|www\.\S+", "<LINK>", text)
    text = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "<EMAIL>", text)
    text = re.sub(r"\b0\d{8,10}\b", "<PHONE>", text)
    text = re.sub(r"\b\d{9,16}\b", "<NUMBER>", text)

    return text