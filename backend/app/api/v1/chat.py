from typing import Any
from fastapi import APIRouter, Depends, File, UploadFile, HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.database import get_db
from app.schemas.chat import TextAnalysisRequest, TextAnalysisResponse
from app.services.chatbot_service import analyze_text_with_ai
from pathlib import Path
import tempfile
import os

router = APIRouter()


@router.post("/analyze", response_model=TextAnalysisResponse)
async def analyze(request: TextAnalysisRequest, db: Session = Depends(get_db)) -> Any:
    """Analyze free text for scam indicators, using AI when configured."""
    settings = get_settings()
    result = await analyze_text_with_ai(request.text, settings.openai_api_key, settings.openai_model)
    return TextAnalysisResponse(
        verdict=result["verdict"],
        summary=result["summary"],
        matches=[
            {"keywords": m["keywords"], "response": m["response"], "type": m["type"]} for m in result["matches"]
        ],
        recommended_action=result.get("recommended_action"),
        ai_used=result.get("ai_used", False),
    )



@router.post("/analyze-image", response_model=TextAnalysisResponse)
async def analyze_image(file: UploadFile = File(...), db: Session = Depends(get_db)) -> Any:
    """Accept an image, run OCR, and analyze the extracted text."""
    suffix = Path(file.filename).suffix or ".png"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name
    try:
        try:
            from PIL import Image, UnidentifiedImageError
            import pytesseract
        except ImportError:
            raise HTTPException(status_code=503, detail="Image OCR dependencies are not installed")

        try:
            img = Image.open(tmp_path)
        except UnidentifiedImageError:
            raise HTTPException(status_code=422, detail="Uploaded file is not a valid image")
        text = pytesseract.image_to_string(img, lang="vie+eng")
        if not text.strip():
            raise HTTPException(status_code=422, detail="No text detected in image")
        settings = get_settings()
        result = await analyze_text_with_ai(text, settings.openai_api_key, settings.openai_model)
        return TextAnalysisResponse(
            verdict=result["verdict"],
            summary=result["summary"],
            matches=[{"keywords": m["keywords"], "response": m["response"], "type": m["type"]} for m in result["matches"]],
            recommended_action=result.get("recommended_action"),
            ai_used=result.get("ai_used", False),
        )
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass
