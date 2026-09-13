from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from app.core.config import Settings, get_settings
from app.core.embedding_config import VECTOR_DIMENSION
from app.services import embeddings
from app.services.embeddings import EmbeddingError, EmbeddingService, validate_vectors


def test_service_loads_once_and_batches_prefixes(monkeypatch):
    service = EmbeddingService(get_settings())
    calls = []
    loaded = []
    class FakeModel:
        def get_sentence_embedding_dimension(self):
            return VECTOR_DIMENSION
        def encode(self, texts, **kwargs):
            calls.append((texts, kwargs))
            return [[1.0] + [0.0] * (VECTOR_DIMENSION-1) for _ in texts]
    def build():
        loaded.append(True)
        return FakeModel()
    monkeypatch.setattr(service, "_build_model", build)
    assert not loaded
    vectors = service.embed_documents(["Nội dung một", "Content two"])
    query = service.embed_query("Quyền truy cập?")
    assert len(loaded) == 1 and len(vectors) == 2 and len(query) == VECTOR_DIMENSION
    assert calls[0][0] == ["passage: Nội dung một", "passage: Content two"]
    assert calls[1][0] == ["query: Quyền truy cập?"]
    assert calls[0][1]["batch_size"] == get_settings().embedding_batch_size
    assert calls[0][1]["normalize_embeddings"] is True


def test_singleton_is_shared_without_loading_model(monkeypatch):
    monkeypatch.setattr(embeddings, "_service", None)
    with ThreadPoolExecutor(max_workers=8) as pool:
        services = list(pool.map(lambda _: embeddings.get_embedding_service(), range(20)))
    assert len({id(service) for service in services}) == 1
    assert services[0]._model is None


def test_model_dimension_is_checked_at_load(monkeypatch):
    service = EmbeddingService(get_settings())
    class WrongModel:
        def get_sentence_embedding_dimension(self):
            return VECTOR_DIMENSION + 1
    monkeypatch.setattr(service, "_build_model", lambda: WrongModel())
    with pytest.raises(EmbeddingError, match="dimension"):
        service.load_model()
    assert service._model is None


@pytest.mark.parametrize("vectors,count", [([],1), ([[0.0]*VECTOR_DIMENSION],1), ([[float('nan')]*VECTOR_DIMENSION],1), ([[1.0]],1)])
def test_invalid_vector_output_rejected(vectors, count):
    with pytest.raises(EmbeddingError):
        validate_vectors(vectors, count, VECTOR_DIMENSION)


def test_empty_input_does_not_load_model():
    service = EmbeddingService(get_settings())
    assert service.embed_documents([]) == []
    with pytest.raises(EmbeddingError):
        service.embed_query("   ")


@pytest.mark.parametrize("values", [
    {"embedding_dimension": VECTOR_DIMENSION + 1}, {"embedding_batch_size": 0},
    {"embedding_model_name": "an-unconfigured-model"},
])
def test_embedding_settings_match_schema(values):
    with pytest.raises(ValidationError):
        Settings(**values)
