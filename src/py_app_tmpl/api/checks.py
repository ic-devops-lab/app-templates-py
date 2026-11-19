import asyncio
import logging

# from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from enum import StrEnum

# from typing import TypeAlias

logger: logging.Logger = logging.getLogger(__name__)


class CheckStatus(StrEnum):
    OK = "ok"
    FAIL = "fail"
    DISABLED = "disabled"


@dataclass(frozen=True)
class CheckResult:
    name: str
    status: CheckStatus


# ReadinessCheck: TypeAlias = Callable[[], Awaitable[CheckResult]]


async def dummy_check(
    name: str, status: CheckStatus = CheckStatus.OK, enabled: bool = True
) -> CheckResult:
    """A dummy check that returns OK if enabled, otherwise DISABLED.
    Use for testing or as a placeholder.
    """
    await asyncio.sleep(0.1)
    return CheckResult(name, status if enabled else CheckStatus.DISABLED)


# async def _run_check(
#     name: str,
#     check: ReadinessCheck,
#     timeout: float = 2.0,
# ) -> CheckResult:
#     try:
#         async with asyncio.timeout(timeout):
#             result = await check()

#         if result.name != name:
#             raise ValueError(f"Check {name!r} returned name {result.name!r}")

#         return result

#     except Exception:
#         logger.exception("Readiness check %s failed", name)
#         return CheckResult(name, CheckStatus.FAIL)


# async def run_checks(
#     checks: dict[str, ReadinessCheck],
# ) -> dict[str, CheckStatus]:
#     results: list[CheckResult] = await asyncio.gather(
#         *(_run_check(name, check) for name, check in checks.items())
#     )

#     return {result.name: result.status for result in results}
