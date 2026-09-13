from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.embedding_config import VECTOR_DIMENSION
from app.models.chunk_embedding import ChunkEmbedding
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.schemas.search import SearchRequest, SearchResult
from app.services.embeddings import EmbeddingBackend, validate_vectors


def search_documents(db: Session, owner_id: UUID, request: SearchRequest, backend: EmbeddingBackend) -> list[SearchResult]:
    if request.document_ids is not None:
        owned = set(db.scalars(select(Document.id).where(
            Document.id.in_(request.document_ids), Document.owner_id == owner_id
        )).all())
        if owned != set(request.document_ids):
            raise HTTPException(404, "One or more documents were not found")

    filters = [
        Document.owner_id == owner_id, Document.status == "processed",
        Document.embedding_status == "indexed", ChunkEmbedding.model_name == backend.model_name,
    ]
    if request.document_ids is not None:
        filters.append(Document.id.in_(request.document_ids))
    candidates = (
        select(ChunkEmbedding.id).join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.id)
        .join(Document, DocumentChunk.document_id == Document.id).where(*filters)
    )
    # Empty libraries do not need to download/load the model.
    if db.scalar(candidates.limit(1)) is None:
        return []
    query_vector = validate_vectors([backend.embed_query(request.query)], 1, VECTOR_DIMENSION)[0]
    distance = ChunkEmbedding.embedding.cosine_distance(query_vector)
    statement = (
        select(
            Document.id.label("document_id"), Document.title.label("document_title"),
            DocumentChunk.id.label("chunk_id"), DocumentChunk.chunk_index,
            DocumentChunk.content, (1 - distance).label("score"),
        )
        .select_from(ChunkEmbedding).join(DocumentChunk, ChunkEmbedding.chunk_id == DocumentChunk.id)
        .join(Document, DocumentChunk.document_id == Document.id).where(*filters)
        .order_by(distance, Document.id, DocumentChunk.chunk_index).limit(request.top_k)
    )
    return [
        SearchResult(**{**row, "score": max(-1.0, min(1.0, float(row["score"])))})
        for row in db.execute(statement).mappings()
    ]
