from uuid import UUID, uuid4

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.models.conversation import Conversation
from app.models.message import Message
from app.models.message_citation import MessageCitation


def create_conversation(db: Session, user_id: UUID, title: str | None) -> Conversation:
    conversation = Conversation(id=uuid4(), user_id=user_id, title=title or "New conversation")
    db.add(conversation)
    db.flush()
    db.refresh(conversation)
    db.commit()
    return conversation


def list_conversations(db: Session, user_id: UUID, limit: int, offset: int) -> tuple[list[Conversation], int]:
    condition = Conversation.user_id == user_id
    total = db.scalar(select(func.count()).select_from(Conversation).where(condition)) or 0
    items = db.scalars(
        select(Conversation)
        .where(condition)
        .order_by(Conversation.updated_at.desc(), Conversation.id.desc())
        .offset(offset)
        .limit(limit)
    ).all()
    return list(items), total


def get_owned_conversation(db: Session, conversation_id: UUID, user_id: UUID, *, lock: bool = False) -> Conversation:
    query = select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user_id)
    if lock:
        query = query.with_for_update().execution_options(populate_existing=True)
    conversation = db.scalar(query)
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    return conversation


def get_conversation_detail(db: Session, conversation_id: UUID, user_id: UUID) -> Conversation:
    conversation = db.scalar(
        select(Conversation)
        .where(Conversation.id == conversation_id, Conversation.user_id == user_id)
        .options(
            selectinload(Conversation.messages)
            .selectinload(Message.citations)
            .selectinload(MessageCitation.document),
            selectinload(Conversation.messages)
            .selectinload(Message.citations)
            .selectinload(MessageCitation.chunk),
        )
    )
    if conversation is None:
        raise HTTPException(404, "Conversation not found")
    return conversation


def rename_conversation(db: Session, conversation_id: UUID, user_id: UUID, title: str) -> Conversation:
    conversation = get_owned_conversation(db, conversation_id, user_id, lock=True)
    conversation.title = title
    db.flush()
    db.refresh(conversation)
    db.commit()
    return conversation


def delete_conversation(db: Session, conversation_id: UUID, user_id: UUID) -> None:
    conversation = get_owned_conversation(db, conversation_id, user_id, lock=True)
    db.delete(conversation)
    db.commit()
