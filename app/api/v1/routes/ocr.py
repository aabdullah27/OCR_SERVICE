import base64
import json
import time

from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException

from app.api.v1.deps import get_ocr_service, verify_api_key
from app.api.v1.schemas.requests import OCRRequest, BatchOCRRequest, JSONLItem
from app.api.v1.schemas.responses import OCRResponse, BatchOCRResponse, BatchItemResult, JSONLBatchResponse, JSONLItemResult
from app.services.ocr_service import OCRService
from app.engines.base import OutputFormat
from app.engines.registry import EngineRegistry
from app.core.config import settings
from app.core.exceptions import OCRException

router = APIRouter(prefix="/ocr", tags=["OCR"], dependencies=[Depends(verify_api_key)])

MAX_JSONL_ITEMS = 100


@router.post("", response_model=OCRResponse)
async def process_image(request: OCRRequest, service: OCRService = Depends(get_ocr_service)):
    try:
        result, engine_name, elapsed_ms = await service.process_image(request.image, request.engine, request.format)
        print(f"[OCR] Single image processed: engine={engine_name}, time={elapsed_ms}ms")
        return OCRResponse(content=result.content, format=result.format, engine=engine_name, processing_time_ms=elapsed_ms)
    except OCRException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/upload", response_model=OCRResponse)
async def process_image_upload(file: UploadFile = File(...), engine: str | None = Form(None), format: OutputFormat = Form("markdown"), service: OCRService = Depends(get_ocr_service)):
    try:
        image_bytes = await file.read()
        image_b64 = base64.b64encode(image_bytes).decode("utf-8")

        result, engine_name, elapsed_ms = await service.process_image(image_b64, engine, format)
        print(f"[OCR] Upload processed: engine={engine_name}, time={elapsed_ms}ms")
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

        print(f"[OCR] Batch processed: {len(items)} images, engine={engine_name}, time={elapsed_ms}ms")
        return BatchOCRResponse(results=items, format=request.format, engine=engine_name, processing_time_ms=elapsed_ms)
    except OCRException as e:
        raise HTTPException(status_code=400, detail=e.message)


@router.post("/batch/jsonl", response_model=JSONLBatchResponse)
async def process_batch_jsonl(file: UploadFile = File(...), engine: str | None = Form(None)):
    start = time.perf_counter()

    content = await file.read()
    lines = content.decode("utf-8").strip().split("\n")

    if len(lines) > MAX_JSONL_ITEMS:
        raise HTTPException(status_code=400, detail=f"Max {MAX_JSONL_ITEMS} items per request")

    items: list[tuple[str | None, bytes]] = []
    for i, line in enumerate(lines):
        if not line.strip():
            continue
        try:
            parsed = JSONLItem.model_validate(json.loads(line))
            image_bytes = base64.b64decode(parsed.image)
            items.append((parsed.id or str(i), image_bytes))
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid JSONL at line {i + 1}: {e}")

    if not items:
        raise HTTPException(status_code=400, detail="No valid items in JSONL file")

    engine_name = engine or settings.DEFAULT_ENGINE
    engine_instance = EngineRegistry.get_instance(engine_name)

    images_bytes = [img for _, img in items]
    ids = [id_ for id_, _ in items]

    print(f"[OCR] JSONL batch started: {len(items)} items, engine={engine_name}")
    results = await engine_instance.process_batch(images_bytes, "markdown")

    elapsed_ms = int((time.perf_counter() - start) * 1000)

    response_items = []
    succeeded = 0
    failed = 0

    for id_, result in zip(ids, results):
        if isinstance(result, Exception):
            response_items.append(JSONLItemResult(id=id_, success=False, error=str(result)))
            failed += 1
        else:
            response_items.append(JSONLItemResult(id=id_, content=result.content, success=True))
            succeeded += 1

    print(f"[OCR] JSONL batch complete: {succeeded}/{len(items)} succeeded, time={elapsed_ms}ms")
    return JSONLBatchResponse(
        results=response_items,
        engine=engine_name,
        processing_time_ms=elapsed_ms,
        total=len(items),
        succeeded=succeeded,
        failed=failed,
    )
