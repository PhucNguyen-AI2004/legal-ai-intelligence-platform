import logging
from contextlib import nullcontext
from pathlib import Path
from types import SimpleNamespace
from uuid import UUID, uuid4

import pytest
from sqlalchemy.exc import OperationalError

from app.core.queue import get_document_queue
from app.core.config import get_settings
from app.core.rate_limit import RateLimitPolicy, RateLimitResult, get_rate_limiter
from app.main import app
from app.models.document import Document
from app.services import document_processing
from app.services.document_storage import DocumentStorage
from app.workers import document_jobs


class RecordingQueue:
    def __init__(self, error=None):
        self.calls = []
        self.error = error

    def enqueue(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        if self.error:
            raise self.error
        return SimpleNamespace(id=f"job-{len(self.calls)}")


def account(client, email):
    password = "SyntheticPassword123!"
    assert client.post("/auth/register", json={
        "email": email, "password": password, "full_name": "Worker Test"
    }).status_code == 201
    response = client.post("/auth/login", json={"email": email, "password": password})
    return {"Authorization": "Bearer " + response.json()["access_token"]}


def uploaded_document(client, headers, content=b"Article one. Access rights."):
    response = client.post(
        "/documents", headers=headers,
        files={"file": ("law.txt", content, "text/plain")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_owner_enqueues_processing_without_inline_work(client, db_session, monkeypatch):
    headers = account(client, "enqueue@example.com")
    document_id = uploaded_document(client, headers)
    queue = RecordingQueue()
    app.dependency_overrides[get_document_queue] = lambda: queue
    monkeypatch.setattr(
        document_processing, "extract_text",
        lambda *args: pytest.fail("expensive processing executed in HTTP request"),
    )
    request_id = str(uuid4())
    try:
        response = client.post(
            f"/documents/{document_id}/process", headers={**headers, "X-Request-ID": request_id}
        )
    finally:
        app.dependency_overrides.pop(get_document_queue, None)

    assert response.status_code == 202
    assert response.json() == {
        "document_id": document_id, "job_id": "job-1", "job_type": "process", "status": "queued"
    }
    args, kwargs = queue.calls[0]
    assert args == ("app.workers.document_jobs.process_document_job", document_id, request_id)
    assert kwargs["job_timeout"] == "15m" and kwargs["result_ttl"] == 0
    assert db_session.get(Document, UUID(document_id)).status == "processing"
    assert client.post(f"/documents/{document_id}/process", headers=headers).status_code == 409


def test_non_owner_and_rate_limit_do_not_enqueue(client):
    owner = account(client, "queue-owner@example.com")
    other = account(client, "queue-other@example.com")
    document_id = uploaded_document(client, owner)
    queue = RecordingQueue()
    app.dependency_overrides[get_document_queue] = lambda: queue
    try:
        assert client.post(f"/documents/{document_id}/process", headers=other).status_code == 404
    finally:
        app.dependency_overrides.pop(get_document_queue, None)
    assert queue.calls == []


def test_rate_limited_request_does_not_enqueue(client):
    headers = account(client, "queue-limited@example.com")
    document_id = uploaded_document(client, headers)
    queue = RecordingQueue()

    class DenyLimiter:
        async def check(self, policy, identity_type, identity):
            assert policy == RateLimitPolicy.DOCUMENT_WRITE
            return RateLimitResult(1, 0, 30, False)

    app.dependency_overrides[get_document_queue] = lambda: queue
    app.dependency_overrides[get_rate_limiter] = lambda: DenyLimiter()
    try:
        response = client.post(f"/documents/{document_id}/process", headers=headers)
    finally:
        app.dependency_overrides.pop(get_document_queue, None)
        app.dependency_overrides.pop(get_rate_limiter, None)
    assert response.status_code == 429
    assert queue.calls == []


def test_enqueue_failure_is_safe_and_restores_state(client, db_session):
    headers = account(client, "queue-failure@example.com")
    document_id = uploaded_document(client, headers)
    queue = RecordingQueue(RuntimeError("redis://private-host"))
    app.dependency_overrides[get_document_queue] = lambda: queue
    try:
        response = client.post(f"/documents/{document_id}/process", headers=headers)
    finally:
        app.dependency_overrides.pop(get_document_queue, None)
    assert response.status_code == 503
    assert response.json() == {"detail": "Document queue unavailable"}
    assert "private-host" not in response.text
    assert db_session.get(Document, UUID(document_id)).status == "uploaded"


def test_processed_document_enqueues_index_and_prevents_duplicate(client, db_session, document_storage):
    headers = account(client, "queue-index@example.com")
    document_id = uploaded_document(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    document_processing.process_document(
        document.id, document.owner_id, db_session, DocumentStorage(get_settings()),
        get_settings(), already_claimed=True,
    )
    queue = RecordingQueue()
    app.dependency_overrides[get_document_queue] = lambda: queue
    try:
        first = client.post(f"/documents/{document_id}/index", headers=headers)
        duplicate = client.post(f"/documents/{document_id}/index", headers=headers)
    finally:
        app.dependency_overrides.pop(get_document_queue, None)
    assert first.status_code == 202
    assert first.json()["job_type"] == "index"
    assert duplicate.status_code == 409
    assert db_session.get(Document, UUID(document_id)).embedding_status == "indexing"


def test_worker_processes_claimed_document_with_correlated_logs(
    client, db_session, document_storage, monkeypatch, caplog,
):
    headers = account(client, "worker-process@example.com")
    document_id = uploaded_document(client, headers, b"Access rights and duties.")
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))
    worker_logger = logging.getLogger("app.document_worker")
    worker_logger.disabled = False
    request_id = str(uuid4())
    with caplog.at_level(logging.INFO, logger="app.document_worker"):
        document_jobs.process_document_job(document_id, request_id)
    assert db_session.get(Document, UUID(document_id)).status == "processed"
    events = {getattr(record, "event", None): record for record in caplog.records}
    assert events["document_job_started"].request_id == request_id
    assert events["document_job_completed"].document_id == document_id


def test_worker_indexes_claimed_document(client, db_session, fake_embeddings, monkeypatch):
    headers = account(client, "worker-index@example.com")
    document_id = uploaded_document(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    document_processing.process_document(
        document.id, document.owner_id, db_session, DocumentStorage(get_settings()),
        get_settings(), already_claimed=True,
    )
    document.embedding_status = "indexing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))
    monkeypatch.setattr(document_jobs, "get_embedding_service", lambda: fake_embeddings)
    document_jobs.index_document_job(document_id, str(uuid4()))
    assert db_session.get(Document, UUID(document_id)).embedding_status == "indexed"
    assert len(fake_embeddings.document_calls) == 1


def test_permanent_worker_failure_sets_safe_state(client, db_session, monkeypatch):
    headers = account(client, "worker-failure@example.com")
    document_id = uploaded_document(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))
    monkeypatch.setattr(document_jobs, "process_document", lambda *args, **kwargs: (_ for _ in ()).throw(ValueError("private content")))
    document_jobs.process_document_job(document_id, str(uuid4()))
    document = db_session.get(Document, UUID(document_id))
    assert document.status == "failed"
    assert document.processing_error == "Document processing failed"
    assert "private" not in document.processing_error


def test_retryable_worker_failure_is_bounded_by_enqueue_policy(client, db_session, monkeypatch):
    headers = account(client, "worker-retry@example.com")
    document_id = uploaded_document(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))
    monkeypatch.setattr(
        document_jobs, "process_document",
        lambda *args, **kwargs: (_ for _ in ()).throw(OperationalError("statement", {}, Exception())),
    )
    with pytest.raises(document_jobs.RetryableDocumentJobError):
        document_jobs.process_document_job(document_id, str(uuid4()))
    assert db_session.get(Document, UUID(document_id)).status == "processing"


def test_final_retry_failure_callback_marks_document_failed(client, db_session, monkeypatch):
    headers = account(client, "worker-exhausted@example.com")
    document_id = uploaded_document(client, headers)
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    monkeypatch.setattr(document_jobs, "SessionLocal", lambda: nullcontext(db_session))
    job = SimpleNamespace(
        id="exhausted-job",
        args=(document_id, str(uuid4())),
        func_name="app.workers.document_jobs.process_document_job",
    )
    document_jobs.handle_job_failure(job, None, None, None, None)
    document = db_session.get(Document, UUID(document_id))
    assert document.status == "failed"
    assert document.processing_error == "Document processing failed"


def test_compose_persists_redis_and_declares_document_worker():
    compose = (Path(__file__).parents[1] / "docker-compose.yml").read_text(encoding="utf-8")
    assert '"--appendonly", "yes"' in compose
    assert '"--appendfsync", "everysec"' in compose
    assert "redis_data:/data" in compose
    assert "worker:" in compose
    assert '["python", "-m", "app.worker"]' in compose
