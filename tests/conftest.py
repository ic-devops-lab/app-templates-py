from collections.abc import Iterator

import pytest

from helpers.test.env import (
    PostgresTestEnv,
    ProdLikeTestEnv,
    TestEnv,
)
from py_app_tmpl.core.config import get_settings

PROFILES = { # type: ignore
    "default": TestEnv,
    "prod": ProdLikeTestEnv,
    "postgres": PostgresTestEnv,
}


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add command-line option to select the test environment profile.

    Usage examples:
        # Default tests, PostgreSQL disabled
        uv run pytest

        # Production-like settings
        uv run pytest --test-profile=prod

        # PostgreSQL-enabled settings
        uv run --extra postgres pytest --test-profile=postgres

    The selected profile applies to the entire pytest process.

    If you run with --test-profile=postgres, every test that relies on the default
    environment will see POSTGRES_ENABLED=true. That can break tests expecting
    PostgreSQL to be disabled, and PostgresTestEnv alone doesn't provide a running
    database.

    For better flexibility apply individual profile through monkeypatch and clear the
    cached settings (see apply_test_env and isolate_settings_cache fixtures).
    """
    parser.addoption(
        "--test-profile",
        choices=list(PROFILES), # type: ignore
        default="default",
        help="Select the test environment profile",
    )

def pytest_configure(config: pytest.Config) -> None:
    """Set environment variables before any imports.

    This hook runs before pytest collects tests, so settings will read
    the correct test values at import time without needing monkeypatch.

    Intentionally enabled for import-time configuration safety.
    Please check out README for more details on configuration.
    """
    profile_name = config.getoption("--test-profile")
    profile = PROFILES[profile_name]() # type: ignore
    profile.export_env() # type: ignore


@pytest.fixture(autouse=True)
def isolate_settings_cache() -> Iterator[None]:
    """Ensure each test sees a fresh settings cache state."""
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


@pytest.fixture
def apply_test_env(monkeypatch: pytest.MonkeyPatch):
    """
    Example usage:
        (1)
        def test_production_settings(apply_test_env):
            apply_test_env(ProdLikeTestEnv(api_workers_count=4))

            settings = get_settings()

            assert settings.api_workers_count == 4
            assert settings.api_reload is False

        (2)
        def test_postgres_settings(apply_test_env):
            apply_test_env(
                PostgresTestEnv(
                    postgres_url="postgresql+asyncpg://app:pass@localhost:5432/testdb"
                )
            )

            settings = get_settings()

            assert settings.postgres_enabled is True

    Important: apply the profile before creating the FastAPI app or starting its
    lifespan. Changing settings after the engine has been initialized won't reconfigure
    the existing engine.
    """
    def apply(profile: TestEnv) -> None:
        for key, value in profile.get_env_dict().items():
            env_key = key.upper()

            if value is None:
                monkeypatch.delenv(env_key, raising=False)
            else:
                monkeypatch.setenv(env_key, str(value))

        get_settings.cache_clear()

    yield apply

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
