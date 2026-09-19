import logging
from uuid import uuid4

from app.api import health as health_api
from app import main


def test_generated_request_id_and_security_headers(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.headers["X-Request-ID"]
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    assert response.headers["X-Frame-Options"] == "DENY"
    assert response.headers["Referrer-Policy"] == "no-referrer"


def test_valid_incoming_request_id_is_preserved(client):
    request_id = str(uuid4())
    response = client.get("/health", headers={"X-Request-ID": request_id.upper()})
    assert response.headers["X-Request-ID"] == request_id


def test_invalid_and_oversized_request_ids_are_replaced(client):
    for supplied in ("not-a-uuid", "x" * 1000):
        response = client.get("/health", headers={"X-Request-ID": supplied})
        assert response.headers["X-Request-ID"] != supplied
        assert len(response.headers["X-Request-ID"]) == 36


def test_generated_request_ids_are_distinct(client):
    first = client.get("/health").headers["X-Request-ID"]
    second = client.get("/health").headers["X-Request-ID"]
    assert first != second


def test_request_log_has_correlation_fields_without_sensitive_values(client, caplog):
    sentinels = {
        "token": "synthetic-token-must-not-appear",
        "password": "synthetic-password-must-not-appear",
        "prompt": "synthetic-question-must-not-appear",
        "document": "synthetic-document-body-must-not-appear",
    }
    request_id = str(uuid4())
    request_logger = logging.getLogger("app.http")
    # Alembic's test-time logging setup disables pre-existing application
    # loggers while the fixture applies migrations; production startup does not.
    request_logger.disabled = False
    with caplog.at_level(logging.INFO, logger="app.http"):
        response = client.post(
            "/auth/login?question=" + sentinels["prompt"],
            headers={"Authorization": "Bearer " + sentinels["token"], "X-Request-ID": request_id},
            json={"email": "nobody@example.com", "password": sentinels["password"], "body": sentinels["document"]},
        )

    record = next(record for record in caplog.records if getattr(record, "event", None) == "http.request.completed")
    assert record.request_id == request_id
    assert record.method == "POST"
    assert record.path == "/auth/login"
    assert record.status_code == response.status_code
    assert record.duration_ms >= 0
    combined = " ".join(record.getMessage() for record in caplog.records)
    assert all(value not in combined for value in sentinels.values())


def test_health_remains_liveness(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_when_database_available(client, monkeypatch):
    monkeypatch.setattr(health_api, "check_database_readiness", lambda: None)
    response = client.get("/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_ready_failure_is_safe(client, monkeypatch):
    internal_detail = "database-host-secret-detail"

    def fail():
        raise RuntimeError(internal_detail)

    monkeypatch.setattr(health_api, "check_database_readiness", fail)
    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
    assert internal_detail not in response.text


def test_configured_cors_origin_and_unconfigured_origin(client):
    allowed = client.options(
        "/auth/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert allowed.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert "authorization" in allowed.headers["Access-Control-Allow-Headers"].lower()

    denied = client.options(
        "/auth/me",
        headers={"Origin": "https://unconfigured.example", "Access-Control-Request-Method": "GET"},
    )
    assert "Access-Control-Allow-Origin" not in denied.headers


def test_docs_and_openapi_remain_available(client):
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_docs_use_configured_external_root_path_for_openapi(client):
    original_root_path = main.app.root_path
    main.app.root_path = "/api"
    try:
        response = client.get("/docs")
    finally:
        main.app.root_path = original_root_path

    assert response.status_code == 200
    assert "/api/openapi.json" in response.text
