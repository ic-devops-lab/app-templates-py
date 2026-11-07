from py_app_tmpl.core.config import Settings, get_settings


def test_env_fixture_overrides_sensitive_vars() -> None:
    settings = Settings()

    assert settings.app_name == "test_app"
    assert settings.app_version == "testVersion"
    assert settings.app_env == "test"
    assert settings.log_level == "ERROR"


def test_get_settings_returns_cached_instance() -> None:
    settings1: Settings = get_settings()
    settings2: Settings = get_settings()

    assert settings1 is settings2
