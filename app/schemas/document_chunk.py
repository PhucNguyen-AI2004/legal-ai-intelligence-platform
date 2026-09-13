from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class DocumentChunkRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    chunk_index: int
    content: str
    char_count: int
    token_estimate: int
    created_at: datetime


class DocumentChunkList(BaseModel):
    document_id: UUID
    status: str
    items: list[DocumentChunkRead]
    total: int
    skip: int
    limit: int


class DocumentProcessResult(BaseModel):
    document_id: UUID
    status: Literal["processed"] = "processed"
    chunk_count: int
    message: str = "Document processed successfully"
