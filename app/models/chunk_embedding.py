from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import JSON, DateTime, ForeignKey, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.embedding_config import VECTOR_DIMENSION
from app.db.base import Base

if TYPE_CHECKING:
    from app.models.document_chunk import DocumentChunk


class ChunkEmbedding(Base):
    __tablename__ = "chunk_embeddings"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True, default=uuid4)
    # One active embedding per chunk; model_name identifies its vector space.
    chunk_id: Mapped[UUID] = mapped_column(
        ForeignKey("document_chunks.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    # SQLite JSON is for isolated tests only. Production Settings require PostgreSQL.
    embedding: Mapped[list[float]] = mapped_column(
        Vector(VECTOR_DIMENSION).with_variant(JSON(), "sqlite"), nullable=False
    )
    model_name: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    chunk: Mapped["DocumentChunk"] = relationship(back_populates="embedding")
