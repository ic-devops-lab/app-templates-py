import logging
import sys


def configure_logging(level: str = "INFO", force: bool = False) -> None:
    """
    Configure the root logger with the specified level and output to stdout.

    Args:
        level (str): The logging level (default: "INFO").
        force (bool): Whether to force reconfiguration of the logging system (default: False).

    Note:
        logging.basicConfig() does nothing if the root logger already has handlers,
        unless force=True is used.
    """
    logging.basicConfig(
        level=level.upper(),
        format=("%(asctime)s %(levelname)s [%(name)s] %(message)s"),
        handlers=[logging.StreamHandler(sys.stdout)],
        force=force,
    )
