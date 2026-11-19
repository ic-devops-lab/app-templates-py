from collections.abc import AsyncGenerator, Generator
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from fastapi import FastAPI
from fastapi.testclient import TestClient
from httpx2 import ASGITransport, AsyncClient

from helpers.test.typing import AsyncClientFactory


@pytest.fixture(scope="function")
def sync_test_client() -> Generator[TestClient]:
    from py_app_tmpl.api.main import create_app

    with TestClient(create_app()) as client:
        yield client


@pytest.fixture
def async_client_factory() -> AsyncClientFactory:
    @asynccontextmanager
    async def create_client() -> AsyncGenerator[AsyncClient]:
        from py_app_tmpl.api.main import create_app

        app: FastAPI = create_app()

        async with app.router.lifespan_context(app):
            async with AsyncClient(
                transport=ASGITransport(app=app),
                base_url="http://testserver",
            ) as client:
                yield client

    return create_client


@pytest_asyncio.fixture
async def async_test_client(
    async_client_factory: AsyncClientFactory,
) -> AsyncGenerator[AsyncClient]:
    """Use for tests that don't need to manipulate configuration."""
    async with async_client_factory() as client:
        yield client
