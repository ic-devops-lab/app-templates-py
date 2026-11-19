from collections.abc import Callable, Iterator

import pytest
from testcontainers.community.postgres import PostgresContainer

from helpers.test.env import (
    PostgresTestEnv,
    TestEnv,
)
from py_app_tmpl.core.config import get_settings


def pytest_configure(config: pytest.Config) -> None:
    """Set environment variables before any imports.

    This hook runs before pytest collects tests, so settings will read
    the correct test values at import time without needing monkeypatch.

    Intentionally enabled for import-time configuration safety.
    Please check out README for more details on configuration.
    """
    TestEnv().export_env()


@pytest.fixture(autouse=True)
def isolate_settings_cache() -> Iterator[None]:
    """Ensure each test sees a fresh settings cache state."""
    get_settings.cache_clear()

    yield

    get_settings.cache_clear()


@pytest.fixture
def apply_test_env(monkeypatch: pytest.MonkeyPatch) -> Iterator[Callable[[TestEnv], None]]:
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


@pytest.fixture(scope="session")
def postgres_url() -> Iterator[str]:
    with PostgresContainer(
        image="postgres:17-alpine",
        driver="asyncpg",
    ) as postgres:
        yield postgres.get_connection_url()


@pytest.fixture
def postgres_test_env(
    postgres_url: str,
    apply_test_env: Callable[[TestEnv], None],
) -> None:
    """Usage example:
    @pytest.mark.asyncio
    async def test_postgres_readiness(
        postgres_test_env,
        async_test_client,
    ):
        response = await async_test_client.get("/ready")

        assert response.status_code == 200
        assert response.json()["postgres"] == "ok"
    """
    apply_test_env(
        PostgresTestEnv(
            postgres_url=postgres_url,
        )
    )


# @pytest.fixture
# async def seed_scenario(db_session):
#     """Usage example:
#     @pytest.mark.asyncio
#     async def test_something(seed_baseline, seed_scenario):
#         await seed_scenario([
#             Customer(name="Alice"),
#             Customer(name="Bob"),
#         ])
#     """
#     async def load(records):
#         db_session.add_all(records)
#         await db_session.flush()
#         return records

#     return load
