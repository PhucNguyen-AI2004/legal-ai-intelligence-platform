import pytest

from app.main import app
from app.services.llm import LLMError, get_llm_provider
from test_semantic_search import make_document, user_headers


@pytest.fixture
def rag_owner(client):
    return user_headers(client, "rag-owner@example.com")


@pytest.fixture
def fake_llm(client):
    class FakeLLMProvider:
        answer = "Users have access rights [1]."
        error = None
        def __init__(self):
            self.calls = []
        def generate_answer(self, **kwargs):
            self.calls.append(kwargs)
            if self.error:
                raise self.error
            return self.answer
    provider = FakeLLMProvider()
    app.dependency_overrides[get_llm_provider] = lambda: provider
    yield provider
    app.dependency_overrides.pop(get_llm_provider, None)


def ask(client, headers, **values):
    return client.post("/rag/ask", headers=headers, json={"question": "access rights", **values})


def test_relevant_context_mapping_and_retrieval_reuse(client, rag_owner, fake_llm):
    identity = make_document(client, rag_owner, "access rights", index=True)
    result = ask(client, rag_owner).json()
    assert result["grounded"] is True
    assert result["retrieved_chunks"] == result["used_chunks"] == 1
    assert result["citations"][0]["document_id"] == identity
    assert result["citations"][0]["citation_number"] == 1
    assert len(fake_llm.calls) == 1
    assert "access rights" in fake_llm.calls[0]["context"]
    assert "file_path" not in str(result) and "system_prompt" not in result
    assert client.post("/search", headers=rag_owner, json={"query":"access rights"}).status_code == 200


def test_owner_and_document_filters(client, rag_owner, fake_llm):
    other = user_headers(client, "rag-other@example.com")
    foreign = make_document(client, other, "access SECRET_OTHER_DOC", index=True)
    assert ask(client, rag_owner).json()["citations"] == []
    assert not fake_llm.calls
    assert ask(client, rag_owner, document_ids=[foreign]).status_code == 404
    mine = make_document(client, rag_owner, "access mine", index=True)
    response = ask(client, rag_owner, document_ids=[mine, mine])
    assert response.status_code == 200
    assert "SECRET_OTHER_DOC" not in response.text
    assert "SECRET_OTHER_DOC" not in fake_llm.calls[-1]["context"]


@pytest.mark.parametrize("indexed,text", [(False,"access"), (True,"tax rules")])
def test_no_context_no_generation(client, rag_owner, fake_llm, indexed, text):
    make_document(client, rag_owner, text, index=indexed)
    result = ask(client, rag_owner).json()
    assert result["grounded"] is False and result["citations"] == []
    assert result["used_chunks"] == 0 and not fake_llm.calls


@pytest.mark.parametrize("answer", ["Invented law [99].", "Mixed claim [1] [0].", "Claim [999999999999999999999999].", "Claim [1] [1, 99]."])
def test_invalid_references_fail_closed(client, rag_owner, fake_llm, answer):
    make_document(client, rag_owner, index=True)
    fake_llm.answer = answer
    result = ask(client, rag_owner).json()
    assert not result["grounded"] and result["citations"] == []
    assert answer != result["answer"]


@pytest.mark.parametrize("answer", ["There is insufficient information.", "Unsupported assertion."])
def test_no_citation_is_not_grounded(client, rag_owner, fake_llm, answer):
    make_document(client, rag_owner, index=True)
    fake_llm.answer = answer
    result = ask(client, rag_owner).json()
    assert not result["grounded"] and result["citations"] == []


def test_timeout_and_empty_answer(client, rag_owner, fake_llm):
    make_document(client, rag_owner, index=True)
    fake_llm.error = LLMError("LLM provider timed out")
    assert ask(client, rag_owner).status_code == 503
    fake_llm.error = None
    fake_llm.answer = " "
    assert ask(client, rag_owner).status_code == 503


def test_missing_configuration_with_context(client, rag_owner):
    make_document(client, rag_owner, index=True)
    response = ask(client, rag_owner)
    assert response.status_code == 503 and "configuration" in response.json()["detail"]
    assert client.get("/health").status_code == 200


@pytest.mark.parametrize("values", [{"question":"  "}, {"question":"x"*1001}, {"top_k":0}, {"top_k":11}, {"document_ids":[]}])
def test_rag_validation(client, rag_owner, fake_llm, values):
    assert ask(client, rag_owner, **values).status_code == 422
    assert not fake_llm.calls


def test_auth_and_openapi(client):
    assert ask(client, {}).status_code == 401
    assert "/rag/ask" in client.get("/openapi.json").json()["paths"]
