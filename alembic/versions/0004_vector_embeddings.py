"""Add pgvector embeddings and an independent document indexing lifecycle.

Revision ID: 0004_vector_embeddings
Revises: 0003_document_processing
"""
from alembic import op
from pgvector.sqlalchemy import Vector
import sqlalchemy as sa

revision = "0004_vector_embeddings"
down_revision = "0003_document_processing"
branch_labels = None
depends_on = None

# Historical schema snapshot: never import mutable application configuration here.
VECTOR_DIMENSION = 384


def upgrade() -> None:
    if op.get_context().dialect.name == "postgresql":
        op.execute("CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA public")
    op.add_column("documents", sa.Column("embedding_status", sa.String(32), server_default="pending", nullable=False))
    op.add_column("documents", sa.Column("embedding_error", sa.String(500), nullable=True))
    op.add_column("documents", sa.Column("embedded_at", sa.DateTime(timezone=True), nullable=True))
    op.create_table(
        "chunk_embeddings",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        # SQLite is only used by isolated tests, not by the application runtime.
        sa.Column("embedding", Vector(VECTOR_DIMENSION).with_variant(sa.JSON(), "sqlite"), nullable=False),
        sa.Column("model_name", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chunk_embeddings")),
        sa.ForeignKeyConstraint(["chunk_id"], ["document_chunks.id"], ondelete="CASCADE", name=op.f("fk_chunk_embeddings_chunk_id_document_chunks")),
        sa.UniqueConstraint("chunk_id", name=op.f("uq_chunk_embeddings_chunk_id")),
    )


def downgrade() -> None:
    op.drop_table("chunk_embeddings")
    op.drop_column("documents", "embedded_at")
    op.drop_column("documents", "embedding_error")
    op.drop_column("documents", "embedding_status")
    # Keep the shared extension: other schemas/tables may still depend on it.
