from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

import jwt
import pytest
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError

from app.core.config import get_settings
from app.core.security import create_access_token, verify_password
from app.models.user import User

USER = {
    "email": "student@example.com",
    "password": "StrongPassword123!",
    "full_name": "Test User",
}


def register(client):
    response = client.post("/auth/register", json=USER)
    assert response.status_code == 201, response.text
    return response.json()


def test_register_returns_public_user_and_hashes_password(client, db_session):
    data = register(client)
    assert UUID(data["id"])
    assert data["email"] == USER["email"]
    assert data["full_name"] == USER["full_name"]
    assert data["is_active"] is True
    assert data["created_at"] and data["updated_at"]
    assert "password" not in data and "hashed_password" not in data
    stored = db_session.get(User, UUID(data["id"]))
    assert stored.hashed_password != USER["password"]
    assert stored.hashed_password.startswith("$argon2id$")
    assert verify_password(USER["password"], stored.hashed_password)
    if db_session.bind.dialect.name == "postgresql":
        assert stored.created_at.tzinfo is not None
        assert stored.updated_at.tzinfo is not None


def test_duplicate_email_is_case_insensitive(client):
    register(client)
    response = client.post("/auth/register", json={**USER, "email": " STUDENT@EXAMPLE.COM "})
    assert response.status_code == 409
    assert response.json()["detail"] == "Email already registered"


def test_login_and_me(client):
    user = register(client)
    response = client.post("/auth/login", json={
        "email": "STUDENT@example.com", "password": USER["password"]
    })
    assert response.status_code == 200
    assert response.headers["cache-control"] == "no-store"
    data = response.json()
    assert set(data) == {"access_token", "token_type"}
    assert data["token_type"] == "bearer"
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {data['access_token']}"})
    assert response.status_code == 200
    assert response.json() == user


@pytest.mark.parametrize("email,password", [
    (USER["email"], "wrong-password"),
    ("unknown@example.com", USER["password"]),
])
def test_login_rejects_invalid_credentials(client, email, password):
    register(client)
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
    assert response.json()["detail"] == "Could not validate credentials"


@pytest.mark.parametrize("headers", [{}, {"Authorization": "Bearer garbage"}, {"Authorization": "Basic abc"}])
def test_me_rejects_missing_or_invalid_token(client, headers):
    response = client.get("/auth/me", headers=headers)
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"


@pytest.mark.parametrize("case", ["expired", "wrong_signature", "missing_exp", "invalid_sub", "wrong_type", "wrong_algorithm"])
def test_me_rejects_invalid_claims(client, case):
    user = register(client)
    now = datetime.now(timezone.utc)
    claims = {"sub": user["id"], "iat": now, "exp": now + timedelta(minutes=5), "token_type": "access"}
    key = get_settings().secret_key.get_secret_value()
    algorithm = "HS256"
    if case == "expired":
        claims["exp"] = now - timedelta(minutes=1)
    elif case == "wrong_signature":
        key = "different-test-signing-key-that-is-long-enough"
    elif case == "missing_exp":
        del claims["exp"]
    elif case == "invalid_sub":
        claims["sub"] = "not-a-uuid"
    elif case == "wrong_type":
        claims["token_type"] = "refresh"
    elif case == "wrong_algorithm":
        algorithm = "HS384"
    token = jwt.encode(claims, key, algorithm=algorithm)
    response = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 401


def test_me_rejects_deleted_user(client):
    token = create_access_token(uuid4())
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 401


def test_inactive_user_cannot_login_or_use_existing_token(client, db_session):
    user = register(client)
    token = create_access_token(UUID(user["id"]))
    stored = db_session.get(User, UUID(user["id"]))
    stored.is_active = False
    db_session.commit()
    assert client.post("/auth/login", json={"email": USER["email"], "password": USER["password"]}).status_code == 401
    assert client.get("/auth/me", headers={"Authorization": f"Bearer {token}"}).status_code == 403


@pytest.mark.parametrize("changes", [
    {"password": "short"}, {"password": "x" * 129}, {"password": " " * 12},
    {"email": "invalid-email"}, {"full_name": "   "}, {"is_active": True},
])
def test_registration_validation_never_echoes_password(client, changes):
    payload = {**USER, **changes}
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 422
    assert payload["password"] not in response.text
    assert all("input" not in error for error in response.json()["detail"])


def test_malformed_request_does_not_echo_secrets(client):
    response = client.post("/auth/register", json=[USER])
    assert response.status_code == 422
    assert USER["password"] not in response.text


def test_database_unique_index_and_migration(db_session):
    inspector = inspect(db_session.bind)
    assert any(i["name"] == "ix_users_email" and i["unique"] for i in inspector.get_indexes("users"))
    assert db_session.scalar(text("SELECT version_num FROM alembic_version")) == "0003_document_processing"
    db_session.add(User(email="unique@example.com", hashed_password="test-only", full_name="One"))
    db_session.commit()
    db_session.add(User(email="unique@example.com", hashed_password="test-only", full_name="Two"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_concurrent_duplicate_conflict_is_mapped(client, db_session, monkeypatch):
    if db_session.bind.dialect.name != "postgresql":
        pytest.skip("PostgreSQL SQLSTATE and constraint diagnostics required")
    register(client)
    # Simulate a stale pre-check: the database constraint must still return 409.
    monkeypatch.setattr(db_session, "scalar", lambda *args, **kwargs: None)
    response = client.post("/auth/register", json=USER)
    assert response.status_code == 409
    assert db_session.execute(select(User.id)).scalar_one()


def test_health_and_swagger_contract(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.get("/docs").status_code == 200
    spec = client.get("/openapi.json").json()
    scheme = spec["components"]["securitySchemes"]["HTTPBearer"]
    assert scheme["scheme"] == "bearer"
    assert spec["paths"]["/auth/me"]["get"]["security"] == [{"HTTPBearer": []}]
    assert "application/json" in spec["paths"]["/auth/login"]["post"]["requestBody"]["content"]
    assert "password" not in spec["components"]["schemas"]["UserRead"]["properties"]
