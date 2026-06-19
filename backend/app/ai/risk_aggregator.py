from typing import Dict, Any


def get_risk_level(score: float) -> str:
    if score >= 0.70:
        return "HIGH"
    if score >= 0.40:
        return "MEDIUM"
    return "LOW"


def aggregate_risk(rule_result: Dict[str, Any], ml_result: Dict[str, Any]) -> Dict[str, Any]:
    rule_score = float(rule_result.get("rule_score", 0.0))
    model_score = float(ml_result.get("model_score", 0.0))
    model_label = ml_result.get("model_label", "SAFE")
    class_scores = ml_result.get("class_scores") or {}
    max_class_score = max(class_scores.values()) if class_scores else 1.0
    model_uncertain = max_class_score < 0.60

    # Kết hợp rule + model
    weighted_score = 0.5 * rule_score + 0.5 * model_score

    # Không để mất cảnh báo khi model rất chắc SCAM
    final_score = max(weighted_score, model_score if model_label == "SCAM" else weighted_score)
    if model_uncertain:
        final_score = max(final_score, 0.70)
    final_score = min(final_score, 1.0)

    risk_level = get_risk_level(final_score)

    if risk_level == "HIGH":
        final_label = "SCAM"
    elif risk_level == "MEDIUM":
        final_label = "SUSPICIOUS"
    else:
        final_label = "SAFE"

    scam_type = rule_result.get("rule_scam_type", "UNKNOWN")

    return {
        "label": final_label,
        "risk_level": risk_level,
        "risk_score": round(float(final_score), 4),
        "scam_type": scam_type,
        "model_uncertain": model_uncertain,
    }
