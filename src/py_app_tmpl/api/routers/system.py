import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Response, status

from py_app_tmpl.core.config import Settings, get_settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="",
    tags=["system"],
    responses={
        404: {"description": "Not Found"},
        500: {"description": "Internal Server Error"},
    },
)


@router.get(
    "/info",
    responses={
        200: {"description": "System Information"},
    },
    summary="Get system information",
    description="Retrieve system information including status and configuration.",
)
async def get_system_info() -> dict[str, Any]:
    settings: Settings = get_settings()

    return {
        "app_name": settings.app_name,
        "app_version": settings.app_version,
        "environment": settings.app_env,
        "logging_level": settings.log_level,
        "api_workers_count": settings.api_workers_count,
    }


@router.get(
    "/health",
    responses={
        200: {"description": "Liveness Probe"},
    },
    summary="Liveness probe",
    description="Check the liveness status of the system.",
    tags=["health"],
)
async def get_liveness_probe() -> dict[str, str]:
    return {"status": "ok"}


@router.get(
    "/ready",
    responses={
        200: {"description": "Readiness Probe"},
    },
    summary="Readiness probe",
    description="Check the readiness status of the system.",
    tags=["health"],
)
async def get_readyness_probe(response: Response) -> dict[str, str]:
    """
    # Run dependency checks concurrently to avoid performance bottlenecks
    # Example:
    # db_healthy, cache_healthy = await asyncio.gather(
    #     check_database(),
    #     check_cache()
    # )
    """

    # Simulate any check for now with some delay
    async def dummy_check(res: bool = True) -> bool:
        await asyncio.sleep(0.1)
        return res

    # gather all checks
    # replace with actual checks as needed
    (db_healthy, cache_healthy) = await asyncio.gather(
        dummy_check(),
        dummy_check(),
    )

    service_status = all([db_healthy, cache_healthy])
    if not service_status:
        # Force a 503 status code
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "global_status": "ok" if service_status else "fail",
        "db_healthy": "ok" if db_healthy else "fail",
        "cache_healthy": "ok" if cache_healthy else "fail",
    }
