from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCR_", env_file=".env", extra="ignore")

    # Core
    DEFAULT_ENGINE: str = "dolphin"
    API_KEY: str | None = None
    REQUEST_TIMEOUT: int = 300

    # Dolphin engine
    DOLPHIN_BACKEND: Literal["transformers", "vllm"] = "transformers"
    DOLPHIN_MODEL: str = "ByteDance/Dolphin-v2"
    DOLPHIN_VLLM_URL: str = "http://localhost:8000/v1"

    # Gemini engine
    GOOGLE_API_KEY: str | None = None
    GEMINI_MODEL: str = "gemini-2.5-flash"
    GEMINI_MAX_CONCURRENT: int = 10


settings = Settings()
