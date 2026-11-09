import logging

from py_app_tmpl.core.config import Settings, get_settings
from py_app_tmpl.core.logging import configure_logging

logger = logging.getLogger(__name__)


def main() -> None:
    settings: Settings = get_settings()
    configure_logging(settings.log_level)

    logger.info("Application started")
    logger.debug("Debug mode enabled")
