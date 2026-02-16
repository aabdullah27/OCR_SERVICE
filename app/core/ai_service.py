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
            if settings.google_api_key:
                print("[AIService] Initializing with Google API key")
                cls._instance.client = genai.Client(api_key=settings.google_api_key)
            else:
                print("[AIService] No Google API key configured")
        return cls._instance

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_content(self, model_name: str, contents: List[Any], config: genai_types.GenerateContentConfig) -> genai_types.GenerateContentResponse:
        print(f"[AIService] Calling generate_content with model: {model_name}")
        try:
            response = await self.client.aio.models.generate_content(
                model=model_name,
                contents=contents,
                config=config
            )
            return response
        except Exception as e:
            print(f"[AIService] Error calling Gemini API: {e}")
            raise

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    async def generate_content_stream(self, model_name: str, contents: List[Any], config: genai_types.GenerateContentConfig) -> AsyncGenerator:
        print(f"[AIService] Calling generate_content_stream with model: {model_name}")
        try:
            response_stream = await self.client.aio.models.generate_content_stream(
                model=model_name,
                contents=contents,
                config=config
            )
            async for chunk in response_stream:
                yield chunk
        except Exception as e:
            print(f"[AIService] Error streaming from Gemini API: {e}")
            raise


ai_service = AIService()
