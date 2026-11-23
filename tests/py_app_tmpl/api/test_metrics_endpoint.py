from collections.abc import Callable

import pytest

from helpers.test.env import TestEnv
from helpers.test.metrics import get_metric_value
from helpers.test.typing import AsyncClientFactory

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.asyncio,
]


async def test_metrics_disabled_returns_404(
    apply_test_env: Callable[[TestEnv], None],
    async_client_factory: AsyncClientFactory,
) -> None:
    apply_test_env(
        TestEnv(
            metrics_enabled=False,
        )
    )

    async with async_client_factory() as client:
        response = await client.get("/metrics")
        data = response.json()

    assert response.status_code == 404
    assert data == {"detail": "Not Found"}


async def test_metrics_enabled_returns_200(
    apply_test_env: Callable[[TestEnv], None],
    async_client_factory: AsyncClientFactory,
) -> None:
    apply_test_env(
        TestEnv(
            metrics_enabled=True,
        )
    )

    async with async_client_factory() as client:
        response = await client.get("/metrics")
        data = response.text

    assert response.status_code == 200
    assert "# HELP" in data
    assert "# TYPE" in data


async def test_metrics_records_requests(
    apply_test_env: Callable[[TestEnv], None],
    async_client_factory: AsyncClientFactory,
) -> None:

    apply_test_env(TestEnv(metrics_enabled=True))

    async with async_client_factory() as client:
        await client.get("/health")
        await client.get("/health")
        response = await client.get("/metrics")

    assert response.status_code == 200

    assert (
        get_metric_value(
            response.text,
            "http_requests_total",
            {
                "handler": "/health",
                "method": "GET",
                "status": "200",
            },
        )
        == 2.0
    )

    assert (
        get_metric_value(
            response.text,
            "http_request_duration_seconds_count",
            {
                "handler": "/health",
                "method": "GET",
            },
        )
        == 2.0
    )

    duration = get_metric_value(
        response.text,
        "http_request_duration_seconds_sum",
        {
            "handler": "/health",
            "method": "GET",
        },
    )

    assert duration is not None
    assert duration >= 0


async def test_metrics_endpoint_is_not_instrumented(
    apply_test_env: Callable[[TestEnv], None],
    async_client_factory: AsyncClientFactory,
) -> None:
    apply_test_env(TestEnv(metrics_enabled=True))

    async with async_client_factory() as client:
        await client.get("/health")
        await client.get("/metrics")
        await client.get("/metrics")
        response = await client.get("/metrics")

    assert response.status_code == 200

    assert (
        get_metric_value(
            response.text,
            "http_requests_total",
            {
                "handler": "/health",
                "method": "GET",
                "status": "200",
            },
        )
        == 1.0
    )

    assert 'handler="/metrics"' not in response.text
