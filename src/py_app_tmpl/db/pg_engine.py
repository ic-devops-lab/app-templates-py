"""
imported only in the enabled branch (POSTGRES_ENABLED=True)
"""

import asyncio
import logging
import re

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlmodel import select

logger: logging.Logger = logging.getLogger(__name__)


def get_safe_db_url(url: str) -> str:
    """Return a safe version of the database URL with credentials masked."""
    pattern = r"(?<=://)(\w+):(.*?)(?=@)"
    subst = r"***:***"
    return re.sub(pattern, subst, url)


def build_engine(
    postgres_url: str, is_prod: bool = False, pool_pre_ping: bool = True
) -> AsyncEngine:
    """Create and cache one async engine per process."""
    safe_url = get_safe_db_url(postgres_url)
    logger.info(f"Creating PostgreSQL engine with URL: {safe_url}")
    try:
        return create_async_engine(
            postgres_url,
            echo=not is_prod,
            pool_pre_ping=pool_pre_ping,
        )
    except Exception as e:
        logger.error(f"Error creating database engine for URL {safe_url}!")
        raise RuntimeError(f"Error creating the database engine for URL {safe_url}.") from e


async def dispose_engine(engine: AsyncEngine) -> None:
    """Dispose of the database engine, closing all connections."""
    safe_url = get_safe_db_url(str(engine.url))
    try:
        await engine.dispose()
        logger.info(f"Disposed database engine for URL {safe_url}.")
    except Exception as e:
        logger.error(f"Error disposing database engine for URL {safe_url}!")
        raise RuntimeError(f"Error disposing database engine for URL {safe_url}.") from e


async def test_connection(engine: AsyncEngine) -> None:
    """Validate the database connection by executing a simple query."""
    safe_url = get_safe_db_url(str(engine.url))

    try:
        async with asyncio.timeout(3):  # Set a timeout for the connection test
            async with engine.connect() as conn:
                await conn.execute(select(1))
                logger.info("Database connection validated successfully.")
    except Exception as e:
        logger.error(f"Error initializing Postgres connection for URL {safe_url}!")
        raise RuntimeError("Error validating Postgres connection.") from e
