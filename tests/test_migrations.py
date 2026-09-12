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
    assert "documents" in inspect(connection).get_table_names()
    assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0002_create_documents"
    command.check(config)


def test_documents_migration_preserves_existing_users(db_session):
    from uuid import uuid4
    from app.models.user import User

    connection = db_session.bind
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    command.downgrade(config, "0001_create_users")
    user_id = uuid4()
    connection.execute(User.__table__.insert().values(
        id=user_id, email="migration@example.com", hashed_password="test-only", full_name="Existing user"
    ))
    command.upgrade(config, "head")
    assert connection.scalar(User.__table__.select().with_only_columns(User.id)) == user_id
    foreign_keys = inspect(connection).get_foreign_keys("documents")
    assert any(fk["referred_table"] == "users" and fk["options"].get("ondelete") == "RESTRICT" for fk in foreign_keys)
    command.check(config)
