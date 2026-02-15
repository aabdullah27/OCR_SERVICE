from fastapi import APIRouter

from app.api.v1.schemas.responses import HealthResponse
from app.engines.registry import EngineRegistry

router = APIRouter(tags=["Health"])


@router.get("/health", response_model=HealthResponse)
async def health():
    return HealthResponse(status="ok", engines=EngineRegistry.list_initialized())


@router.get("/ready", response_model=HealthResponse)
async def ready():
    initialized = EngineRegistry.list_initialized()
    if not initialized:
        return HealthResponse(status="not_ready", engines=[])
    return HealthResponse(status="ready", engines=initialized)
