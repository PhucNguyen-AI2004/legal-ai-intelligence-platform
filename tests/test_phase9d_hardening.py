import logging
from contextlib import nullcontext
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from app.api import documents as documents_api
from app.core.logging import JsonFormatter
from app.core.queue import get_document_queue
from app.core.rate_limit import RateLimitBackendError, get_rate_limiter
from app.main import app
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.workers import document_jobs


PASSWORD = "SyntheticPassword123!"
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff",
    "X-Frame-Options": "DENY",
    "Referrer-Policy": "no-referrer",
}


def account(client, email: str) -> dict[str, str]:
    assert client.post(
        "/auth/register",
        json={"email": email, "password": PASSWORD, "full_name": "Phase 9D User"},
    ).status_code == 201
    response = client.post("/auth/login", json={"email": email, "password": PASSWORD})
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def upload(client, headers: dict[str, str], content: bytes = b"Access rights and duties.") -> str:
    response = client.post(
        "/documents",
        headers=headers,
        files={"file": ("phase9d.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def assert_transport_hardening(response) -> None:
    assert response.headers["X-Request-ID"]
    for name, expected in SECURITY_HEADERS.items():
        assert response.headers[name] == expected


@pytest.mark.parametrize(
    ("method", "path", "kwargs", "expected"),
    [
        ("get", "/auth/me", {}, 401),
        ("get", f"/documents/{uuid4()}", {}, 401),
        ("post", "/rag/ask", {"json": {}}, 401),
    ],
)
def test_auth_error_paths_keep_request_id_and_security_headers(
    client, method, path, kwargs, expected,
):
    response = getattr(client, method)(path, **kwargs)
    assert response.status_code == expected
    assert_transport_hardening(response)


def test_validation_not_found_and_conflict_paths_keep_transport_hardening(client):
    headers = account(client, "phase9d-status@example.com")
    missing = client.get(f"/documents/{uuid4()}", headers=headers)
    invalid = client.post("/rag/ask", headers=headers, json={"question": ""})
    document_id = upload(client, headers)

    class RecordingQueue:
        def __init__(self):
            self.calls = 0

        def enqueue(self, *args, **kwargs):
            self.calls += 1
            return SimpleNamespace(id="phase9d-job")

    queue = RecordingQueue()
    app.dependency_overrides[get_document_queue] = lambda: queue
    try:
        accepted = client.post(f"/documents/{document_id}/process", headers=headers)
        conflict = client.post(f"/documents/{document_id}/process", headers=headers)
    finally:
        app.dependency_overrides.pop(get_document_queue, None)

    assert (missing.status_code, invalid.status_code) == (404, 422)
    assert (accepted.status_code, conflict.status_code, queue.calls) == (202, 409, 1)
    for response in (missing, invalid, conflict):
        assert_transport_hardening(response)


def test_rate_limit_failure_happens_before_queue_or_document_work(client, monkeypatch):
    headers = account(client, "phase9d-limit@example.com")
    document_id = upload(client, headers)

    class UnavailableLimiter:
        async def check(self, *args, **kwargs):
            raise RateLimitBackendError

    app.dependency_overrides[get_rate_limiter] = lambda: UnavailableLimiter()
    monkeypatch.setattr(
        documents_api,
        "enqueue_processing",
        lambda *args, **kwargs: pytest.fail("queue work ran after rate-limit rejection"),
    )
    try:
        response = client.post(f"/documents/{document_id}/process", headers=headers)
    finally:
        app.dependency_overrides.pop(get_rate_limiter, None)

    assert response.status_code == 503
    assert response.json() == {"detail": "Rate limiting service unavailable"}
    assert_transport_hardening(response)


def test_queue_failure_restores_authoritative_state_and_returns_safe_503(client, db_session):
    headers = account(client, "phase9d-queue@example.com")
    document_id = upload(client, headers)

    class FailedQueue:
        def enqueue(self, *args, **kwargs):
            raise RuntimeError("redis://private-host:6379/0")

    app.dependency_overrides[get_document_queue] = lambda: FailedQueue()
    try:
        response = client.post(f"/documents/{document_id}/process", headers=headers)
    finally:
        app.dependency_overrides.pop(get_document_queue, None)

    db_session.expire_all()
    document = db_session.get(Document, UUID(document_id))
    assert response.status_code == 503
    assert response.json() == {"detail": "Document queue unavailable"}
    assert "private-host" not in response.text
    assert document.status == "uploaded"
    assert document.embedding_status == "pending"
    assert_transport_hardening(response)


def test_duplicate_worker_delivery_is_idempotently_rejected(
    client, db_session, fake_embeddings, monkeypatch,
):
    headers = account(client, "phase9d-worker@example.com")
    document_id = upload(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))

    document_jobs.process_document_job(document_id, str(uuid4()))
    chunk_count = db_session.query(DocumentChunk).filter_by(document_id=UUID(document_id)).count()
    document_jobs.process_document_job(document_id, str(uuid4()))
    assert db_session.query(DocumentChunk).filter_by(document_id=UUID(document_id)).count() == chunk_count

    document.embedding_status = "indexing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "get_embedding_service", lambda: fake_embeddings)
    document_jobs.index_document_job(document_id, str(uuid4()))
    document_jobs.index_document_job(document_id, str(uuid4()))
    assert len(fake_embeddings.document_calls) == 1
    assert db_session.get(Document, UUID(document_id)).embedding_status == "indexed"


def test_foreign_owner_cannot_enqueue_or_discover_document(client):
    owner = account(client, "phase9d-owner@example.com")
    stranger = account(client, "phase9d-stranger@example.com")
    document_id = upload(client, owner)

    class ForbiddenQueue:
        def enqueue(self, *args, **kwargs):
            pytest.fail("foreign resource was enqueued")

    app.dependency_overrides[get_document_queue] = lambda: ForbiddenQueue()
    try:
        responses = [
            client.get(f"/documents/{document_id}", headers=stranger),
            client.post(f"/documents/{document_id}/process", headers=stranger),
            client.post(f"/documents/{document_id}/index", headers=stranger),
            client.get(f"/documents/{document_id}/chunks", headers=stranger),
            client.post(
                "/rag/ask",
                headers=stranger,
                json={"question": "What are the rights?", "document_ids": [document_id]},
            ),
        ]
    finally:
        app.dependency_overrides.pop(get_document_queue, None)

    assert [response.status_code for response in responses] == [404] * len(responses)
    assert {response.json()["detail"] for response in responses[:4]} == {"Document not found"}
    assert responses[4].json() == {"detail": "One or more documents were not found"}


def test_unexpected_error_is_generic_correlated_and_does_not_log_sentinels(
    client, monkeypatch, caplog,
):
    headers = account(client, "phase9d-500@example.com")
    sentinel = "database-password-sentinel"
    request_id = str(uuid4())
    monkeypatch.setattr(documents_api.documents, "list_documents", lambda *args: (_ for _ in ()).throw(RuntimeError(sentinel)))
    logger = logging.getLogger("app.http")
    logger.disabled = False
    with caplog.at_level(logging.INFO, logger="app.http"):
        response = client.get(
            "/documents", headers={**headers, "X-Request-ID": request_id}
        )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal server error"}
    assert response.headers["X-Request-ID"] == request_id
    assert sentinel not in response.text
    formatted = "\n".join(JsonFormatter().format(record) for record in caplog.records)
    assert sentinel not in formatted
    assert request_id in formatted
    assert_transport_hardening(response)
