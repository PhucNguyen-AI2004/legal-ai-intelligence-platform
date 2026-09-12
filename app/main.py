from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import text

from app.api.health import router as health_router
from app.core.config import get_settings
from app.db.session import engine


def check_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    try:
        # Fail startup if PostgreSQL cannot be reached with these credentials.
        await run_in_threadpool(check_database)
        yield
    finally:
        await run_in_threadpool(engine.dispose)


app = FastAPI(title=get_settings().app_name, lifespan=lifespan)
app.include_router(health_router)
