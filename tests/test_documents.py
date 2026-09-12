from io import BytesIO
from uuid import UUID, uuid4
from zipfile import ZipFile

import pytest
from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from starlette.datastructures import Headers

from app.core.config import get_settings
from app.models.document import Document
from app.services.document_storage import DocumentStorage

PDF = b"%PDF-1.7\nSmall fixture; no deep parsing in Phase 3.\n%%EOF"


def account_headers(client, email):
    password = "StrongPassword123!"
    assert client.post("/auth/register", json={"email": email, "password": password, "full_name": "Test Owner"}).status_code == 201
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return {"Authorization": "Bearer " + response.json()["access_token"]}


@pytest.fixture
def auth_headers(client):
    return account_headers(client, "owner@example.com")


def upload(client, headers, filename="law.txt", content=b"Legal text", mime="text/plain", **fields):
    return client.post("/documents", headers=headers, files={"file": (filename, content, mime)}, data=fields)


def test_upload_txt_metadata_and_private_file(client, auth_headers, db_session, document_storage):
    content = "Văn bản pháp luật".encode()
    response = upload(client, auth_headers, content=content, title="  Luật mẫu  ", description="  Ghi chú  ")
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["title"] == "Luật mẫu" and data["description"] == "Ghi chú"
    assert data["status"] == "uploaded"
    assert data["file_size"] == len(content)
    assert data["file_type"] == "txt" and data["mime_type"] == "text/plain"
    assert "file_path" not in data and "stored_filename" not in data
    document = db_session.get(Document, UUID(data["id"]))
    assert document.owner.email == "owner@example.com"
    assert document.stored_filename != document.original_filename
    assert document.file_path == document.stored_filename
    assert (document_storage / document.stored_filename).read_bytes() == content
    assert client.get("/documents/" + data["id"], headers=auth_headers).json() == data


def test_pdf_default_title_and_repeated_filename(client, auth_headers, document_storage):
    first = upload(client, auth_headers, "law.PDF", PDF, "application/pdf")
    second = upload(client, auth_headers, "law.PDF", PDF, "application/octet-stream")
    assert first.status_code == second.status_code == 201
    assert first.json()["title"] == "law"
    assert first.json()["description"] is None
    assert first.json()["id"] != second.json()["id"]
    assert len(list(document_storage.glob("*.pdf"))) == 2


def test_docx_container(client, auth_headers):
    content = BytesIO()
    with ZipFile(content, "w") as archive:
        archive.writestr("[Content_Types].xml", "<Types/>")
        archive.writestr("word/document.xml", "<document/>")
    response = upload(client, auth_headers, "law.docx", content.getvalue(), "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    assert response.status_code == 201, response.text
    assert response.json()["file_type"] == "docx"


@pytest.mark.parametrize("filename,content,mime,status", [
    ("payload.exe", b"binary", "application/octet-stream", 415),
    ("fake.pdf", b"not a PDF", "application/pdf", 415),
    ("fake.docx", b"not a ZIP", "application/vnd.openxmlformats-officedocument.wordprocessingml.document", 415),
    ("wrong.txt", b"text", "application/pdf", 415),
    ("binary.txt", b"\x00\xff", "text/plain", 415),
    ("empty.txt", b"", "text/plain", 400),
    ("../escape.txt", b"text", "text/plain", 400),
    ("/tmp/escape.txt", b"text", "text/plain", 400),
])
def test_invalid_upload_leaves_no_file_or_metadata(client, auth_headers, document_storage, db_session, filename, content, mime, status):
    response = upload(client, auth_headers, filename, content, mime)
    assert response.status_code == status, response.text
    assert not list(document_storage.glob("*"))
    assert db_session.scalar(select(func.count()).select_from(Document)) == 0


def test_upload_file_size_limit(client, auth_headers, document_storage):
    response = upload(client, auth_headers, content=b"a" * (1024 * 1024 + 1))
    assert response.status_code == 413
    assert not list(document_storage.glob("*"))


def test_exact_size_limit_is_accepted(client, auth_headers):
    assert upload(client, auth_headers, content=b"a" * (1024 * 1024)).status_code == 201


def test_request_stream_limit_without_content_length(client, auth_headers, document_storage):
    def chunks():
        yield b'--boundary\r\nContent-Disposition: form-data; name="file"; filename="large.txt"\r\nContent-Type: text/plain\r\n\r\n'
        for _ in range(18):
            yield b"a" * (64 * 1024)
        yield b"\r\n--boundary--\r\n"

    response = client.post("/documents", headers={**auth_headers, "Content-Type": "multipart/form-data; boundary=boundary"}, content=chunks())
    assert response.status_code == 413, response.text
    assert not list(document_storage.glob("*"))


def test_list_pagination_and_cross_owner_access(client, auth_headers):
    other_headers = account_headers(client, "other@example.com")
    other = upload(client, other_headers).json()
    first = upload(client, auth_headers).json()
    second = upload(client, auth_headers).json()
    response = client.get("/documents?skip=0&limit=1", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["total"] == 2
    assert len(response.json()["items"]) == 1
    page_two = client.get("/documents?skip=1&limit=1", headers=auth_headers).json()
    ids = {response.json()["items"][0]["id"], page_two["items"][0]["id"]}
    assert ids == {first["id"], second["id"]}
    for method in [client.get, client.delete]:
        assert method("/documents/" + other["id"], headers=auth_headers).status_code == 404
    assert client.get("/documents/" + other["id"], headers=other_headers).status_code == 200
    assert client.get("/documents?skip=100", headers=auth_headers).json()["items"] == []


@pytest.mark.parametrize("query", ["skip=-1", "limit=0", "limit=101"])
def test_invalid_pagination(client, auth_headers, query):
    assert client.get("/documents?" + query, headers=auth_headers).status_code == 422


@pytest.mark.parametrize("missing_file", [False, True])
def test_delete_metadata_and_file(client, auth_headers, db_session, document_storage, missing_file):
    response = upload(client, auth_headers)
    document_id = response.json()["id"]
    document = db_session.get(Document, UUID(document_id))
    if missing_file:
        (document_storage / document.stored_filename).unlink()
    response = client.delete("/documents/" + document_id, headers=auth_headers)
    assert response.status_code == 204 and response.content == b""
    assert db_session.get(Document, UUID(document_id)) is None
    assert not list(document_storage.glob("*"))
    assert client.get("/documents/" + document_id, headers=auth_headers).status_code == 404
    assert client.delete("/documents/" + document_id, headers=auth_headers).status_code == 404


def test_all_document_routes_require_auth(client):
    path = "/documents/" + str(uuid4())
    for response in [upload(client, {}), client.get("/documents"), client.get(path), client.delete(path)]:
        assert response.status_code == 401
        assert response.headers["www-authenticate"] == "Bearer"


def test_upload_database_failure_removes_file(client, auth_headers, db_session, document_storage, monkeypatch):
    def fail():
        raise SQLAlchemyError("private database diagnostic")
    monkeypatch.setattr(db_session, "commit", fail)
    response = upload(client, auth_headers)
    assert response.status_code == 503
    assert "private" not in response.text
    assert not list(document_storage.glob("*"))
    assert db_session.scalar(select(func.count()).select_from(Document)) == 0


def test_delete_database_failure_restores_file(client, auth_headers, db_session, document_storage, monkeypatch):
    document_id = upload(client, auth_headers).json()["id"]
    document = db_session.get(Document, UUID(document_id))
    path = document_storage / document.stored_filename
    def fail():
        raise SQLAlchemyError("private diagnostic")
    monkeypatch.setattr(db_session, "commit", fail)
    response = client.delete("/documents/" + document_id, headers=auth_headers)
    assert response.status_code == 503
    assert path.read_bytes() == b"Legal text"
    assert not list(document_storage.glob("*.deleting"))
    assert db_session.get(Document, UUID(document_id)) is not None


def test_storage_permission_error_preserves_document(client, auth_headers, db_session, monkeypatch):
    document_id = upload(client, auth_headers).json()["id"]
    def fail(*args):
        raise PermissionError("private path")
    monkeypatch.setattr(DocumentStorage, "stage_delete", fail)
    response = client.delete("/documents/" + document_id, headers=auth_headers)
    assert response.status_code == 503 and "private path" not in response.text
    assert db_session.get(Document, UUID(document_id)) is not None


def test_storage_key_cannot_escape_root(document_storage):
    storage = DocumentStorage(get_settings())
    for key in ["../outside.txt", "/tmp/outside.txt", "C:\\outside.txt", "not-a-uuid.txt"]:
        with pytest.raises(OSError):
            storage.path_for(key)


def test_storage_rejects_windows_filename(document_storage):
    storage = DocumentStorage(get_settings())
    file = UploadFile(BytesIO(b"text"), filename="..\\outside.txt", headers=Headers({"content-type": "text/plain"}))
    with pytest.raises(HTTPException) as error:
        storage.save(file)
    assert error.value.status_code == 400


def test_storage_rejects_symlink(document_storage, tmp_path):
    document_storage.mkdir()
    outside = tmp_path / "outside.txt"
    outside.write_text("keep this file")
    key = uuid4().hex + ".txt"
    try:
        (document_storage / key).symlink_to(outside)
    except OSError:
        pytest.skip("Symlink creation requires privileges on this platform")
    with pytest.raises(OSError):
        DocumentStorage(get_settings()).remove(key)
    assert outside.read_text() == "keep this file"


def test_final_file_cleanup_failure_is_reported(client, auth_headers, db_session, document_storage, monkeypatch):
    document_id = upload(client, auth_headers).json()["id"]
    def fail(*args):
        raise PermissionError("private path")
    monkeypatch.setattr(DocumentStorage, "remove", fail)
    response = client.delete("/documents/" + document_id, headers=auth_headers)
    assert response.status_code == 503
    assert response.json()["detail"] == "Metadata deleted; file cleanup pending"
    assert db_session.get(Document, UUID(document_id)) is None
    assert len(list(document_storage.glob("*.deleting"))) == 1


def test_copy_limit_does_not_trust_upload_size(document_storage):
    storage = DocumentStorage(get_settings())
    file = UploadFile(BytesIO(b"a" * (storage.max_size + 1)), filename="large.txt", size=1, headers=Headers({"content-type": "text/plain"}))
    with pytest.raises(HTTPException) as error:
        storage.save(file)
    assert error.value.status_code == 413
    assert not list(document_storage.glob("*"))


def test_swagger_multipart_and_private_schema(client):
    spec = client.get("/openapi.json").json()
    operation = spec["paths"]["/documents"]["post"]
    assert "multipart/form-data" in operation["requestBody"]["content"]
    assert operation["security"] == [{"HTTPBearer": []}]
    fields = spec["components"]["schemas"]["DocumentRead"]["properties"]
    assert "file_path" not in fields and "stored_filename" not in fields
    assert client.get("/storage/documents/example.txt").status_code == 404
