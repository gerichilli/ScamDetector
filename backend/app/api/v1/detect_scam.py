from fastapi import APIRouter, HTTPException

from app.schemas.scam_detection import (
    ScamDetectionRequest,
    ScamDetectionResponse,
)
from app.services.scam_detection_service import detect_scam_service


router = APIRouter(prefix="/detect-scam", tags=["Scam Detection"])


@router.post("", response_model=ScamDetectionResponse)
def detect_scam(payload: ScamDetectionRequest):
    try:
        result = detect_scam_service(payload.text)
        return result
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))