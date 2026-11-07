import pytest

from py_app_tmpl.main import main


def test_main_logging(caplog: pytest.LogCaptureFixture) -> None:
    with caplog.at_level("INFO"):
        main()
    assert "Application started" in caplog.text
