from contextlib import asynccontextmanager
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient, Response

from helpers.test.env import ProdLikeTestEnv, TestEnv
from py_app_tmpl.api import main


@pytest.mark.asyncio
async def test_lifespan_generates_logs(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO"):
        async with main.lifespan(FastAPI()):
            pass

    assert "Starting application lifespan" in caplog.text
    assert "Application startup complete" in caplog.text
    assert "Application shutdown complete" in caplog.text


def test_GunicornApp_class() -> None:
    app: FastAPI = main.create_app()
    options: dict[str, Any] = {
        "bind": "0.0.0.0:8000",
        "workers": 2,
        "worker_class": "uvicorn_worker.UvicornWorker",
        # "worker_class": "uvicorn.workers.UvicornWorker",
        "logLevel": "info",
    }
    gunicorn_app = main.GunicornApp(app, options)

    assert gunicorn_app.cfg.bind == [options["bind"]]
    assert gunicorn_app.cfg.workers == options["workers"]
    assert gunicorn_app.cfg.worker_class.__name__ == "UvicornWorker"
    assert "uvicorn_worker" in gunicorn_app.cfg.worker_class.__module__
    assert gunicorn_app.cfg.loglevel == options["logLevel"]

    assert gunicorn_app.load() == app


def test_GunicornApp_load_config(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that GunicornApp correctly loads its configuration.
    Should skip None values from options.
    Should ignore unknown Gunicorn settings from options.
    """
    options: dict[str, Any] = {
        "bind": "0.0.0.0:8000",
        "workers": 2,
        "worker_class": "uvicorn_worker.UvicornWorker",
        "logLevel": "info",
        "unknown_option": "should_be_ignored",
        "none_option": None,
    }
    app: FastAPI = main.create_app()
    gunicorn_app = main.GunicornApp(app, options)
    gunicorn_app.load_config()

    assert gunicorn_app.cfg.bind == [options["bind"]]
    assert gunicorn_app.cfg.workers == options["workers"]
    assert gunicorn_app.cfg.worker_class.__name__ == "UvicornWorker"
    assert "uvicorn_worker" in gunicorn_app.cfg.worker_class.__module__
    assert gunicorn_app.cfg.loglevel == options["logLevel"]
    # unknown_option should be ignored, none_option should be skipped
    assert not hasattr(gunicorn_app.cfg, "unknown_option")
    assert not hasattr(gunicorn_app.cfg, "none_option")


def test_main_uses_gunicorn(monkeypatch: pytest.MonkeyPatch) -> None:

    test_env: ProdLikeTestEnv = ProdLikeTestEnv()

    captured: dict[str, object] = {}

    class FakeGunicornApp:
        def __init__(self, app: FastAPI, options: dict[str, Any] | None = None) -> None:
            captured["application"] = app
            captured["options"] = options

        def run(self) -> None:
            captured["ran"] = True

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(**test_env.get_env_dict()),
    )
    monkeypatch.setattr(
        main,
        "GunicornApp",
        FakeGunicornApp,
    )

    main.main()

    assert type(captured["application"]) is FastAPI
    assert captured["ran"] is True

    options: dict[str, Any] | None = captured["options"]  # type: ignore
    assert options is not None
    assert options["bind"] == f"{test_env.api_host}:{test_env.api_port}"
    assert options["workers"] == test_env.api_workers_count
    assert "UvicornWorker" in options["worker_class"]
    assert options["loglevel"] == test_env.log_level.lower()


def test_main_uses_uvicorn(monkeypatch: pytest.MonkeyPatch) -> None:
    test_env: TestEnv = TestEnv()
    run_mock = Mock()

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(**test_env.get_env_dict()),
    )

    monkeypatch.setattr(
        main,
        "uvicorn",
        SimpleNamespace(run=run_mock),
        raising=False,
    )

    main.main()

    run_mock.assert_called_once_with(
        "py_app_tmpl.api.main:create_app",
        factory=True,
        host=test_env.api_host,
        port=test_env.api_port,
        reload=test_env.api_reload,
        log_level=test_env.log_level.lower(),
    )


def test_main_raises_value_error(monkeypatch: pytest.MonkeyPatch) -> None:
    test_env: TestEnv = TestEnv(api_reload=True, api_workers_count=2)
    run_mock = Mock()

    monkeypatch.setattr(
        main,
        "get_settings",
        lambda: SimpleNamespace(**test_env.get_env_dict()),
    )

    monkeypatch.setattr(
        main,
        "uvicorn",
        SimpleNamespace(run=run_mock),
        raising=False,
    )

    with pytest.raises(
        ValueError,
        match="Configuration error: Auto-reload cannot be enabled with multiple workers.",
    ):
        main.main()


def test_root_endpoint(sync_test_client: TestClient) -> None:
    response = sync_test_client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Python Project Template API"}


@pytest.mark.asyncio
async def test_root_endpoint_async(async_test_client: AsyncClient) -> None:
    response: Response = await async_test_client.get("/async_home")

    assert response.status_code == 200
    assert response.json() == {"message": "Python Project Template Async API Home"}


def test_sync_client_runs_lifespan() -> None:
    events: list[str] = []

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        events.append("startup")
        yield
        events.append("shutdown")

    app = FastAPI(lifespan=test_lifespan)

    with TestClient(app) as client:
        assert events == ["startup"]
        assert client.get("/missing").status_code == 404

    assert events == ["startup", "shutdown"]

@pytest.mark.asyncio
async def test_async_client_runs_lifespan() -> None:
    events: list[str] = []

    @asynccontextmanager
    async def test_lifespan(app: FastAPI):
        events.append("startup")
        yield
        events.append("shutdown")

    app = FastAPI(lifespan=test_lifespan)

    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as client:
            assert events == ["startup"]
            assert (await client.get("/missing")).status_code == 404

    assert events == ["startup", "shutdown"]
