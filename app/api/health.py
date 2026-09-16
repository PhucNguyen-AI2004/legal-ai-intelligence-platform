from fastapi import APIRouter
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db.session import engine

router = APIRouter()


@router.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Liveness only: this endpoint does not query PostgreSQL."""
    return {"status": "ok"}


def check_database_readiness() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@router.get("/ready", tags=["health"])
async def ready() -> JSONResponse:
    """Readiness checks only the currently required database dependency."""
    try:
        await run_in_threadpool(check_database_readiness)
    except Exception:
        return JSONResponse(status_code=503, content={"status": "not_ready"})
    return JSONResponse(status_code=200, content={"status": "ready"})
