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

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO",
    )

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


def validate_api_settings(settings: Settings) -> None:
    if settings.api_reload and settings.api_workers_count > 1:
        raise ValueError(
            "Configuration error: Auto-reload cannot be enabled with multiple workers."
        )
