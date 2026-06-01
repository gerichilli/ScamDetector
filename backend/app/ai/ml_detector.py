from pathlib import Path
from typing import Dict, Any

import joblib


BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BACKEND_DIR / "ml_artifacts" / "scam_detector_pipeline_v1.joblib"

_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            raise FileNotFoundError(f"Model file not found: {MODEL_PATH}")
        _model = joblib.load(MODEL_PATH)

    return _model


def predict_scam(text: str) -> Dict[str, Any]:
    model = get_model()

    predicted_label = model.predict([text])[0]
    probabilities = model.predict_proba([text])[0]
    classes = list(model.classes_)

    scores = {
        label: float(score)
        for label, score in zip(classes, probabilities)
    }

    scam_score = scores.get("SCAM", 0.0)
    suspicious_score = scores.get("SUSPICIOUS", 0.0)

    # Risk từ model: SCAM là nguy hiểm trực tiếp, SUSPICIOUS tính một phần
    model_risk_score = min(scam_score + 0.5 * suspicious_score, 1.0)

    return {
        "model_label": predicted_label,
        "model_score": float(model_risk_score),
        "class_scores": scores,
    }