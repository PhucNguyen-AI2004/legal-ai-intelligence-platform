from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.search import SearchRequest


class RAGRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    question: str = Field(min_length=1, max_length=1000)
    top_k: int = Field(default=5, ge=1, le=10)
    document_ids: list[UUID] | None = Field(default=None, min_length=1, max_length=100)

    @field_validator("question", mode="before")
    @classmethod
    def trim_question(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("document_ids")
    @classmethod
    def unique_ids(cls, value: list[UUID] | None) -> list[UUID] | None:
        return list(dict.fromkeys(value)) if value is not None else None

    def search_request(self) -> SearchRequest:
        return SearchRequest(query=self.question, top_k=self.top_k, document_ids=self.document_ids)


class Citation(BaseModel):
    citation_number: int
    document_id: UUID
    document_title: str
    chunk_id: UUID
    chunk_index: int
    score: float
    excerpt: str


class RAGResponse(BaseModel):
    answer: str
    grounded: bool
    citations: list[Citation]
    model: str | None
    retrieved_chunks: int
    used_chunks: int
