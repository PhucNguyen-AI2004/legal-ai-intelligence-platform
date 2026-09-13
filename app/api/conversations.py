from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import selectinload

from app.api.dependencies import CurrentUser, DbSession
from app.core.config import get_settings
from app.models.message import Message
from app.models.message_citation import MessageCitation
from app.schemas.conversation import (
    ConversationCreate,
    ConversationDetail,
    ConversationList,
    ConversationMessageCreate,
    ConversationRead,
    ConversationUpdate,
    MessageCitationRead,
    MessageRead,
)
from app.services import conversation as conversation_service
from app.services.chat import post_message
from app.services.embeddings import EmbeddingBackend, EmbeddingError, get_embedding_service
from app.services.llm import LLMError, LLMProvider, get_llm_provider

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post("", response_model=ConversationRead, status_code=201)
def create_conversation(data: ConversationCreate, user: CurrentUser, db: DbSession) -> ConversationRead:
    try:
        return conversation_service.create_conversation(db, user.id, data.title)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation database operation failed") from None


@router.get("", response_model=ConversationList)
def list_conversations(
    user: CurrentUser,
    db: DbSession,
    response: Response,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> ConversationList:
    response.headers["Cache-Control"] = "no-store"
    try:
        items, total = conversation_service.list_conversations(db, user.id, limit, offset)
        return ConversationList(
            items=[ConversationRead.model_validate(item) for item in items],
            total=total,
            limit=limit,
            offset=offset,
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation database operation failed") from None


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: UUID, user: CurrentUser, db: DbSession, response: Response) -> ConversationDetail:
    response.headers["Cache-Control"] = "no-store"
    try:
        conversation = conversation_service.get_conversation_detail(db, conversation_id, user.id)
        return ConversationDetail(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at,
            messages=[_message_read(message) for message in conversation.messages],
        )
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation database operation failed") from None


@router.patch("/{conversation_id}", response_model=ConversationRead)
def rename_conversation(conversation_id: UUID, data: ConversationUpdate, user: CurrentUser, db: DbSession) -> ConversationRead:
    try:
        return conversation_service.rename_conversation(db, conversation_id, user.id, data.title)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation database operation failed") from None


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: UUID, user: CurrentUser, db: DbSession) -> Response:
    try:
        conversation_service.delete_conversation(db, conversation_id, user.id)
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation database operation failed") from None
    return Response(status_code=204)


@router.post("/{conversation_id}/messages", response_model=MessageRead)
def create_message(
    conversation_id: UUID,
    data: ConversationMessageCreate,
    user: CurrentUser,
    db: DbSession,
    response: Response,
    embeddings: Annotated[EmbeddingBackend, Depends(get_embedding_service)],
    provider: Annotated[LLMProvider, Depends(get_llm_provider)],
) -> MessageRead:
    response.headers["Cache-Control"] = "no-store"
    try:
        message = post_message(db, user.id, conversation_id, data, embeddings, provider, get_settings())
        return _load_message_read(db, message.id)
    except (LLMError, EmbeddingError) as exc:
        db.rollback()
        raise HTTPException(503, str(exc)) from None
    except SQLAlchemyError:
        db.rollback()
        raise HTTPException(503, "Conversation message database operation failed") from None


def _load_message_read(db: DbSession, message_id: UUID) -> MessageRead:
    message = db.scalar(
        select(Message)
        .where(Message.id == message_id)
        .options(
            selectinload(Message.citations).selectinload(MessageCitation.document),
            selectinload(Message.citations).selectinload(MessageCitation.chunk),
        )
    )
    if message is None:
        raise HTTPException(404, "Message not found")
    return _message_read(message)


def _message_read(message: Message) -> MessageRead:
    return MessageRead(
        id=message.id,
        conversation_id=message.conversation_id,
        role=message.role,
        content=message.content,
        sequence_number=message.sequence_number,
        grounded=message.grounded,
        retrieval_query=message.retrieval_query,
        created_at=message.created_at,
        citations=[
            MessageCitationRead(
                citation_index=citation.citation_index,
                document_id=citation.document_id,
                document_name=citation.document.title,
                chunk_id=citation.chunk_id,
                chunk_index=citation.chunk.chunk_index,
                similarity_score=citation.similarity_score,
            )
            for citation in message.citations
        ],
    )
