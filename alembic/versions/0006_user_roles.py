"""Add persisted user/admin role; existing accounts remain ordinary users."""
from alembic import op
import sqlalchemy as sa

revision = "0006_user_roles"
down_revision = "0005_conversations_and_messages"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # SQLite cannot rebuild a referenced users table with foreign keys enabled.
    # A column-level CHECK allows an additive migration without table replacement.
    if op.get_bind().dialect.name == "sqlite":
        op.execute("ALTER TABLE users ADD COLUMN role VARCHAR(20) NOT NULL DEFAULT 'user' CONSTRAINT ck_users_valid_user_role CHECK (role IN ('user', 'admin'))")
    else:
        op.add_column("users", sa.Column("role", sa.String(20), nullable=False, server_default="user"))
        op.create_check_constraint("valid_user_role", "users", "role IN ('user', 'admin')")


def downgrade() -> None:
    if op.get_bind().dialect.name != "sqlite":
        op.drop_constraint("valid_user_role", "users", type_="check")
    op.drop_column("users", "role")
