"""
Postgres database readiness checks.
"""

import asyncio
import logging

from ..api.checks import CheckResult, CheckStatus

logger: logging.Logger = logging.getLogger(__name__)


async def check_postgres(
    engine: object | None,
    enabled: bool,
) -> CheckResult:
    if not enabled:
        return CheckResult("postgres", CheckStatus.DISABLED)

    if engine is None:
        return CheckResult("postgres", CheckStatus.FAIL)

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import AsyncEngine

    if not isinstance(engine, AsyncEngine):
        return CheckResult("postgres", CheckStatus.FAIL)

    try:
        async with asyncio.timeout(3):
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
    except Exception as _:
        logger.error("Postgres check failed")
        return CheckResult("postgres", CheckStatus.FAIL)

    return CheckResult("postgres", CheckStatus.OK)
