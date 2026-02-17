from PIL import Image

from app.engines.base import OCREngine, OCRResult, OutputFormat
from app.engines.registry import EngineRegistry
from app.engines.dolphin.backends.base import DolphinBackend
from app.engines.dolphin.prompts import LAYOUT_PROMPT, get_element_prompt
from app.engines.dolphin.utils import bytes_to_image, parse_layout_string, process_coordinates, elements_to_markdown
from app.core.config import settings
from app.core.exceptions import ImageProcessingError


@EngineRegistry.register("dolphin")
class DolphinEngine(OCREngine):
    name = "dolphin"
    supported_formats: list[OutputFormat] = ["markdown"]

    def __init__(self):
        self.backend: DolphinBackend | None = None

    async def initialize(self) -> None:
        print(f"[DolphinEngine] Initializing with backend={settings.DOLPHIN_BACKEND}, model={settings.DOLPHIN_MODEL}")

        if settings.DOLPHIN_BACKEND == "vllm":
            from app.engines.dolphin.backends.vllm import VLLMBackend
            self.backend = VLLMBackend(settings.DOLPHIN_VLLM_URL, settings.DOLPHIN_MODEL, settings.REQUEST_TIMEOUT)
        else:
            from app.engines.dolphin.backends.transformers import TransformersBackend
            self.backend = TransformersBackend(settings.DOLPHIN_MODEL)

        await self.backend.initialize()
        print(f"[DolphinEngine] Ready")

    async def health_check(self) -> bool:
        return self.backend is not None and await self.backend.health_check()

    async def cleanup(self) -> None:
        if self.backend:
            await self.backend.cleanup()
            self.backend = None

    async def process(self, image_bytes: bytes, output_format: OutputFormat = "markdown") -> OCRResult:
        try:
            image = bytes_to_image(image_bytes)
        except Exception as e:
            raise ImageProcessingError(str(e))

        elements = await self._process_document(image)
        content = self._format_output(elements, output_format)

        print(f"[DolphinEngine] Processed image: {len(elements)} elements, {len(content)} chars")
        return OCRResult(content=content, format=output_format, metadata={"element_count": len(elements)})

    async def _process_document(self, image: Image.Image) -> list[dict]:
        layout_output = await self.backend.chat(LAYOUT_PROMPT, image)
        layout_elements = parse_layout_string(layout_output)

        if not layout_elements or not (layout_output.strip().startswith("[") and layout_output.strip().endswith("]")):
            layout_elements = [([0, 0, image.size[0], image.size[1]], "distorted_page", [])]

        return await self._process_elements(layout_elements, image)

    async def _process_elements(self, layout_elements: list, image: Image.Image) -> list[dict]:
        results = []

        for idx, (bbox, label, tags) in enumerate(layout_elements):
            if label == "distorted_page":
                crop = image
                x1, y1, x2, y2 = 0, 0, image.size[0], image.size[1]
            else:
                x1, y1, x2, y2 = process_coordinates(bbox, image)
                crop = image.crop((x1, y1, x2, y2))

            if crop.size[0] < 4 or crop.size[1] < 4:
                continue

            if label == "fig":
                results.append({"label": label, "text": "[Figure]", "bbox": [x1, y1, x2, y2], "reading_order": idx, "tags": tags})
                continue

            prompt = get_element_prompt(label)
            text = await self.backend.chat(prompt, crop)

            results.append({"label": label, "text": text.strip(), "bbox": [x1, y1, x2, y2], "reading_order": idx, "tags": tags})

        return results

    def _format_output(self, elements: list[dict], output_format: OutputFormat) -> str:
        return elements_to_markdown(elements)

    async def process_batch(self, images: list[bytes], output_format: OutputFormat = "markdown") -> list[OCRResult | Exception]:
        results = []
        for i, img in enumerate(images):
            try:
                result = await self.process(img, output_format)
                results.append(result)
            except Exception as e:
                results.append(e)
            print(f"[DolphinEngine] Batch progress: {i + 1}/{len(images)}")

        succeeded = sum(1 for r in results if not isinstance(r, Exception))
        print(f"[DolphinEngine] Batch complete: {succeeded}/{len(images)} succeeded")
        return results
