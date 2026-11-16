from collections.abc import Iterator

import pytest

from helpers.test.env import TestEnv
from py_app_tmpl.core.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    """Set environment variables before any imports.

    This hook runs before pytest collects tests, so settings will read
    the correct test values at import time without needing monkeypatch.

    Intentionally enabled for import-time configuration safety.
    Please check out README for more details on configuration.
    """
    test_env: TestEnv = TestEnv()
    test_env.export_env()


@pytest.fixture(autouse=True)
def isolate_settings_cache() -> Iterator[None]:
    """Ensure each test sees a fresh settings cache state."""
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


@pytest.fixture
def override_settings(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[pytest.MonkeyPatch]:
    """Allow per-test environment overrides with cache isolation.

    Usage:
    def test_custom_name(override_settings: pytest.MonkeyPatch) -> None:
        override_settings.setenv("APP_NAME", "custom_app")

        settings = get_settings()

        assert settings.app_name == "custom_app"
    """
    yield monkeypatch
