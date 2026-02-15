import base64
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from app.api.v1.deps import get_ocr_service, verify_api_key
from app.api.v1.schemas.requests import OCRRequest, BatchOCRRequest
from app.api.v1.schemas.responses import OCRResponse, BatchOCRResponse, BatchItemResult
from app.services.ocr_service import OCRService
from app.engines.base import OutputFormat
from app.core.exceptions import OCRException

router = APIRouter(prefix="/ocr", tags=["OCR"], dependencies=[Depends(verify_api_key)])


@router.post("", response_model=OCRResponse)
async def process_image(request: OCRRequest, service: OCRService = Depends(get_ocr_service)):
    try:
        result, engine_name, elapsed_ms = await service.process_image(request.image, request.engine, request.format)
        return OCRResponse(content=result.content, format=result.format, engine=engine_name, processing_time_ms=elapsed_ms)
    except OCRException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/upload", response_model=OCRResponse)
async def process_image_upload(file: UploadFile = File(...), engine: str | None = Form(None), format: OutputFormat = Form("markdown"), service: OCRService = Depends(get_ocr_service)):
    try:
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        result, engine_name, elapsed_ms = await service.process_image(image_b64, engine, format)
        return OCRResponse(content=result.content, format=result.format, engine=engine_name, processing_time_ms=elapsed_ms)
    except OCRException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/batch", response_model=BatchOCRResponse)
async def process_batch(request: BatchOCRRequest, service: OCRService = Depends(get_ocr_service)):
    try:
        results, engine_name, elapsed_ms = await service.process_batch(request.images, request.engine, request.format)

        items = []
        for r in results:
            if isinstance(r, Exception):
                items.append(BatchItemResult(success=False, error=str(r)))
            else:
                items.append(BatchItemResult(content=r.content, success=True))

        return BatchOCRResponse(results=items, format=request.format, engine=engine_name, processing_time_ms=elapsed_ms)
    except OCRException as e:
        raise HTTPException(status_code=400, detail=e.message)
