"""Create owner-scoped document metadata.

Revision ID: 0002_create_documents
Revises: 0001_create_users
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_create_documents"
down_revision = "0001_create_users"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=False),
        sa.Column("original_filename", sa.String(255), nullable=False),
        sa.Column("stored_filename", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(50), nullable=False),
        sa.Column("file_type", sa.String(10), nullable=False),
        sa.Column("mime_type", sa.String(100), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(32), server_default="uploaded", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_documents")),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="RESTRICT", name=op.f("fk_documents_owner_id_users")),
        sa.UniqueConstraint("stored_filename", name=op.f("uq_documents_stored_filename")),
        sa.CheckConstraint("file_size > 0", name=op.f("ck_documents_positive_file_size")),
    )
    op.create_index("ix_documents_owner_created_id", "documents", ["owner_id", "created_at", "id"])


def downgrade() -> None:
    op.drop_index("ix_documents_owner_created_id", table_name="documents")
    op.drop_table("documents")
