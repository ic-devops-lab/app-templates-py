import pytest

from py_app_tmpl.api.checks import CheckResult, CheckStatus
from py_app_tmpl.db.pg_checks import check_postgres


@pytest.mark.asyncio
async def test_check_postgres_disabled() -> None:
    res: CheckResult = await check_postgres({}, False)

    assert res is not None
    assert res.name == "postgres"
    assert res.status == CheckStatus.DISABLED


@pytest.mark.asyncio
async def test_check_postgres_engine_is_none() -> None:
    res: CheckResult = await check_postgres(None, True)

    assert res is not None
    assert res.name == "postgres"
    assert res.status == CheckStatus.FAIL


@pytest.mark.postgres
@pytest.mark.asyncio
async def test_check_postgres_engine_has_wrong_type(override_settings: pytest.MonkeyPatch) -> None:
    override_settings.setenv("POSTGRES_ENABLED", "True")

    res: CheckResult = await check_postgres({}, True)

    assert res is not None
    assert res.name == "postgres"
    assert res.status == CheckStatus.FAIL
