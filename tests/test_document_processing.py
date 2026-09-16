from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import get_settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services import document_processing


def headers_for(client, email):
    password = "StrongPassword123!"
    assert client.post("/auth/register", json={"email": email, "password": password, "full_name": "Processor"}).status_code == 201
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def processing_document(client):
    headers = headers_for(client, "processor@example.com")
    content = ("Điều 1. Nội dung pháp luật.\n\n" * 150).encode()
    response = client.post("/documents", headers=headers, files={"file": ("law.txt", content, "text/plain")})
    assert response.status_code == 201
    return headers, response.json()["id"]


def test_process_and_paginated_chunks(client, processing_document):
    headers, document_id = processing_document
    response = client.post(f"/documents/{document_id}/process", headers=headers)
    assert response.status_code == 202, response.text
    assert response.json()["status"] == "queued"
    page = client.get(f"/documents/{document_id}/chunks?skip=1&limit=1", headers=headers).json()
    count = page["total"]
    assert count > 1
    assert page["total"] == count and page["status"] == "processed"
    assert page["items"][0]["chunk_index"] == 1
    assert page["items"][0]["char_count"] == len(page["items"][0]["content"])
    assert "file_path" not in response.text
    detail = client.get(f"/documents/{document_id}", headers=headers).json()
    assert detail["status"] == "processed" and detail["processing_error"] is None


def test_docx_process(client, docx_bytes):
    headers = headers_for(client, "docx@example.com")
    uploaded = client.post("/documents", headers=headers, files={"file": (
        "law.docx", docx_bytes, "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )}).json()
    response = client.post(f"/documents/{uploaded['id']}/process", headers=headers)
    assert response.status_code == 202, response.text


def test_pdf_process(client, pdf_bytes):
    headers = headers_for(client, "pdf@example.com")
    uploaded = client.post("/documents", headers=headers, files={"file": ("law.pdf", pdf_bytes, "application/pdf")}).json()
    assert client.post(f"/documents/{uploaded['id']}/process", headers=headers).status_code == 202
    chunks = client.get(f"/documents/{uploaded['id']}/chunks", headers=headers).json()["items"]
    assert "Article 1. Scope." in chunks[0]["content"]


@pytest.mark.parametrize("case", ["empty", "invalid_utf8", "missing"])
def test_processing_errors_are_persisted(client, processing_document, db_session, document_storage, case):
    headers, document_id = processing_document
    document = db_session.get(Document, UUID(document_id))
    path = document_storage / document.stored_filename
    if case == "missing":
        path.unlink()
    else:
        # Phase 3 rejects empty uploads; simulate a damaged stored file.
        path.write_bytes(b"" if case == "empty" else b"\xff")
    response = client.post(f"/documents/{document_id}/process", headers=headers)
    assert response.status_code == 202, response.text
    detail = client.get(f"/documents/{document_id}", headers=headers).json()
    assert detail["status"] == "failed" and detail["processing_error"]
    assert str(document_storage) not in response.text + detail["processing_error"]
    assert client.get(f"/documents/{document_id}/chunks", headers=headers).json()["total"] == 0


def test_pdf_without_text_fails(client, blank_pdf_bytes):
    headers = headers_for(client, "scan@example.com")
    uploaded = client.post("/documents", headers=headers, files={"file": ("scan.pdf", blank_pdf_bytes, "application/pdf")}).json()
    response = client.post(f"/documents/{uploaded['id']}/process", headers=headers)
    assert response.status_code == 202
    assert client.get(f"/documents/{uploaded['id']}", headers=headers).json()["status"] == "failed"


def test_reprocess_replaces_chunks(client, processing_document, monkeypatch):
    headers, document_id = processing_document
    path = f"/documents/{document_id}"
    assert client.post(path + "/process", headers=headers).status_code == 202
    first = client.get(path + "/chunks?limit=100", headers=headers).json()
    monkeypatch.setattr(get_settings(), "chunk_size", 400)
    monkeypatch.setattr(get_settings(), "chunk_overlap", 50)
    response = client.post(path + "/process", headers=headers)
    assert response.status_code == 202
    second = client.get(path + "/chunks?limit=100", headers=headers).json()
    assert second["total"] > first["total"]
    assert [item["chunk_index"] for item in second["items"]] == list(range(second["total"]))
    assert {item["id"] for item in first["items"]}.isdisjoint(item["id"] for item in second["items"])


def test_failed_reprocess_rolls_back_partial_replacement(client, processing_document, db_session, monkeypatch):
    headers, document_id = processing_document
    path = f"/documents/{document_id}"
    assert client.post(path + "/process", headers=headers).status_code == 202
    old = client.get(path + "/chunks?limit=100", headers=headers).json()["items"]
    real_add_all = db_session.add_all
    def fail_after_insert(objects):
        real_add_all(objects[:1])
        db_session.flush()
        raise SQLAlchemyError("private database diagnostic")
    monkeypatch.setattr(db_session, "add_all", fail_after_insert)
    response = client.post(path + "/process", headers=headers)
    assert response.status_code == 202 and "private" not in response.text
    current = client.get(path + "/chunks?limit=100", headers=headers).json()
    assert current["status"] == "failed" and current["items"] == old


def test_unexpected_error_is_sanitized_and_failed(client, processing_document, monkeypatch):
    headers, document_id = processing_document
    def fail(*args):
        raise RuntimeError("private path and document contents")
    monkeypatch.setattr(document_processing, "extract_text", fail)
    response = client.post(f"/documents/{document_id}/process", headers=headers)
    assert response.status_code == 202 and "private" not in response.text
    assert client.get(f"/documents/{document_id}", headers=headers).json()["processing_error"] == "Document processing failed"


def test_processing_claim_blocks_reprocess_and_delete(client, processing_document, db_session, monkeypatch):
    headers, document_id = processing_document
    document = db_session.get(Document, UUID(document_id))
    document.status = "processing"
    db_session.commit()
    path = f"/documents/{document_id}"
    assert client.post(path + "/process", headers=headers).status_code == 409
    assert client.delete(path, headers=headers).status_code == 409
    assert db_session.get(Document, UUID(document_id)).status == "processing"


def test_claim_is_set_before_extraction_and_failed_can_retry(client, processing_document, db_session, monkeypatch):
    headers, document_id = processing_document
    document = db_session.get(Document, UUID(document_id))
    document.status = "failed"
    document.processing_error = "Previous failure"
    db_session.commit()
    original = document_processing.extract_text
    def check_claim(*args):
        current = db_session.get(Document, UUID(document_id))
        assert current.status == "processing" and current.processing_error is None
        return original(*args)
    monkeypatch.setattr(document_processing, "extract_text", check_claim)
    assert client.post(f"/documents/{document_id}/process", headers=headers).status_code == 202
    assert db_session.get(Document, UUID(document_id)).processing_error is None


def test_chunks_cascade_on_document_deletion(client, processing_document, db_session):
    headers, document_id = processing_document
    path = f"/documents/{document_id}"
    assert client.post(path + "/process", headers=headers).status_code == 202
    assert client.delete(path, headers=headers).status_code == 204
    assert db_session.scalar(select(func.count()).select_from(DocumentChunk)) == 0


def test_owner_isolation_and_unauthenticated_requests(client, processing_document):
    headers, document_id = processing_document
    other = headers_for(client, "other-processor@example.com")
    for identity in [document_id, str(uuid4())]:
        assert client.post(f"/documents/{identity}/process", headers=other).status_code == 404
        assert client.get(f"/documents/{identity}/chunks", headers=other).status_code == 404
    assert client.post(f"/documents/{document_id}/process").status_code == 401
    assert client.get(f"/documents/{document_id}/chunks").status_code == 401
    assert client.get(f"/documents/{document_id}", headers=headers).json()["status"] == "uploaded"


@pytest.mark.parametrize("query", ["skip=-1", "limit=0", "limit=101"])
def test_chunk_pagination_validation(client, processing_document, query):
    headers, document_id = processing_document
    assert client.get(f"/documents/{document_id}/chunks?{query}", headers=headers).status_code == 422


def test_processing_openapi(client):
    spec = client.get("/openapi.json").json()
    for path, method in [("/documents/{document_id}/process", "post"), ("/documents/{document_id}/chunks", "get")]:
        assert spec["paths"][path][method]["security"] == [{"HTTPBearer": []}]
