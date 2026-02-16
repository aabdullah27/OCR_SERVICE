import httpx
from PIL import Image

from app.engines.dolphin.backends.base import DolphinBackend
from app.engines.dolphin.utils import resize_image, image_to_base64
from app.core.exceptions import VLLMConnectionError


class VLLMBackend(DolphinBackend):
    def __init__(self, vllm_url: str, model_name: str, timeout: int = 300):
        self.vllm_url = vllm_url.rstrip("/")
        self.model_name = model_name
        self.timeout = timeout
        self.client: httpx.AsyncClient | None = None

    async def initialize(self) -> None:
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(self.timeout))
        if not await self.health_check():
            raise VLLMConnectionError(self.vllm_url, "Health check failed")
        print(f"[VLLMBackend] Connected to {self.vllm_url}")

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

    async def chat(self, prompt: str, image: Image.Image) -> str:
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

        response = await self.client.post(f"{self.vllm_url}/chat/completions", json=payload)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]