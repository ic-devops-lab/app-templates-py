from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient


@pytest.fixture(scope="function")
def sync_test_client() -> Generator[TestClient]:
    from py_app_tmpl.api.main import create_app

    with TestClient(create_app()) as client:
        yield client


@pytest_asyncio.fixture(scope="function")
async def async_test_client() -> AsyncGenerator[AsyncClient]:
    """Overrides FastAPI dependencies and provisions an async test client."""
    from py_app_tmpl.api.main import create_app

    app: FastAPI = create_app()

    # here you can override FastAPI dependencies if needed
    # before creating the async client
    # Example of overriding a dependency
    # app.dependency_overrides[SomeDependency] = lambda: MockedDependency()

    async with app.router.lifespan_context(app):
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as async_client:
            yield async_client

    # Crucial: Reset the application state cleanly after the test case finishes
    # uncomment the following line if you have a function to reset the app state
    # app.dependency_overrides.clear()
