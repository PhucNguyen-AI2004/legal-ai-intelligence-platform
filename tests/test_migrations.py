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
    assert "document_chunks" in inspect(connection).get_table_names()
    assert connection.scalar(text("SELECT version_num FROM alembic_version")) == "0003_document_processing"
    command.check(config)


def test_processing_migration_preserves_documents(db_session):
    from uuid import uuid4
    import sqlalchemy as sa
    from app.models.user import User

    connection = db_session.bind
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    command.downgrade(config, "0002_create_documents")
    user_id, document_id = uuid4(), uuid4()
    connection.execute(User.__table__.insert().values(
        id=user_id, email="processing-migration@example.com", hashed_password="test-only", full_name="Existing owner"
    ))
    old_documents = sa.Table("documents", sa.MetaData(), autoload_with=connection)
    connection.execute(old_documents.insert().values(
        id=document_id if connection.dialect.name == "postgresql" else document_id.hex,
        owner_id=user_id if connection.dialect.name == "postgresql" else user_id.hex,
        original_filename="law.txt", stored_filename="old.txt", file_path="old.txt",
        file_type="txt", mime_type="text/plain", file_size=10, title="Existing law",
    ))
    command.upgrade(config, "head")
    assert connection.scalar(text("SELECT title FROM documents")) == "Existing law"
    assert connection.scalar(text("SELECT processing_error FROM documents")) is None
    constraints = inspect(connection).get_unique_constraints("document_chunks")
    assert any(item["column_names"] == ["document_id", "chunk_index"] for item in constraints)
    assert inspect(connection).get_foreign_keys("document_chunks")[0]["options"]["ondelete"] == "CASCADE"
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
