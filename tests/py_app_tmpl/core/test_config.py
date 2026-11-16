import pytest

from helpers.test.env import TestEnv
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


def test_validate_api_settings_raises_value_error() -> None:
    from py_app_tmpl.core.config import validate_api_settings

    settings = Settings(api_reload=True, api_workers_count=2)

    with pytest.raises(
        ValueError,
        match="Configuration error: Auto-reload cannot be enabled with multiple workers.",
    ):
        validate_api_settings(settings)
