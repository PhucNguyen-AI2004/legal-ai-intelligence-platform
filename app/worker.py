from redis import Redis
from rq import Queue, Worker

from app.core.config import get_settings
from app.core.logging import configure_logging


def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)
    connection = Redis.from_url(
        str(settings.redis_url),
        socket_connect_timeout=settings.redis_timeout_seconds,
        socket_timeout=settings.redis_timeout_seconds,
        health_check_interval=30,
    )
    try:
        Worker([Queue(settings.document_queue_name, connection=connection)], connection=connection).work()
    finally:
        connection.close()


if __name__ == "__main__":
    main()
