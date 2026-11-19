from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Python Project Template"
    app_version: str = "0.1.0"
    app_env: str = "local"

    api_host: str = Field(default="127.0.0.1", min_length=3)
    api_port: int = Field(default=8000, ge=1, le=65535)
    # Whether to enable auto-reload for the API server in development
    # Set to False in production to disable auto-reload
    api_reload: bool = False
    api_workers_count: int = Field(default=1, ge=1)

    postgres_enabled: bool = Field(default=False)
    postgres_url: str | None = None

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_postgres_settings(settings: Settings) -> None:
    """Validate database configuration without importing optional packages."""
    if not settings.postgres_enabled:
        return
    if not settings.postgres_url:
        raise ValueError("POSTGRES_URL is required when POSTGRES_ENABLED=true")
    if not settings.postgres_url.startswith("postgresql+asyncpg://"):
        raise ValueError("POSTGRES_URL must use the postgresql+asyncpg driver")
    if len(settings.postgres_url) == len("postgresql+asyncpg://"):
        raise ValueError("POSTGRES_URL is incomplete")


def validate_app_settings(settings: Settings) -> None:
    # postgres_url should exist
    validate_postgres_settings(settings)


def validate_api_settings(settings: Settings) -> None:
    validate_app_settings(settings)
    if settings.api_reload and settings.api_workers_count > 1:
        raise ValueError(
            "Configuration error: Auto-reload cannot be enabled with multiple workers."
        )
