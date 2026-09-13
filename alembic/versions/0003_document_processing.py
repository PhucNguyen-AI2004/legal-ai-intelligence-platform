"""Add document processing errors and persistent chunks.

Revision ID: 0003_document_processing
Revises: 0002_create_documents
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_document_processing"
down_revision = "0002_create_documents"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("processing_error", sa.String(500), nullable=True))
    op.create_table(
        "document_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("document_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("char_count", sa.Integer(), nullable=False),
        sa.Column("token_estimate", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_chunks")),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"], ondelete="CASCADE", name=op.f("fk_document_chunks_document_id_documents")),
        sa.UniqueConstraint("document_id", "chunk_index", name="uq_document_chunks_document_index"),
        sa.CheckConstraint("chunk_index >= 0", name=op.f("ck_document_chunks_nonnegative_chunk_index")),
        sa.CheckConstraint("char_count > 0", name=op.f("ck_document_chunks_positive_char_count")),
        sa.CheckConstraint("token_estimate > 0", name=op.f("ck_document_chunks_positive_token_estimate")),
    )


def downgrade() -> None:
    op.drop_table("document_chunks")
    op.drop_column("documents", "processing_error")
