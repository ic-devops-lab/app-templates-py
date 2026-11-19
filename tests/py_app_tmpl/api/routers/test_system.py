from collections.abc import Callable

import pytest
from fastapi.testclient import TestClient
from httpx2 import AsyncClient, Response

from helpers.test.env import PostgresTestEnv, TestEnv
from helpers.test.typing import AsyncClientFactory


@pytest.mark.smoke
def test_system_info(sync_test_client: TestClient) -> None:
    test_env: TestEnv = TestEnv()
    response = sync_test_client.get("/info")
    data = response.json()

    assert response.status_code == 200
    assert "app_name" in data
    assert "app_version" in data
    assert "environment" in data
    assert "logging_level" in data
    assert "api_workers_count" in data

    assert data["app_name"] == test_env.app_name
    assert data["app_version"] == test_env.app_version
    assert data["environment"] == test_env.app_env
    assert data["logging_level"] == test_env.log_level
    assert data["api_workers_count"] == test_env.api_workers_count


@pytest.mark.smoke
def test_liveness_probe(sync_test_client: TestClient) -> None:
    response = sync_test_client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_readiness_probe_ok(
    async_client_factory: AsyncClientFactory,
) -> None:
    async with async_client_factory() as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["postgres"] == "disabled"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_readiness_probe_service_unvailable(
    async_test_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    from py_app_tmpl.api.checks import CheckResult, CheckStatus

    # force the postgres check to fail
    async def fake_check_postgres(*args: object, **_kwargs: object) -> CheckResult:
        return CheckResult("postgres", CheckStatus.FAIL)

    monkeypatch.setattr("py_app_tmpl.api.routers.system.check_postgres", fake_check_postgres)

    response: Response = await async_test_client.get("/ready")
    data = response.json()

    assert response.status_code == 503
    assert "global_status" in data
    assert "postgres" in data
    assert data["global_status"] == "fail"


@pytest.mark.postgres
@pytest.mark.integration
@pytest.mark.asyncio
async def test_readiness_postgres_ok(
    postgres_test_env: None,
    async_client_factory: AsyncClientFactory,
) -> None:
    async with async_client_factory() as client:
        response = await client.get("/ready")

    assert response.status_code == 200
    assert response.json()["postgres"] == "ok"


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_readiness_postgres_bad_connection(
    apply_test_env: Callable[[TestEnv], None],
    async_client_factory: AsyncClientFactory,
) -> None:
    apply_test_env(
        PostgresTestEnv(
            postgres_url="postgresql+asyncpg://app:pass@127.0.0.1:1/testdb",
        )
    )

    async with async_client_factory() as client:
        response = await client.get("/ready")

    assert response.status_code == 503
    assert response.json()["global_status"] == "fail"
    assert response.json()["postgres"] == "fail"
