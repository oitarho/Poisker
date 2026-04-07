"""add email_verified_at to users

Revision ID: 0005_email_verified_at
Revises: 0004_chats_owner_interested_read
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "0005_email_verified_at"
down_revision = "0004_chats_owner_interested_read"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("email_verified_at", postgresql.TIMESTAMP(timezone=True), nullable=True),
    )
    op.create_index("ix_users_email_verified_at", "users", ["email_verified_at"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_users_email_verified_at", table_name="users")
    op.drop_column("users", "email_verified_at")
