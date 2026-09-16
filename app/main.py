from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.health import router as health_router
from app.api.auth import router as auth_router
from app.api.documents import router as documents_router
from app.api.search import router as search_router
from app.api.rag import router as rag_router
from app.api.conversations import router as conversations_router
from app.api.admin import router as admin_router
from app.core.config import get_settings
from app.core.http_middleware import HttpObservabilityMiddleware
from app.core.logging import configure_logging
from app.core.redis import close_redis_client, create_redis_client
from app.db.session import engine


def check_database() -> None:
    with engine.connect() as connection:
        connection.execute(text("SELECT 1"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    redis = await create_redis_client(get_settings())
    app.state.redis = redis
    try:
        # Fail startup if PostgreSQL cannot be reached with these credentials.
        await run_in_threadpool(check_database)
        yield
    finally:
        await close_redis_client(redis)
        await run_in_threadpool(engine.dispose)


settings = get_settings()
configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name, lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[str(settings.frontend_origin).rstrip("/")],
    allow_credentials=False,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Accept", "Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID"],
)
app.add_middleware(HttpObservabilityMiddleware)
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(documents_router)
app.include_router(search_router)
app.include_router(rag_router)
app.include_router(conversations_router)
app.include_router(admin_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    # FastAPI's default validation response may echo plaintext request input.
    errors = [
        {"loc": error["loc"], "msg": error["msg"], "type": error["type"]}
        for error in exc.errors()
    ]
    return JSONResponse(status_code=422, content={"detail": errors})
