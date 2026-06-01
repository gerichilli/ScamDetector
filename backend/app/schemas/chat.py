from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class ScamContext(BaseModel):
    label: str
    risk_level: str
    risk_score: float
    scam_type: str
    explanation: str
    recommended_action: str
    triggered_rules: List[str] = Field(default_factory=list)
    model_label: Optional[str] = None
    class_scores: Dict[str, float] = Field(default_factory=dict)
    responsible_ai_note: Optional[str] = None


class TextAnalysisRequest(BaseModel):
    text: str
    scam_result: Optional[ScamContext] = None


class MatchItem(BaseModel):
    keywords: List[str]
    response: str
    type: str


class TextAnalysisResponse(BaseModel):
    verdict: str
    summary: str
    matches: List[MatchItem]
    recommended_action: Optional[str]
    ai_used: bool = False
