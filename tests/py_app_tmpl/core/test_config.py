import re
from types import SimpleNamespace

import pytest

from helpers.test.env import TestEnv
from py_app_tmpl.core import config
from py_app_tmpl.core.config import Settings, get_settings


def test_env_fixture_overrides_sensitive_vars() -> None:
    test_env: TestEnv = TestEnv()
    settings = Settings()

    assert settings.app_name == test_env.app_name
    assert settings.app_version == test_env.app_version
    assert settings.app_env == test_env.app_env
    assert settings.log_level == test_env.log_level


def test_get_settings_returns_cached_instance() -> None:
    settings1: Settings = get_settings()
    settings2: Settings = get_settings()

    assert settings1 is settings2


def test_validate_app_settings_postgres_url_null(monkeypatch: pytest.MonkeyPatch) -> None:
    """
    Settings have postgres_enabled set to True but postgres_url is None.
    """
    fake_settings = SimpleNamespace(postgres_enabled=True, postgres_url=None)
    monkeypatch.setattr(config, "get_settings", lambda: fake_settings)

    settings: Settings = config.get_settings()

    with pytest.raises(
        ValueError,
        match=re.escape("POSTGRES_URL is required when POSTGRES_ENABLED=true"),
    ):
        config.validate_app_settings(settings)


def test_settings_rejects_non_asyncpg_scheme() -> None:
    with pytest.raises(
        ValueError,
        match=re.escape("POSTGRES_URL must use the postgresql+asyncpg driver"),
    ):
        config.validate_app_settings(
            Settings(
                postgres_enabled=True,
                postgres_url="postgresql://user:pass@localhost:5432/mydb",
            )
        )


def test_settings_rejects_malformed_asyncpg_url() -> None:
    with pytest.raises(ValueError, match=re.escape("POSTGRES_URL is incomplete")):
        config.validate_app_settings(
            Settings(
                postgres_enabled=True,
                postgres_url="postgresql+asyncpg://",
            )
        )


def test_validate_api_settings_raises_value_error() -> None:
    from py_app_tmpl.core.config import validate_api_settings

    settings = Settings(api_reload=True, api_workers_count=2)

    with pytest.raises(
        ValueError,
        match="Configuration error: Auto-reload cannot be enabled with multiple workers.",
    ):
        validate_api_settings(settings)
