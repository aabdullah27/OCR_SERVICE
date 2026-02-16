from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCR_", env_file=".env", extra="ignore")

    default_engine: str = "dolphin"

    dolphin_backend: Literal["transformers", "vllm"] = "transformers"
    dolphin_model: str = "ByteDance/Dolphin-v2"
    dolphin_vllm_url: str = "http://localhost:8000/v1"

    request_timeout: int = 300
    api_key: str | None = None


settings = Settings()
