from pydantic import BaseModel, Field

from app.engines.base import OutputFormat


class OCRRequest(BaseModel):
    image: str = Field(..., description="Base64 encoded image")
    engine: str | None = Field(None, description="OCR engine to use")
    format: OutputFormat = Field("markdown", description="Output format")


class BatchOCRRequest(BaseModel):
    images: list[str] = Field(..., description="List of base64 encoded images", min_length=1)
    engine: str | None = Field(None, description="OCR engine to use")
    format: OutputFormat = Field("markdown", description="Output format")
