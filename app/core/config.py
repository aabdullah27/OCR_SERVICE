from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="OCR_", env_file=".env", extra="ignore")

    default_engine: str = "dolphin"

    dolphin_vllm_url: str = "http://localhost:8000/v1"
    dolphin_model_name: str = "ByteDance/Dolphin-v2"

    max_batch_size: int = 8
    request_timeout: int = 120

    api_key: str | None = None


settings = Settings()
