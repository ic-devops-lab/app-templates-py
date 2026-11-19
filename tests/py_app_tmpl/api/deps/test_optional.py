# import pytest
# from fastapi import Request
# from sqlalchemy.ext.asyncio import AsyncEngine

# from py_app_tmpl.api.deps.optional import get_pg_engine
# from py_app_tmpl.core.config import Settings, get_settings


# def test_get_pg_engine_postgres_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
#     settings: Settings = get_settings(postgres_enabled=False)
#     request = Request(scope={"type": "http"})
#     request.app = type("App", (), {})()
#     request.app.state = type("State", (), {})()
#     request.app.state.settings = settings

#     pg_engine: AsyncEngine | None = get_pg_engine(request)

#     assert pg_engine is None
