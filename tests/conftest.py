"""Fast default tests use SQLite; TEST_DATABASE_URL enables real PostgreSQL.

Only a database whose name ends in _test is accepted. Each run creates and
removes its own schema; application tables outside that schema are untouched.
"""
import os
import secrets
from uuid import uuid4

# Set isolated configuration before importing application modules; never use .env secrets.
os.environ["APP_ENV"] = "test"
os.environ["APP_NAME"] = "Legal AI Auth Tests"
os.environ["SECRET_KEY"] = secrets.token_urlsafe(48)
os.environ["ALGORITHM"] = "HS256"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "30"
os.environ["DATABASE_URL"] = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:1/legal_ai_test"
)

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session
from sqlalchemy.schema import CreateSchema, DropSchema

from app import main
from app.core.config import PROJECT_ROOT
from app.db.session import get_db


@pytest.fixture(scope="session")
def db_engine(tmp_path_factory):
    database_url = os.environ.get("TEST_DATABASE_URL")
    admin_engine = None
    schema = None
    if database_url:
        url = make_url(database_url)
        if url.drivername != "postgresql+psycopg" or not (url.database or "").endswith("_test"):
            raise ValueError("TEST_DATABASE_URL must use psycopg and a database ending in _test")
        schema = f"auth_test_{uuid4().hex}"
        admin_engine = create_engine(url)
        with admin_engine.begin() as connection:
            connection.execute(CreateSchema(schema))
        engine = create_engine(url, connect_args={"options": f"-csearch_path={schema}"})
    else:
        path = tmp_path_factory.mktemp("auth") / "auth.db"
        engine = create_engine(f"sqlite:///{path}", connect_args={"check_same_thread": False})

    try:
        # Exercise the actual migration, never Base.metadata.create_all().
        config = Config(str(PROJECT_ROOT / "alembic.ini"))
        with engine.begin() as connection:
            config.attributes["connection"] = connection
            command.upgrade(config, "head")
        yield engine
    finally:
        engine.dispose()
        if admin_engine is not None:
            try:
                with admin_engine.begin() as connection:
                    connection.execute(DropSchema(schema, cascade=True))
            finally:
                admin_engine.dispose()


@pytest.fixture
def db_session(db_engine):
    with db_engine.connect() as connection:
        # Explicit SQL BEGIN avoids SQLite's legacy SAVEPOINT transaction behavior.
        if db_engine.dialect.name == "sqlite":
            connection.exec_driver_sql("BEGIN")
            transaction = connection.get_transaction()
        else:
            transaction = connection.begin()
        with Session(bind=connection, join_transaction_mode="create_savepoint") as session:
            try:
                yield session
            finally:
                session.close()
                transaction.rollback()


@pytest.fixture
def client(db_session, db_engine, monkeypatch):
    def override_get_db():
        yield db_session

    main.app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(main, "engine", db_engine)
    try:
        with TestClient(main.app) as test_client:
            yield test_client
    finally:
        main.app.dependency_overrides.clear()
