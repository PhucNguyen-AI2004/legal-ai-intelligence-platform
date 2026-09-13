from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.chunk_embedding import ChunkEmbedding
from app.services.embeddings import EmbeddingError


def user_headers(client, email):
    password = "StrongPassword123!"
    assert client.post("/auth/register", json={"email": email, "password": password, "full_name": "Searcher"}).status_code == 201
    token = client.post("/auth/login", json={"email": email, "password": password}).json()["access_token"]
    return {"Authorization": "Bearer " + token}


@pytest.fixture
def search_owner(client):
    return user_headers(client, "search-owner@example.com")


def make_document(client, headers, text="access rights", process=True, index=False):
    response = client.post("/documents", headers=headers, files={"file": ("law.txt", text.encode(), "text/plain")})
    assert response.status_code == 201
    identity = response.json()["id"]
    if process:
        assert client.post(f"/documents/{identity}/process", headers=headers).status_code == 200
    if index:
        response = client.post(f"/documents/{identity}/index", headers=headers)
        assert response.status_code == 200, response.text
    return identity


def search(client, headers, **values):
    return client.post("/search", headers=headers, json={"query": "access rights", **values})


def test_index_processed_document_and_reindex(client, search_owner, db_session, fake_embeddings):
    identity = make_document(client, search_owner, "access rights\n\n"*150)
    first = client.post(f"/documents/{identity}/index", headers=search_owner)
    assert first.status_code == 200, first.text
    assert first.json()["embedding_status"] == "indexed"
    count = first.json()["embedded_chunks"]
    assert count > 1 and len(fake_embeddings.document_calls) == 1
    old_ids = set(db_session.scalars(select(ChunkEmbedding.id)).all())
    assert len(old_ids) == count
    assert client.post(f"/documents/{identity}/index", headers=search_owner).status_code == 200
    new_ids = set(db_session.scalars(select(ChunkEmbedding.id)).all())
    assert len(new_ids) == count and old_ids.isdisjoint(new_ids)
    document = client.get(f"/documents/{identity}", headers=search_owner).json()
    assert document["embedded_at"] and document["embedding_error"] is None


def test_reject_unprocessed_document(client, search_owner, fake_embeddings):
    identity = make_document(client, search_owner, process=False)
    assert client.post(f"/documents/{identity}/index", headers=search_owner).status_code == 409
    assert fake_embeddings.document_calls == []


def test_exact_top_k_and_document_filter(client, search_owner):
    access = make_document(client, search_owner, "access rights", index=True)
    mixed = make_document(client, search_owner, "mixed rights", index=True)
    tax = make_document(client, search_owner, "tax rules", index=True)
    response = search(client, search_owner, top_k=2)
    assert response.status_code == 200, response.text
    results = response.json()["results"]
    assert [item["document_id"] for item in results] == [access, mixed]
    assert [item["score"] for item in results] == pytest.approx([1.0,0.8], abs=1e-5)
    assert results[0]["content"] == "access rights"
    assert "embedding" not in results[0] and "file_path" not in results[0]
    filtered = search(client, search_owner, document_ids=[tax,tax]).json()["results"]
    assert len(filtered) == 1 and filtered[0]["document_id"] == tax


def test_owner_filter_and_all_requested_ids_must_be_owned(client, search_owner, fake_embeddings):
    other = user_headers(client, "other-searcher@example.com")
    foreign = make_document(client, other, "access rights", index=True)
    own = make_document(client, search_owner, "mixed rights", index=True)
    result = search(client, search_owner, top_k=20).json()["results"]
    assert [item["document_id"] for item in result] == [own]
    fake_embeddings.query_calls.clear()
    for ids in [[foreign],[own,foreign],[str(uuid4())]]:
        assert search(client, search_owner, document_ids=ids).status_code == 404
    assert fake_embeddings.query_calls == []
    assert client.post(f"/documents/{foreign}/index", headers=search_owner).status_code == 404


@pytest.mark.parametrize("state", ["pending","indexing","failed"])
def test_search_excludes_not_indexed_documents(client, search_owner, db_session, fake_embeddings, state):
    identity = make_document(client, search_owner, index=True)
    document = db_session.get(Document, UUID(identity))
    document.embedding_status = state
    db_session.commit()
    assert search(client, search_owner).json()["results"] == []
    assert fake_embeddings.query_calls == []


def test_search_excludes_wrong_model_space(client, search_owner, db_session):
    make_document(client, search_owner, index=True)
    vector = db_session.scalar(select(ChunkEmbedding))
    vector.model_name = "another-model"
    db_session.commit()
    assert search(client, search_owner).json()["results"] == []


def test_reprocess_invalidates_and_cascades_old_embeddings(client, search_owner, db_session):
    identity = make_document(client, search_owner, index=True)
    assert client.post(f"/documents/{identity}/process", headers=search_owner).status_code == 200
    document = client.get(f"/documents/{identity}", headers=search_owner).json()
    assert document["embedding_status"] == "pending" and document["embedded_at"] is None
    assert db_session.scalar(select(func.count()).select_from(ChunkEmbedding)) == 0
    assert search(client, search_owner).json()["results"] == []


def test_reindex_failure_preserves_previous_complete_set(client, search_owner, db_session, monkeypatch):
    identity = make_document(client, search_owner, "access rights\n\n"*150, index=True)
    original = set(db_session.scalars(select(ChunkEmbedding.id)).all())
    real_add_all = db_session.add_all
    def fail(objects):
        real_add_all(objects[:1]); db_session.flush()
        raise SQLAlchemyError("private SQL diagnostic")
    monkeypatch.setattr(db_session, "add_all", fail)
    response = client.post(f"/documents/{identity}/index", headers=search_owner)
    assert response.status_code == 503 and "private" not in response.text
    assert set(db_session.scalars(select(ChunkEmbedding.id)).all()) == original
    assert client.get(f"/documents/{identity}", headers=search_owner).json()["embedding_status"] == "failed"
    assert search(client, search_owner).json()["results"] == []


def test_model_failure_sets_failed_and_retry_works(client, search_owner, fake_embeddings, monkeypatch):
    identity = make_document(client, search_owner)
    with monkeypatch.context() as context:
        def fail(texts):
            raise RuntimeError("private token and path")
        context.setattr(fake_embeddings, "embed_documents", fail)
        response = client.post(f"/documents/{identity}/index", headers=search_owner)
        assert response.status_code == 503 and "private" not in response.text
    assert client.get(f"/documents/{identity}", headers=search_owner).json()["embedding_status"] == "failed"
    assert client.post(f"/documents/{identity}/index", headers=search_owner).status_code == 200


def test_indexing_blocks_index_process_and_delete(client, search_owner, db_session):
    identity = make_document(client, search_owner)
    document = db_session.get(Document, UUID(identity))
    document.embedding_status = "indexing"
    db_session.commit()
    for suffix in ["index","process"]:
        assert client.post(f"/documents/{identity}/{suffix}", headers=search_owner).status_code == 409
    assert client.delete(f"/documents/{identity}", headers=search_owner).status_code == 409


def test_cascade_delete_embeddings(client, search_owner, db_session):
    identity = make_document(client, search_owner, index=True)
    assert client.delete(f"/documents/{identity}", headers=search_owner).status_code == 204
    assert db_session.scalar(select(func.count()).select_from(DocumentChunk)) == 0
    assert db_session.scalar(select(func.count()).select_from(ChunkEmbedding)) == 0


@pytest.mark.parametrize("values", [
    {"query":""}, {"query":"   "}, {"query":"a"*1001},
    {"top_k":0}, {"top_k":21}, {"document_ids":[]}, {"document_ids":["invalid"]},
])
def test_search_request_validation(client, search_owner, values):
    assert search(client, search_owner, **values).status_code == 422


def test_no_auth_and_empty_library(client, search_owner, fake_embeddings):
    assert client.post(f"/documents/{uuid4()}/index").status_code == 401
    assert search(client, {}).status_code == 401
    assert search(client, search_owner).json()["results"] == []
    assert not fake_embeddings.query_calls


def test_search_model_error_is_safe(client, search_owner, fake_embeddings, monkeypatch):
    make_document(client, search_owner, index=True)
    def fail(query):
        raise EmbeddingError("Embedding inference failed")
    monkeypatch.setattr(fake_embeddings, "embed_query", fail)
    response = search(client, search_owner)
    assert response.status_code == 503


def test_swagger_security_contract(client):
    spec = client.get("/openapi.json").json()
    assert spec["paths"]["/search"]["post"]["security"] == [{"HTTPBearer":[]}]
    assert spec["paths"]["/documents/{document_id}/index"]["post"]["security"] == [{"HTTPBearer":[]}]
