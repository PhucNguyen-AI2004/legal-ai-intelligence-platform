import logging
from pathlib import Path
from uuid import UUID, uuid4

from fastapi import HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models.document import Document
from app.services.document_storage import DocumentStorage

logger = logging.getLogger(__name__)


def upload_document(
    db: Session, owner_id: UUID, upload: UploadFile, title: str | None,
    description: str | None, storage: DocumentStorage,
) -> Document:
    stored = storage.save(upload)
    document = Document(
        id=uuid4(), owner_id=owner_id,
        original_filename=stored.original_filename,
        stored_filename=stored.stored_filename, file_path=stored.stored_filename,
        file_type=stored.file_type, mime_type=stored.mime_type, file_size=stored.file_size,
        title=(title or "").strip() or Path(stored.original_filename).stem.strip() or "Untitled document",
        description=(description or "").strip() or None,
    )
    try:
        db.add(document)
        # Load database defaults before commit; avoid a fallible refresh after commit.
        db.flush()
        db.refresh(document)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        try:
            storage.remove(stored.stored_filename)
        except OSError:
            logger.error("Failed to clean upload for document %s", document.id)
        raise
    return document


def list_documents(db: Session, owner_id: UUID, skip: int, limit: int) -> tuple[list[Document], int]:
    condition = Document.owner_id == owner_id
    total = db.scalar(select(func.count()).select_from(Document).where(condition)) or 0
    documents = db.scalars(
        select(Document).where(condition)
        .order_by(Document.created_at.desc(), Document.id.desc()).offset(skip).limit(limit)
    ).all()
    return list(documents), total


def get_document(db: Session, document_id: UUID, owner_id: UUID, *, lock: bool = False) -> Document:
    query = select(Document).where(Document.id == document_id, Document.owner_id == owner_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    document = db.scalar(query)
    if document is None:
        raise HTTPException(404, "Document not found")
    return document


def delete_document(db: Session, document_id: UUID, owner_id: UUID, storage: DocumentStorage) -> None:
    document = get_document(db, document_id, owner_id, lock=True)
    if document.status == "processing":
        raise HTTPException(409, "Cannot delete a document while it is processing")
    if document.embedding_status == "indexing":
        raise HTTPException(409, "Cannot delete a document while it is indexing")
    key = document.stored_filename
    staged_key = storage.stage_delete(key)
    try:
        db.delete(document)
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        if staged_key is not None:
            try:
                storage.restore(staged_key, key)
            except OSError:
                logger.error("Failed to restore file for document %s", document_id)
        raise
    if staged_key is not None:
        try:
            storage.remove(staged_key)
        except OSError:
            # Metadata is already committed. Report failure rather than pretending
            # the requested physical deletion completed; retain the file for cleanup.
            logger.error("File cleanup pending for document %s", document_id)
            raise HTTPException(503, "Metadata deleted; file cleanup pending") from None
