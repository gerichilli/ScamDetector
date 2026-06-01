from app.ai.preprocessing import normalize_text
from app.ai.rule_detector import detect_by_rules
from app.ai.ml_detector import predict_scam
from app.ai.risk_aggregator import aggregate_risk
from app.ai.explanation_generator import generate_explanation


def detect_scam_service(text: str):
    clean_text = normalize_text(text)

    rule_result = detect_by_rules(clean_text)
    ml_result = predict_scam(clean_text)
    risk_result = aggregate_risk(rule_result, ml_result)

    explanation_result = generate_explanation(
        text=clean_text,
        risk_result=risk_result,
        rule_result=rule_result,
        ml_result=ml_result,
    )

    return {
        **risk_result,
        **explanation_result,
    }