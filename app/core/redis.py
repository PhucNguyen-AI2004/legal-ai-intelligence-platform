from typing import Any

from fastapi import Request

from app.core.config import Settings


async def create_redis_client(settings: Settings) -> Any:
    # Imported lazily so configuration and pure unit tests do not open sockets.
    from redis.asyncio import Redis

    return Redis.from_url(
        str(settings.redis_url),
        encoding="utf-8",
        decode_responses=True,
        socket_connect_timeout=settings.redis_timeout_seconds,
        socket_timeout=settings.redis_timeout_seconds,
        health_check_interval=30,
    )


async def close_redis_client(client: Any) -> None:
    await client.aclose()


def get_redis_client(request: Request) -> Any:
    return request.app.state.redis
