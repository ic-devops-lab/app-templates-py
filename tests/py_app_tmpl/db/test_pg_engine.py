import re

import pytest

from py_app_tmpl.db.pg_engine import build_engine


@pytest.mark.smoke
def test_build_engine_raises_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    # simulate create_async_engine raising an exception
    def fake_create_async_engine(*args: object, **kwargs: object) -> None:
        raise RuntimeError("Failed to create engine")

    monkeypatch.setattr("py_app_tmpl.db.pg_engine.create_async_engine", fake_create_async_engine)

    with pytest.raises(RuntimeError, match=re.escape("Error creating the database engine for URL")):
        build_engine("postgresql+asyncpg://app:pass@127.0.0.1:1/testdb")


@pytest.mark.smoke
@pytest.mark.asyncio
async def test_dispose_engine_raises_exception(monkeypatch: pytest.MonkeyPatch) -> None:
    # simulate engine.dispose raising an exception
    class FakeEngine:
        def __init__(self) -> None:
            self.url = "postgresql+asyncpg://app:pass@127.0.0.1:1/testdb"

        async def dispose(self) -> None:
            raise RuntimeError("Failed to dispose engine")

    monkeypatch.setattr(
        "py_app_tmpl.db.pg_engine.create_async_engine",
        lambda *args, **kwargs: FakeEngine(),  # type: ignore
    )
    engine = build_engine("postgresql+asyncpg://app:pass@127.0.0.1:1/testdb")

    with pytest.raises(RuntimeError, match=re.escape("Error disposing database engine for URL")):
        from py_app_tmpl.db.pg_engine import dispose_engine

        await dispose_engine(engine)
