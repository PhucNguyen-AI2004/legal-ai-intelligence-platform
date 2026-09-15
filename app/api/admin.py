from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError

from app.api.dependencies import DbSession, require_admin
from app.models.user import User
from app.models.document import Document
from app.models.conversation import Conversation
from app.models.message import Message
from app.schemas.admin import AdminOverview, AdminUsers, AdminUser, AdminDocuments, AdminDocument, ProcessingState, EmbeddingState

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
Limit = Annotated[int, Query(ge=1, le=100)]
Skip = Annotated[int, Query(ge=0)]


def database_error(db: DbSession) -> HTTPException:
    db.rollback()
    return HTTPException(503, "Admin data could not be loaded")


@router.get("/overview", response_model=AdminOverview)
def overview(db: DbSession, response: Response) -> AdminOverview:
    response.headers["Cache-Control"] = "no-store"
    try:
        counts = [db.scalar(select(func.count()).select_from(model)) for model in (User, Document, Conversation, Message)]
        return AdminOverview(
            total_users=counts[0], total_documents=counts[1], total_conversations=counts[2], total_messages=counts[3],
            processing_counts=dict(db.execute(select(Document.status, func.count()).group_by(Document.status)).all()),
            embedding_counts=dict(db.execute(select(Document.embedding_status, func.count()).group_by(Document.embedding_status)).all()),
        )
    except SQLAlchemyError:
        raise database_error(db) from None


@router.get("/users", response_model=AdminUsers)
def users(db: DbSession, response: Response, skip: Skip = 0, limit: Limit = 20,
          email: Annotated[str | None, Query(max_length=254)] = None) -> AdminUsers:
    response.headers["Cache-Control"] = "no-store"
    filters = [User.email.contains(email.strip().lower(), autoescape=True)] if email and email.strip() else []
    try:
        total = db.scalar(select(func.count()).select_from(User).where(*filters))
        rows = db.scalars(select(User).where(*filters).order_by(User.created_at.desc(), User.id).offset(skip).limit(limit)).all()
        return AdminUsers(items=[AdminUser.model_validate(row) for row in rows], total=total, skip=skip, limit=limit)
    except SQLAlchemyError:
        raise database_error(db) from None


@router.get("/documents", response_model=AdminDocuments)
def documents(db: DbSession, response: Response, skip: Skip = 0, limit: Limit = 20,
              status: ProcessingState | None = None, embedding_status: EmbeddingState | None = None) -> AdminDocuments:
    response.headers["Cache-Control"] = "no-store"
    filters = []
    if status is not None:
        filters.append(Document.status == status)
    if embedding_status is not None:
        filters.append(Document.embedding_status == embedding_status)
    try:
        total = db.scalar(select(func.count()).select_from(Document).where(*filters))
        columns = [Document.id, Document.owner_id, User.email.label("owner_email"), Document.title,
                   Document.original_filename, Document.file_type, Document.file_size, Document.status,
                   Document.embedding_status, Document.created_at]
        rows = db.execute(select(*columns).join(User, User.id == Document.owner_id).where(*filters)
                          .order_by(Document.created_at.desc(), Document.id).offset(skip).limit(limit)).mappings().all()
        return AdminDocuments(items=[AdminDocument.model_validate(row) for row in rows], total=total, skip=skip, limit=limit)
    except SQLAlchemyError:
        raise database_error(db) from None
