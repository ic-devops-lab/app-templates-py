import asyncio
import logging
from typing import Any

from fastapi import APIRouter, Request, Response, status

from ...api.checks import CheckResult, CheckStatus, dummy_check
from ...core.config import Settings, get_settings
from ...db.pg_checks import check_postgres

logger: logging.Logger = logging.getLogger(__name__)

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
        "api_reload": settings.api_reload,
        "postgres_enabled": settings.postgres_enabled,
        "metrics_enabled": settings.metrics_enabled,
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
async def get_readyness_probe(
    request: Request,
    response: Response,
) -> dict[str, str]:
    """
    # Run dependency checks concurrently to avoid performance bottlenecks
    # Example:
    # db_healthy, cache_healthy = await asyncio.gather(
    #     check_database(),
    #     check_cache()
    # )
    """
    pg_enabled: bool = request.app.state.settings.postgres_enabled
    pg_engine = getattr(request.app.state, "pg_engine", None)

    # gather all checks
    # replace with actual checks as needed
    checks: tuple[CheckResult, ...] = await asyncio.gather(
        check_postgres(pg_engine, pg_enabled),
        dummy_check("cache_placeholder"),
        dummy_check("mq_placeholder"),
    )
    check_list: list[CheckResult] = list(checks)

    service_status = (
        "fail" if any([check.status == CheckStatus.FAIL for check in check_list]) else "ok"
    )
    if service_status == "fail":
        # Force a 503 status code
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE

    return {
        "global_status": service_status,
        **{check.name: check.status.value for check in check_list},
    }


@router.get("/async_home", response_model=dict)
async def async_root() -> dict[str, str]:  # type: ignore
    return {"message": "Python Project Template Async API Home"}


router.get("/")(lambda: {"message": "Python Project Template API"})
