from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class SearchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=20)
    document_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("query", mode="before")
    @classmethod
    def strip_query(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("document_ids")
    @classmethod
    def deduplicate_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        return list(dict.fromkeys(value)) if value is not None else None


class SearchResult(BaseModel):
    document_id: UUID
    document_title: str
    chunk_id: UUID
    chunk_index: int
    content: str
    score: float = Field(ge=-1, le=1)


class SearchResponse(BaseModel):
    model_name: str
    results: list[SearchResult]


class DocumentIndexResult(BaseModel):
    document_id: UUID
    embedding_status: Literal["indexed"] = "indexed"
    embedded_chunks: int
    model_name: str
