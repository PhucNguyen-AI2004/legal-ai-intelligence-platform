from uuid import UUID

import pytest
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError
from alembic import command
from alembic.config import Config

from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.core.security import create_access_token
from app.core.config import PROJECT_ROOT
from app.scripts.promote_user import promote_user


def account(client, db_session, name, role="user"):
    response = client.post("/auth/register", json={"email": f"{name}@example.com", "password": "TestPassword123!", "full_name": name})
    assert response.status_code == 201
    user = db_session.get(User, UUID(response.json()["id"]))
    user.role = role
    db_session.commit()
    return user, {"Authorization": f"Bearer {create_access_token(user.id)}"}


@pytest.mark.parametrize("route", ["overview", "users", "documents"])
def test_admin_authorization(client, db_session, route):
    assert client.get(f"/admin/{route}").status_code == 401
    user, headers = account(client, db_session, "normal")
    assert client.get(f"/admin/{route}", headers=headers).status_code == 403
    user.role = "admin"
    db_session.commit()
    response = client.get(f"/admin/{route}", headers=headers)
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    user.role = "user"
    db_session.commit()
    assert client.get(f"/admin/{route}", headers=headers).status_code == 403


def test_registration_and_me_role(client, db_session):
    response = client.post("/auth/register", json={"email": "attempt@example.com", "password": "TestPassword123!", "full_name": "Attempt", "role": "admin"})
    assert response.status_code == 422
    user, headers = account(client, db_session, "ordinary")
    assert user.role == "user"
    assert client.get("/auth/me", headers=headers).json()["role"] == "user"
    assert promote_user(db_session, " ORDINARY@EXAMPLE.COM ") is True
    assert client.get("/auth/me", headers=headers).json()["role"] == "admin"


def test_promotion_idempotent_missing(client, db_session):
    user, _ = account(client, db_session, "operator")
    assert promote_user(db_session, user.email) is True
    assert promote_user(db_session, user.email) is True
    assert user.role == "admin"
    assert promote_user(db_session, "missing@example.com") is False
    assert len(db_session.scalars(select(User)).all()) == 1


def test_overview_and_global_metadata_privacy(client, db_session):
    admin, headers = account(client, db_session, "admin", "admin")
    owner, owner_headers = account(client, db_session, "owner")
    docs = []
    for user, status, embedding in [(admin, "processed", "indexed"), (owner, "failed", "failed")]:
        doc = Document(owner_id=user.id, original_filename=f"{user.id}.txt", stored_filename=f"{user.id}.txt", file_path="private-storage-key", file_type="txt", mime_type="text/plain", file_size=20, title="Metadata", description="PRIVATE DESCRIPTION", status=status, embedding_status=embedding, processing_error="PRIVATE ERROR")
        db_session.add(doc)
        docs.append(doc)
    conversation = Conversation(user_id=owner.id, title="PRIVATE TITLE")
    db_session.add(conversation)
    db_session.flush()
    db_session.add(Message(conversation_id=conversation.id, role="user", content="PRIVATE PROMPT", sequence_number=1))
    db_session.commit()
    overview = client.get("/admin/overview", headers=headers).json()
    assert overview == {"total_users": 2, "total_documents": 2, "total_conversations": 1, "total_messages": 1, "processing_counts": {"processed": 1, "failed": 1}, "embedding_counts": {"indexed": 1, "failed": 1}}
    response = client.get("/admin/documents", headers=headers)
    body = response.json()
    assert body["total"] == 2
    assert {row["owner_email"] for row in body["items"]} == {admin.email, owner.email}
    allowed = {"id", "owner_id", "owner_email", "title", "original_filename", "file_type", "file_size", "status", "embedding_status", "created_at"}
    assert all(set(row) == allowed for row in body["items"])
    for forbidden in ["PRIVATE", "private-storage-key", "hashed_password", "embedding_error", "content", "file_path"]:
        assert forbidden not in response.text
    filtered = client.get("/admin/documents?status=failed&embedding_status=failed&limit=1", headers=headers).json()
    assert filtered["total"] == 1 and filtered["items"][0]["owner_id"] == str(owner.id)
    assert client.get("/admin/documents?skip=1&limit=1", headers=headers).json()["items"][0]["id"] != client.get("/admin/documents?limit=1", headers=headers).json()["items"][0]["id"]
    assert client.get("/admin/documents?status=bogus", headers=headers).status_code == 422
    assert client.get("/admin/documents?limit=101", headers=headers).status_code == 422
    # Admin metadata access never changes the ordinary owner-scoped endpoints.
    assert client.get(f"/documents/{docs[0].id}", headers=owner_headers).status_code == 404
    assert client.get(f"/documents/{docs[1].id}", headers=headers).status_code == 404
    assert client.get(f"/conversations/{conversation.id}", headers=headers).status_code == 404
    assert client.get("/documents", headers=owner_headers).json()["total"] == 1


def test_users_search_pagination_allowlist(client, db_session):
    _, headers = account(client, db_session, "admin", "admin")
    account(client, db_session, "someone")
    first = client.get("/admin/users?limit=1", headers=headers).json()
    second = client.get("/admin/users?limit=1&skip=1", headers=headers).json()
    assert first["total"] == second["total"] == 2
    assert first["items"][0]["id"] != second["items"][0]["id"]
    assert set(first["items"][0]) == {"id", "email", "role", "created_at"}
    assert client.get("/admin/users?email=SOMEONE", headers=headers).json()["total"] == 1
    assert client.get("/admin/users?email=%25", headers=headers).json()["total"] == 0
    assert client.get("/admin/users?skip=-1", headers=headers).status_code == 422


def test_role_migration_preserves_existing_users_and_enforces_check(db_session):
    connection = db_session.bind
    config = Config(str(PROJECT_ROOT / "alembic.ini"))
    config.attributes["connection"] = connection
    command.downgrade(config, "0005_conversations_and_messages")
    connection.execute(text("INSERT INTO users (id, email, hashed_password, full_name) VALUES ('00000000000000000000000000000001', 'old@example.com', 'test-only', 'Existing')"))
    command.upgrade(config, "head")
    assert connection.scalar(text("SELECT role FROM users WHERE email='old@example.com'")) == "user"
    with pytest.raises(IntegrityError):
        with connection.begin_nested():
            connection.execute(text("UPDATE users SET role='super-admin' WHERE email='old@example.com'"))
