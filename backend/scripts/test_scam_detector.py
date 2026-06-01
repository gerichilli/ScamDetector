from pathlib import Path
import joblib

BASE_DIR = Path(__file__).resolve().parents[1]
MODEL_PATH = BASE_DIR / "ml_artifacts" / "scam_detector_pipeline_v1.joblib"

model = joblib.load(MODEL_PATH)

test_cases = [
    "Cô gửi mã OTP để xác minh tài khoản ngay nhé",
    "Mẹ ơi con đang cấp cứu, chuyển gấp cho con 5 triệu, đừng gọi lại",
    "Chúc mừng cô đã trúng thưởng xe máy, bấm link để nhận quà",
    "Anh chị xác minh tài khoản trong hôm nay nhé",
    "Mai con về nhà ăn cơm với ba mẹ",
    "Co gui ma OTP de xac minh tai khoan",
    "Me ck gap cho con 5tr, dung goi lai",
    "Cô ơi cháu bên công an, cô đang liên quan vụ án rửa tiền",
    "Bên em tuyển việc online, cô nạp trước 300 nghìn để nhận nhiệm vụ",
    "Ngân hàng thông báo bảo trì hệ thống tối nay, không yêu cầu cung cấp thông tin",
]

for text in test_cases:
    pred = model.predict([text])[0]
    proba = model.predict_proba([text])[0]
    classes = model.classes_

    score_map = {
        label: round(float(score), 4)
        for label, score in zip(classes, proba)
    }

    print("\nTEXT:", text)
    print("PRED:", pred)
    print("SCORES:", score_map)