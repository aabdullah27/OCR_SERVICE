import base64
import time

from app.engines.base import OCRResult, OutputFormat
from app.engines.registry import EngineRegistry
from app.core.config import settings
from app.core.exceptions import UnsupportedFormatError, ImageProcessingError


class OCRService:
    def __init__(self):
        self.default_engine = settings.DEFAULT_ENGINE

    def _get_engine(self, engine_name: str | None):
        name = engine_name or self.default_engine
        return EngineRegistry.get_instance(name)

    def _validate_format(self, engine, output_format: OutputFormat) -> None:
        if output_format not in engine.supported_formats:
            raise UnsupportedFormatError(output_format, engine.name, engine.supported_formats)

    def _decode_image(self, image_b64: str) -> bytes:
        try:
            return base64.b64decode(image_b64)
        except Exception as e:
            raise ImageProcessingError(f"Invalid base64 image: {e}")

    async def process_image(self, image_b64: str, engine_name: str | None = None, output_format: OutputFormat = "markdown") -> tuple[OCRResult, str, int]:
        engine = self._get_engine(engine_name)
        self._validate_format(engine, output_format)

        image_bytes = self._decode_image(image_b64)

        start = time.perf_counter()
        result = await engine.process(image_bytes, output_format)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return result, engine.name, elapsed_ms

    async def process_batch(self, images_b64: list[str], engine_name: str | None = None, output_format: OutputFormat = "markdown") -> tuple[list[OCRResult | Exception], str, int]:
        engine = self._get_engine(engine_name)
        self._validate_format(engine, output_format)

        images_bytes = []
        for img_b64 in images_b64:
            images_bytes.append(self._decode_image(img_b64))

        start = time.perf_counter()
        results = await engine.process_batch(images_bytes, output_format)
        elapsed_ms = int((time.perf_counter() - start) * 1000)

        return results, engine.name, elapsed_ms


ocr_service = OCRService()
