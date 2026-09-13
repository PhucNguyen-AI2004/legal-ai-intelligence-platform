from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import CurrentUser, DbSession
from app.api.document_route import DocumentRoute
from app.core.config import get_settings
from app.models.document import Document
from app.schemas.document import DocumentList, DocumentRead
from app.schemas.document_chunk import DocumentChunkList, DocumentChunkRead, DocumentProcessResult
from app.services import documents
from app.services.document_storage import DocumentStorage
from app.services import document_processing
from app.services.text_extraction import ProcessingError
from app.services.embeddings import EmbeddingBackend, EmbeddingError, get_embedding_service
from app.services.document_indexing import index_document as run_index_document
from app.schemas.search import DocumentIndexResult

router = APIRouter(prefix="/documents", tags=["documents"], route_class=DocumentRoute)


def get_document_storage() -> DocumentStorage:
    return DocumentStorage(get_settings())


Storage = Annotated[DocumentStorage, Depends(get_document_storage)]


@router.post("", response_model=DocumentRead, status_code=201)
def upload_document(
    user: CurrentUser, db: DbSession, storage: Storage,
    file: Annotated[UploadFile, File()],
    title: Annotated[str | None, Form(max_length=255)] = None,
    description: Annotated[str | None, Form(max_length=5000)] = None,
) -> Document:
    try:
        return documents.upload_document(db, user.id, file, title, description, storage)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None
    except OSError:
        raise HTTPException(503, "Document storage operation failed") from None
    finally:
        file.file.close()


@router.post("/{document_id}/index", response_model=DocumentIndexResult)
def index_document(
    document_id: UUID, user: CurrentUser, db: DbSession,
    backend: Annotated[EmbeddingBackend, Depends(get_embedding_service)],
) -> DocumentIndexResult:
    try:
        count = run_index_document(document_id, user.id, db, backend)
        return DocumentIndexResult(document_id=document_id, embedded_chunks=count, model_name=backend.model_name)
    except EmbeddingError as exc:
        raise HTTPException(503, str(exc)) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Embedding database operation failed") from None


@router.get("", response_model=DocumentList)
def list_documents(
    user: CurrentUser, db: DbSession, response: Response,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentList:
    response.headers["Cache-Control"] = "no-store"
    try:
        items, total = documents.list_documents(db, user.id, skip, limit)
        return DocumentList(items=[DocumentRead.model_validate(item) for item in items], total=total, skip=skip, limit=limit)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None


@router.get("/{document_id}", response_model=DocumentRead)
def get_document(document_id: UUID, user: CurrentUser, db: DbSession, response: Response) -> Document:
    response.headers["Cache-Control"] = "no-store"
    try:
        return documents.get_document(db, document_id, user.id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None


@router.delete("/{document_id}", status_code=204)
def delete_document(document_id: UUID, user: CurrentUser, db: DbSession, storage: Storage) -> Response:
    try:
        documents.delete_document(db, document_id, user.id, storage)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None
    except OSError:
        db.rollback()
        raise HTTPException(503, "Document storage operation failed") from None
    return Response(status_code=204)


@router.post("/{document_id}/process", response_model=DocumentProcessResult)
def process_document(document_id: UUID, user: CurrentUser, db: DbSession, storage: Storage) -> DocumentProcessResult:
    try:
        count = document_processing.process_document(document_id, user.id, db, storage, get_settings())
        return DocumentProcessResult(document_id=document_id, chunk_count=count)
    except ProcessingError as exc:
        raise HTTPException(exc.status_code, exc.message) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None


@router.get("/{document_id}/chunks", response_model=DocumentChunkList)
def get_chunks(
    document_id: UUID, user: CurrentUser, db: DbSession, response: Response,
    skip: Annotated[int, Query(ge=0)] = 0,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
) -> DocumentChunkList:
    response.headers["Cache-Control"] = "no-store"
    try:
        status, chunks, total = document_processing.list_chunks(db, document_id, user.id, skip, limit)
        return DocumentChunkList(
            document_id=document_id, status=status,
            items=[DocumentChunkRead.model_validate(chunk) for chunk in chunks],
            total=total, skip=skip, limit=limit,
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Document database operation failed") from None
