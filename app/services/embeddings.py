"""Lazy CPU embedding model with an injectable backend for offline tests."""
import logging
import math
from threading import Lock, RLock
from typing import Protocol

from app.core.config import Settings, get_settings

logger = logging.getLogger("uvicorn.error")


class EmbeddingError(Exception):
    """Contains only a safe, client-visible diagnostic."""


class EmbeddingBackend(Protocol):
    model_name: str
    dimension: int

    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, query: str) -> list[float]: ...


def validate_vectors(vectors, expected_count: int, dimension: int) -> list[list[float]]:
    try:
        result = [[float(value) for value in vector] for vector in vectors]
        if len(result) != expected_count:
            raise ValueError
        for vector in result:
            if len(vector) != dimension or not all(math.isfinite(value) for value in vector):
                raise ValueError
            norm = math.sqrt(sum(value * value for value in vector))
            if not math.isfinite(norm) or norm <= 0:
                raise ValueError
        return result
    except (TypeError, ValueError, OverflowError):
        raise EmbeddingError("Embedding output has invalid size or numeric values") from None


class EmbeddingService:
    def __init__(self, settings: Settings):
        self.model_name = settings.embedding_model_name
        self.dimension = settings.embedding_dimension
        self.batch_size = settings.embedding_batch_size
        self.cache_directory = settings.model_cache_directory
        self._model = None
        # One load at a time; serialize encode calls to bound CPU/RAM concurrency.
        self._lock = RLock()

    def _build_model(self):
        from sentence_transformers import SentenceTransformer

        self.cache_directory.mkdir(parents=True, exist_ok=True)
        return SentenceTransformer(
            self.model_name, device="cpu", cache_folder=str(self.cache_directory),
            trust_remote_code=False, token=False,
        )

    def load_model(self):
        with self._lock:
            if self._model is None:
                try:
                    model = self._build_model()
                    if model.get_sentence_embedding_dimension() != self.dimension:
                        raise EmbeddingError("Loaded model dimension does not match the vector schema")
                    self._model = model
                    logger.info("Embedding model loaded: model=%s dimension=%s device=cpu", self.model_name, self.dimension)
                except EmbeddingError:
                    raise
                except Exception:
                    raise EmbeddingError("Embedding model could not be loaded; check dependencies, network and cache") from None
            return self._model

    def _encode(self, texts: list[str]) -> list[list[float]]:
        with self._lock:
            model = self.load_model()
            try:
                vectors = model.encode(
                    texts, batch_size=self.batch_size, normalize_embeddings=True,
                    convert_to_numpy=True, show_progress_bar=False,
                )
                return validate_vectors(vectors, len(texts), self.dimension)
            except EmbeddingError:
                raise
            except Exception:
                raise EmbeddingError("Embedding inference failed") from None

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if any(not text.strip() for text in texts):
            raise EmbeddingError("Cannot embed an empty chunk")
        return self._encode(["passage: " + text for text in texts])

    def embed_query(self, query: str) -> list[float]:
        if not query.strip():
            raise EmbeddingError("Cannot embed an empty query")
        return self._encode(["query: " + query])[0]


_service: EmbeddingService | None = None
_service_lock = Lock()


def get_embedding_service() -> EmbeddingBackend:
    global _service
    with _service_lock:
        if _service is None:
            _service = EmbeddingService(get_settings())
        return _service
