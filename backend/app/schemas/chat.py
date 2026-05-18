from pydantic import BaseModel
from typing import List, Optional


class TextAnalysisRequest(BaseModel):
    text: str


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
