from typing import List, Dict, Optional
from pydantic import BaseModel, Field


class ScamDetectionRequest(BaseModel):
    text: str = Field(..., min_length=1)


class ScamDetectionResponse(BaseModel):
    label: str
    risk_level: str
    risk_score: float
    scam_type: str
    explanation: str
    recommended_action: str
    triggered_rules: List[str]
    model_label: Optional[str] = None
    class_scores: Dict[str, float]
    responsible_ai_note: str