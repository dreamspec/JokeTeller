"""Application settings for JokeTeller."""

from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Typed application settings loaded from environment variables."""

    app_name: str = "JokeTeller API"
    app_version: str = "0.1.0"
    lm_studio_base_url: str = "http://127.0.0.1:1234"
    lm_studio_default_model: str = ""
    lm_studio_timeout_seconds: float = 60.0
    backend_cors_origins: str = (
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:4173,http://127.0.0.1:4173"
    )
    max_history_messages: int = 12

    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def normalized_lm_studio_base_url(self) -> str:
        """Return an LM Studio base URL that always ends in `/v1`."""

        base_url = self.lm_studio_base_url.rstrip("/")
        return base_url if base_url.endswith("/v1") else f"{base_url}/v1"

    @property
    def cors_origins(self) -> list[str]:
        """Return the configured frontend origins as a clean list."""

        return [origin.strip() for origin in self.backend_cors_origins.split(",") if origin.strip()]


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return a cached settings object."""

    return Settings()
