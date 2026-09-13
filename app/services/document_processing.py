import logging
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import delete, func, select, update
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.core.config import Settings
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.document_storage import DocumentStorage
from app.services.documents import get_document
from app.services.text_chunking import chunk_text
from app.services.text_extraction import ProcessingError, extract_text
from app.services.text_normalization import normalize_text

logger = logging.getLogger(__name__)


def process_document(
    document_id: UUID, owner_id: UUID, db: Session,
    storage: DocumentStorage, settings: Settings,
) -> int:
    # Claim under a row lock, then commit so other requests see processing.
    document = get_document(db, document_id, owner_id, lock=True)
    if document.status == "processing":
        raise HTTPException(409, "Document is already processing")
    if document.embedding_status == "indexing":
        raise HTTPException(409, "Cannot process a document while it is indexing")
    key, file_type = document.stored_filename, document.file_type
    document.status = "processing"
    document.processing_error = None
    # Hide old vectors immediately; successful chunk replacement cascades their deletion.
    document.embedding_status = "pending"
    document.embedding_error = None
    document.embedded_at = None
    db.commit()

    try:
        text = normalize_text(extract_text(storage.path_for(key), file_type))
        if not text:
            raise ProcessingError("Document contains no usable text")
        chunks = chunk_text(text, settings.chunk_size, settings.chunk_overlap)
        if not chunks:
            raise ProcessingError("Document contains no usable text")
        document = get_document(db, document_id, owner_id, lock=True)
        # One transaction replaces the complete set and publishes processed.
        db.execute(delete(DocumentChunk).where(DocumentChunk.document_id == document_id))
        db.add_all([
            DocumentChunk(
                document_id=document_id, chunk_index=chunk.chunk_index,
                content=chunk.content, char_count=chunk.char_count,
                token_estimate=chunk.token_estimate,
            )
            for chunk in chunks
        ])
        document.status = "processed"
        document.processing_error = None
        document.embedding_status = "pending"
        db.commit()
        return len(chunks)
    except Exception as exc:
        db.rollback()
        if isinstance(exc, ProcessingError):
            failure = exc
        elif isinstance(exc, OSError):
            failure = ProcessingError("Stored file cannot be accessed safely", 503)
        elif isinstance(exc, SQLAlchemyError):
            failure = ProcessingError("Document database operation failed", 503)
        else:
            failure = ProcessingError("Document processing failed", 500)
        # Do not log parser exception text: it may include private document data.
        logger.error("Processing failed for document %s (%s)", document_id, type(exc).__name__)
        db.execute(
            update(Document).where(Document.id == document_id, Document.owner_id == owner_id)
            .values(status="failed", processing_error=failure.message)
        )
        db.commit()
        raise failure from None


def list_chunks(
    db: Session, document_id: UUID, owner_id: UUID, skip: int, limit: int,
) -> tuple[str, list[DocumentChunk], int]:
    document = get_document(db, document_id, owner_id)
    condition = DocumentChunk.document_id == document_id
    total = db.scalar(select(func.count()).select_from(DocumentChunk).where(condition)) or 0
    chunks = db.scalars(
        select(DocumentChunk).where(condition)
        .order_by(DocumentChunk.chunk_index).offset(skip).limit(limit)
    ).all()
    return document.status, list(chunks), total
