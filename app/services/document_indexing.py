import logging
from datetime import datetime, timezone
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.embedding_config import VECTOR_DIMENSION
from app.models.chunk_embedding import ChunkEmbedding
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.documents import get_document
from app.services.embeddings import EmbeddingBackend, EmbeddingError, validate_vectors

logger = logging.getLogger("uvicorn.error")


def index_document(document_id: UUID, owner_id: UUID, db: Session, backend: EmbeddingBackend) -> int:
    document = get_document(db, document_id, owner_id, lock=True)
    if document.status != "processed":
        raise HTTPException(409, "Document must be processed before indexing")
    if document.embedding_status == "indexing":
        raise HTTPException(409, "Document is already indexing")
    chunks = db.execute(
        select(DocumentChunk.id, DocumentChunk.content)
        .where(DocumentChunk.document_id == document_id).order_by(DocumentChunk.chunk_index)
    ).all()
    if not chunks:
        raise HTTPException(409, "Document has no chunks to index")
    document.embedding_status = "indexing"
    document.embedding_error = None
    db.commit()
    logger.info("Document indexing started: document_id=%s chunks=%s", document_id, len(chunks))

    try:
        vectors = validate_vectors(
            backend.embed_documents([chunk.content for chunk in chunks]), len(chunks), VECTOR_DIMENSION
        )
        document = get_document(db, document_id, owner_id, lock=True)
        db.execute(delete(ChunkEmbedding).where(ChunkEmbedding.chunk_id.in_(
            select(DocumentChunk.id).where(DocumentChunk.document_id == document_id)
        )))
        db.add_all([
            ChunkEmbedding(chunk_id=chunk.id, embedding=vector, model_name=backend.model_name)
            for chunk, vector in zip(chunks, vectors, strict=True)
        ])
        document.embedding_status = "indexed"
        document.embedding_error = None
        document.embedded_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Document indexing completed: document_id=%s indexed_chunks=%s", document_id, len(chunks))
        return len(chunks)
    except Exception as exc:
        db.rollback()
        if isinstance(exc, EmbeddingError):
            message = str(exc)
        elif isinstance(exc, SQLAlchemyError):
            message = "Embedding database operation failed"
        else:
            message = "Document indexing failed"
        logger.error("Document indexing failed: document_id=%s error_type=%s", document_id, type(exc).__name__)
        db.execute(update(Document).where(Document.id == document_id, Document.owner_id == owner_id)
                   .values(embedding_status="failed", embedding_error=message))
        db.commit()
        raise EmbeddingError(message) from None
