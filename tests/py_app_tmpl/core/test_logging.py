import logging

from py_app_tmpl.core.logging import configure_logging


def test_configure_logging_replaces_existing_handlers() -> None:
    root = logging.getLogger()
    original_handlers = root.handlers[:]
    original_level = root.level

    existing_handler = logging.NullHandler()

    try:
        root.addHandler(existing_handler)

        configure_logging(level="DEBUG", force=True)

        assert root.level == logging.DEBUG
        assert existing_handler not in root.handlers
        assert len(root.handlers) == 1

    finally:
        for handler in root.handlers[:]:
            root.removeHandler(handler)
            if handler not in original_handlers:
                handler.close()

        for handler in original_handlers:
            root.addHandler(handler)

        root.setLevel(original_level)
