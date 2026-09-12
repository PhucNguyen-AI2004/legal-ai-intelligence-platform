from logging.config import fileConfig

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import Connection

from app.core.config import get_settings
from app.db.base import Base
from app import models  # noqa: F401 -- register model metadata for autogenerate

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    context.configure(
        url=str(get_settings().database_url),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # Tests supply an isolated connection; normal CLI runs use DATABASE_URL.
    supplied_connection = config.attributes.get("connection")
    if supplied_connection is not None:
        configure_connection(supplied_connection)
        return

    connectable = create_engine(
        str(get_settings().database_url),
        poolclass=pool.NullPool,
        connect_args={"connect_timeout": 5},
    )
    try:
        with connectable.connect() as connection:
            configure_connection(connection)
    finally:
        connectable.dispose()


def configure_connection(connection: Connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
