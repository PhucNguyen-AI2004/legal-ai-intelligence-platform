from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, Response, UploadFile
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import CurrentUser, DbSession
from app.api.document_route import DocumentRoute
from app.core.config import get_settings
from app.models.document import Document
from app.schemas.document import DocumentList, DocumentRead
from app.services import documents
from app.services.document_storage import DocumentStorage

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
