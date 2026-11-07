import os
from collections.abc import Iterator

import pytest

from py_app_tmpl.core.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    """Set environment variables before any imports.

    This hook runs before pytest collects tests, so settings will read
    the correct test values at import time without needing monkeypatch.

    Intentionally enabled for import-time configuration safety.
    Please check out README for more details on configuration.
    """
    os.environ["APP_NAME"] = "test_app"
    os.environ["APP_VERSION"] = "testVersion"
    os.environ["APP_ENV"] = "test"
    os.environ["LOG_LEVEL"] = "ERROR"


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
    get_settings.cache_clear()

    yield monkeypatch

    get_settings.cache_clear()
