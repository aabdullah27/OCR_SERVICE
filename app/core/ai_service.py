from typing import List, Any, AsyncGenerator

from tenacity import retry, stop_after_attempt, wait_exponential
from google import genai
from google.genai import types as genai_types

from app.core.config import settings


class AIService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(AIService, cls).__new__(cls)
            cls._instance.client = None
            if settings.GOOGLE_API_KEY:
                print("[AIService] Initializing with Google API key")
                cls._instance.client = genai.Client(api_key=settings.GOOGLE_API_KEY)
        return cls._instance

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_content(self, model_name: str, contents: List[Any], config: genai_types.GenerateContentConfig) -> genai_types.GenerateContentResponse:
        if not self.client:
            raise RuntimeError("Google API key not configured")
        print(f"[AIService] Calling generate_content with model: {model_name}")
        response = await self.client.aio.models.generate_content(model=model_name, contents=contents, config=config)
        return response

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_content_stream(self, model_name: str, contents: List[Any], config: genai_types.GenerateContentConfig) -> AsyncGenerator:
        if not self.client:
            raise RuntimeError("Google API key not configured")
        print(f"[AIService] Calling generate_content_stream with model: {model_name}")
        response_stream = await self.client.aio.models.generate_content_stream(model=model_name, contents=contents, config=config)
        async for chunk in response_stream:
            yield chunk


ai_service = AIService()
