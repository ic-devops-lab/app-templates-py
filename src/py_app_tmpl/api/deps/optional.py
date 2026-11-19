# from fastapi import HTTPException, Request, status
# from sqlalchemy.ext.asyncio import AsyncEngine

# from ...core.config import Settings


# def get_pg_engine(request: Request) -> AsyncEngine | None:
#     """
#     Retrieve the database engine from the FastAPI request state when postgres
#     component is enabled.
#     """
#     settings: Settings = request.app.state.settings

#     if not settings.postgres_enabled:
#         return None

#     engine: AsyncEngine | None = getattr(request.app.state, "pg_engine", None)
#     if engine is None:
#         raise HTTPException(
#             status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
#             detail="Postgres database engine is not available.",
#         )

#     return engine
