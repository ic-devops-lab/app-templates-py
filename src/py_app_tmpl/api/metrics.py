from fastapi import FastAPI


def configure_metrics(app: FastAPI) -> None:
    """Configure optional Prometheus instrumentation."""
    from prometheus_client import (
        CollectorRegistry,
        GCCollector,
        PlatformCollector,
        ProcessCollector,
    )
    from prometheus_fastapi_instrumentator import Instrumentator

    registry = CollectorRegistry()

    GCCollector(registry=registry)
    PlatformCollector(registry=registry)
    ProcessCollector(registry=registry)

    Instrumentator(
        registry=registry,
        should_group_status_codes=False,
        excluded_handlers=["/metrics"],
    ).instrument(app).expose(
        app,
        endpoint="/metrics",
        include_in_schema=False,
    )
