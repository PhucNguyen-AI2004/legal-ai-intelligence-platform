from typing import Annotated, Any

from fastapi import APIRouter, Depends
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import engine
from app.core.redis import get_redis_client

router = APIRouter()


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness only: this endpoint does not query PostgreSQL."""
    return {"status": "ok"}


def check_database_readiness() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@router.get("/ready", tags=["health"])
async def ready(
    redis: Annotated[Any, Depends(get_redis_client)],
) -> JSONResponse:
    """Readiness checks the currently required database and Redis dependencies."""
    try:
        await run_in_threadpool(check_database_readiness)
        if await redis.ping() is not True:
            raise RuntimeError("Redis readiness failed")
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})
