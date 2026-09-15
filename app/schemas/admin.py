from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict

ProcessingState = Literal["uploaded", "processing", "processed", "failed"]
EmbeddingState = Literal["pending", "indexing", "indexed", "failed"]


class AdminOverview(BaseModel):
    total_users: int
    total_documents: int
    total_conversations: int
    total_messages: int
    processing_counts: dict[str, int]
    embedding_counts: dict[str, int]


class AdminUser(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    email: str
    role: Literal["user", "admin"]
    created_at: datetime


class AdminUsers(BaseModel):
    items: list[AdminUser]
    total: int
    skip: int
    limit: int


class AdminDocument(BaseModel):
    # Explicit allowlist. Never reuse the owner-facing document schema here.
    id: UUID
    owner_id: UUID
    owner_email: str
    title: str
    original_filename: str
    file_type: str
    file_size: int
    status: str
    embedding_status: str
    created_at: datetime


class AdminDocuments(BaseModel):
    items: list[AdminDocument]
    total: int
    skip: int
    limit: int
