import inspect

import pytest
from fastapi.testclient import TestClient
from httpx2 import AsyncClient, Response

from helpers.test.env import TestEnv


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


def test_liveness_probe(sync_test_client: TestClient) -> None:
    response = sync_test_client.get("/health")
    data = response.json()

    assert response.status_code == 200
    assert "status" in data
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_probe_ok(async_test_client: AsyncClient) -> None:
    response: Response = await async_test_client.get("/ready")
    data = response.json()

    assert response.status_code == 200
    assert "global_status" in data
    assert "db_healthy" in data
    assert "cache_healthy" in data
    assert data["global_status"] == "ok"


@pytest.mark.asyncio
async def test_readiness_probe_service_unvailable(
    async_test_client: AsyncClient, monkeypatch: pytest.MonkeyPatch
) -> None:

    # Force readiness checks to fail by patching concurrent result aggregation.
    async def fake_gather(*args: object, **_kwargs: object) -> tuple[bool, bool]:
        for arg in args:
            if inspect.isawaitable(arg):
                await arg
        return (False, False)

    monkeypatch.setattr("py_app_tmpl.api.routers.system.asyncio.gather", fake_gather)

    response: Response = await async_test_client.get("/ready")
    data = response.json()

    assert response.status_code == 503
    assert "global_status" in data
    assert "db_healthy" in data
    assert "cache_healthy" in data
    assert data["global_status"] == "fail"
