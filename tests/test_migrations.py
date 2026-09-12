from alembic import command
from alembic.config import Config
from sqlalchemy import inspect, text

from app.core.config import PROJECT_ROOT


def test_migration_downgrade_upgrade_and_metadata_match(db_session):
    # The fixture's outer transaction isolates this DDL round-trip.
    connection = db_session.bind
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    command.downgrade(config, "base")
    assert "users" not in inspect(connection).get_table_names()
    command.upgrade(config, "head")
    assert "users" in inspect(connection).get_table_names()
    assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0001_create_users"
    command.check(config)
