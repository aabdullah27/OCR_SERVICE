import asyncio

from google.genai import types as genai_types

from app.engines.base import OCREngine, OCRResult, OutputFormat
from app.engines.registry import EngineRegistry
from app.engines.gemini.prompts import MARKDOWN_PROMPT
from app.core.config import settings
from app.core.ai_service import ai_service
from app.core.exceptions import OCRException


@EngineRegistry.register("gemini")
class GeminiEngine(OCREngine):
    name = "gemini"
    supported_formats: list[OutputFormat] = ["markdown"]

    def __init__(self):
        self._initialized = False
        self._semaphore: asyncio.Semaphore | None = None

    async def initialize(self) -> None:
        if not settings.GOOGLE_API_KEY:
            raise OCRException("GOOGLE_API_KEY is required for Gemini engine. Set OCR_GOOGLE_API_KEY env var.")

        self._semaphore = asyncio.Semaphore(settings.GEMINI_MAX_CONCURRENT)
        self._initialized = True
        print(f"[GeminiEngine] Initialized with model={settings.GEMINI_MODEL}, max_concurrent={settings.GEMINI_MAX_CONCURRENT}")

    async def health_check(self) -> bool:
        return self._initialized and ai_service.client is not None

    async def cleanup(self) -> None:
        self._initialized = False
        self._semaphore = None

    async def process(self, image_bytes: bytes, output_format: OutputFormat = "markdown") -> OCRResult:
        if not self._initialized:
            raise OCRException("Engine not initialized")

        contents = [
            genai_types.Part.from_bytes(data=image_bytes, mime_type="image/png"),
            MARKDOWN_PROMPT,
        ]

        config = genai_types.GenerateContentConfig(temperature=0)

        try:
            response = await ai_service.generate_content(settings.GEMINI_MODEL, contents, config)
            content = response.text or ""
        except Exception as e:
            raise OCRException(f"Gemini API error: {e}")

        print(f"[GeminiEngine] Processed image: {len(content)} chars extracted")
        return OCRResult(content=content.strip(), format=output_format, metadata={"model": settings.GEMINI_MODEL})

    async def _process_with_semaphore(self, image_bytes: bytes, output_format: OutputFormat) -> OCRResult:
        async with self._semaphore:
            return await self.process(image_bytes, output_format)

    async def process_batch(self, images: list[bytes], output_format: OutputFormat = "markdown") -> list[OCRResult | Exception]:
        if not self._initialized:
            raise OCRException("Engine not initialized")

        tasks = [self._process_with_semaphore(img, output_format) for img in images]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        succeeded = sum(1 for r in results if not isinstance(r, Exception))
        print(f"[GeminiEngine] Batch complete: {succeeded}/{len(images)} succeeded")
        return list(results)
