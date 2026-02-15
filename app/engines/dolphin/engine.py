import httpx
from PIL import Image

from app.engines.base import OCREngine, OCRResult, OutputFormat
from app.engines.registry import EngineRegistry
from app.engines.dolphin.prompts import LAYOUT_PROMPT, get_element_prompt
from app.engines.dolphin.utils import (
    bytes_to_image,
    resize_image,
    image_to_base64,
    parse_layout_string,
    process_coordinates,
    elements_to_markdown,
    elements_to_html,
    elements_to_json,
)
from app.core.exceptions import VLLMConnectionError, ImageProcessingError


@EngineRegistry.register("dolphin")
class DolphinEngine(OCREngine):
    name = "dolphin"
    supported_formats: list[OutputFormat] = ["markdown", "html", "json"]

    def __init__(self, vllm_url: str, model_name: str, timeout: int = 120):
        self.vllm_url = vllm_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self.client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        if not await self.health_check():
            raise VLLMConnectionError(self.vllm_url, "Health check failed")
        print(f"[DolphinEngine] Initialized with vLLM at {self.vllm_url}")

    async def health_check(self) -> bool:
        if not self.client:
            return False
        try:
            response = await self.client.get(f"{self.vllm_url}/models")
            return response.status_code == 200
        except httpx.RequestError:
            return False

    async def cleanup(self) -> None:
        if self.client:
            await self.client.aclose()
            self.client = None
        print("[DolphinEngine] Cleaned up")

    async def process(self, image_bytes: bytes, output_format: OutputFormat = "markdown") -> OCRResult:
        try:
            image = bytes_to_image(image_bytes)
        except Exception as e:
            raise ImageProcessingError(str(e))

        elements = await self._process_document(image)

        content = self._format_output(elements, output_format)

        return OCRResult(
            content=content,
            format=output_format,
            metadata={"element_count": len(elements)},
        )

    async def _process_document(self, image: Image.Image) -> list[dict]:
        layout_output = await self._call_vllm(LAYOUT_PROMPT, image)

        layout_elements = parse_layout_string(layout_output)

        if not layout_elements or not (layout_output.strip().startswith("[") and layout_output.strip().endswith("]")):
            layout_elements = [([0, 0, image.size[0], image.size[1]], "distorted_page", [])]

        elements = await self._process_elements(layout_elements, image)
        return elements

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
                results.append({
                    "label": label,
                    "text": f"[Figure]",
                    "bbox": [x1, y1, x2, y2],
                    "reading_order": idx,
                    "tags": tags,
                })
                continue

            prompt = get_element_prompt(label)
            text = await self._call_vllm(prompt, crop)

            results.append({
                "label": label,
                "text": text.strip(),
                "bbox": [x1, y1, x2, y2],
                "reading_order": idx,
                "tags": tags,
            })

        return results

    async def _call_vllm(self, prompt: str, image: Image.Image) -> str:
        if not self.client:
            raise VLLMConnectionError(self.vllm_url, "Client not initialized")

        resized = resize_image(image)
        image_b64 = image_to_base64(resized)

        payload = {
            "model": self.model_name,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_b64}"}},
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": 4096,
            "temperature": 0,
        }

        try:
            response = await self.client.post(f"{self.vllm_url}/chat/completions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data["choices"][0]["message"]["content"]
        except httpx.RequestError as e:
            raise VLLMConnectionError(self.vllm_url, str(e))
        except (KeyError, IndexError) as e:
            raise ImageProcessingError(f"Invalid vLLM response: {e}")

    def _format_output(self, elements: list[dict], output_format: OutputFormat) -> str:
        if output_format == "markdown":
            return elements_to_markdown(elements)
        elif output_format == "html":
            return elements_to_html(elements)
        elif output_format == "json":
            return elements_to_json(elements)
        return elements_to_markdown(elements)
