from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCR_", env_file=".env", extra="ignore")

    default_engine: str = "dolphin"
    api_key: str | None = None
    request_timeout: int = 300

    dolphin_backend: Literal["transformers", "vllm"] = "transformers"
    dolphin_model: str = "ByteDance/Dolphin-v2"
    dolphin_vllm_url: str = "http://localhost:8000/v1"

    google_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"


settings = Settings()
