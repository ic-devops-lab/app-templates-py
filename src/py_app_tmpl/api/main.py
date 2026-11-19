import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

import uvicorn
from fastapi import FastAPI
from gunicorn.app.base import BaseApplication

from ..core.config import Settings, get_settings, validate_api_settings
from ..core.logging import configure_logging
from .routers.system import router as system_router

logger: logging.Logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, Any]:
    """Lifespan context manager for FastAPI application.

    Called when the application starts and stops. Initializes the database
    connection and language detector on startup, and closes them on shutdown.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    logger.info("Starting application lifespan...")
    # Initialize resources here, e.g., database connection, language detector, etc.
    logger.info("Application startup complete.")

    settings = get_settings()
    app.state.settings = settings

    try:
        if settings.postgres_enabled:
            from ..db.pg_engine import build_engine, dispose_engine
            from ..db.pg_session import make_session_factory

            engine = build_engine(
                settings.postgres_url or "",
                is_prod=settings.app_env == settings.app_prod_env_name,
            )
            app.state.pg_engine = engine
            app.state.pg_sessionmaker = make_session_factory(engine)

        yield
    finally:
        # Clean up resources here, e.g., close database connection, etc.
        if settings.postgres_enabled and hasattr(app.state, "pg_engine") and app.state.pg_engine:
            await dispose_engine(app.state.pg_engine)  # type: ignore
        logger.info("Application shutdown complete.")


def create_app() -> FastAPI:
    """
    Create and configure the FastAPI application.

    Returns:
        FastAPI: The configured FastAPI application instance.
    """
    logger.info("Creating FastAPI application...")
    settings: Settings = get_settings()
    app = FastAPI(
        lifespan=lifespan,
        title=settings.app_name,
        version=settings.app_version,
        docs_url="/docs" if settings.app_env != "prod" else None,
        redoc_url="/redoc" if settings.app_env != "prod" else None,
        openapi_url="/openapi.json" if settings.app_env != "prod" else None,
    )

    logger.info("Adding routes and endpoints...")
    app.include_router(system_router)

    logger.info("FastAPI application created.")
    return app


class GunicornApp(BaseApplication):
    """
    Custom Gunicorn application class to run the FastAPI app.
    """

    def __init__(self, app: FastAPI, options: dict[str, Any] | None = None) -> None:
        """
        Initialize the Gunicorn application with the FastAPI app and options.

        Args:
            application (FastAPI): The FastAPI application instance.
            options (dict, optional): Gunicorn configuration options. Defaults to None.
        """
        self.options = options or {}
        self.application = app

        super().__init__()

    def load_config(self) -> None:
        """
        Load the Gunicorn configuration from the provided options.
        """
        for key, value in self.options.items():
            if value is None:
                continue

            normalized_key = key.lower()
            if normalized_key in self.cfg.settings:
                self.cfg.set(normalized_key, value)
            else:
                logger.warning("Ignoring unknown Gunicorn setting: %s", key)

    def load(self) -> FastAPI:
        """
        Load the FastAPI application instance.

        Returns:
            FastAPI: The FastAPI application instance.
        """
        return self.application


def main() -> None:
    """
    Main entry point for running the FastAPI application.
    """
    settings: Settings = get_settings()
    configure_logging(settings.log_level)

    try:
        validate_api_settings(settings)
    except ValueError as e:
        logger.error(str(e))
        raise

    if settings.api_workers_count == 1:
        logger.info("Starting FastAPI application with Uvicorn...")
        uvicorn.run(
            "py_app_tmpl.api.main:create_app",
            factory=True,
            host=settings.api_host,
            port=settings.api_port,
            reload=settings.api_reload,
            log_level=settings.log_level.lower(),
        )
    else:
        logger.info("Starting FastAPI application with Gunicorn...")
        gunicorn_options: dict[str, Any] = {
            "bind": f"{settings.api_host}:{settings.api_port}",
            "workers": settings.api_workers_count,
            "worker_class": "uvicorn_worker.UvicornWorker",
            "loglevel": settings.log_level.lower(),
            "accesslog": "-",  # Log access to stdout
            "errorlog": "-",  # Log errors to stderr
        }

        # Run Gunicorn programmatically
        GunicornApp(create_app(), gunicorn_options).run()
