from pathlib import Path
from typing import Dict, Any
import logging

import joblib


BACKEND_DIR = Path(__file__).resolve().parents[2]
MODEL_PATH = BACKEND_DIR / "ml_artifacts" / "scam_detector_pipeline_v2_clean.joblib"
SAFE_DEFAULT_RESULT = {
    "model_label": "SAFE",
    "model_score": 0.0,
    "class_scores": {
        "SAFE": 1.0,
        "SUSPICIOUS": 0.0,
        "SCAM": 0.0,
    },
}

logger = logging.getLogger(__name__)
_model = None


def get_model():
    global _model

    if _model is None:
        if not MODEL_PATH.exists():
            logger.warning("Model file not found, using safe default: %s", MODEL_PATH)
            return None
        try:
            _model = joblib.load(MODEL_PATH)
        except Exception:
            logger.exception("Failed to load model, using safe default: %s", MODEL_PATH)
            return None

    return _model


def predict_scam(text: str) -> Dict[str, Any]:
    model = get_model()
    if model is None:
        return {
            **SAFE_DEFAULT_RESULT,
            "class_scores": SAFE_DEFAULT_RESULT["class_scores"].copy(),
        }

    try:
        predicted_label = model.predict([text])[0]
        probabilities = model.predict_proba([text])[0]
        classes = list(model.classes_)
    except Exception:
        logger.exception("Model prediction failed, using safe default")
        return {
            **SAFE_DEFAULT_RESULT,
            "class_scores": SAFE_DEFAULT_RESULT["class_scores"].copy(),
        }

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
