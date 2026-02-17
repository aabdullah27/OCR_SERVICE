from pydantic import BaseModel, Field

from app.engines.base import OutputFormat


class OCRResponse(BaseModel):
    content: str
    format: OutputFormat
    engine: str
    processing_time_ms: int


class BatchItemResult(BaseModel):
    content: str | None = None
    success: bool
    error: str | None = None


class BatchOCRResponse(BaseModel):
    results: list[BatchItemResult]
    format: OutputFormat
    engine: str
    processing_time_ms: int


class JSONLItemResult(BaseModel):
    id: str | None = None
    content: str | None = None
    success: bool
    error: str | None = None


class JSONLBatchResponse(BaseModel):
    results: list[JSONLItemResult]
    engine: str
    processing_time_ms: int
    total: int
    succeeded: int
    failed: int


class HealthResponse(BaseModel):
    status: str
    engines: list[str] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    detail: str
    error_type: str | None = None
