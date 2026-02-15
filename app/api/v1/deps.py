from fastapi import HTTPException, Header

from app.core.config import settings
from app.services.ocr_service import ocr_service, OCRService


def get_ocr_service() -> OCRService:
    return ocr_service


async def verify_api_key(x_api_key: str | None = Header(None)) -> None:
    if settings.api_key is None:
        return

    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
