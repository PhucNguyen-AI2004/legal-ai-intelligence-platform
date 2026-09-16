from dataclasses import dataclass
from typing import Any

from fastapi import Request

from app.core.config import Settings


@dataclass(frozen=True)
class QueueRuntime:
    connection: Any
    queue: Any


def create_queue_runtime(settings: Settings) -> QueueRuntime:
    from redis import Redis
    from rq import Queue

    connection = Redis.from_url(
        str(settings.redis_url),
        socket_connect_timeout=settings.redis_timeout_seconds,
        socket_timeout=settings.redis_timeout_seconds,
        health_check_interval=30,
    )
    return QueueRuntime(connection, Queue(settings.document_queue_name, connection=connection))


def close_queue_runtime(runtime: QueueRuntime) -> None:
    runtime.connection.close()


def get_document_queue(request: Request) -> Any:
    return request.app.state.document_queue
