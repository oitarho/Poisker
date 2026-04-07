"""chats: owner/interested uniqueness + read tracking

Revision ID: 0004_chats_owner_interested_read
Revises: 0003_categories_scope
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0004_chats_owner_interested_read"
down_revision = "0003_categories_scope"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # conversations: replace starter_user_id with owner/interested
    op.add_column(
        "conversations",
        sa.Column("owner_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.add_column(
        "conversations",
        sa.Column("interested_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )

    # Backfill: assume starter_user_id was the interested user, owner is listing.owner_id
    op.execute(
        """
        UPDATE conversations c
        SET
          interested_user_id = c.starter_user_id,
          owner_user_id = l.owner_id
        FROM listings l
        WHERE l.id = c.listing_id
        """
    )

    op.create_foreign_key(
        "fk_conversations_owner_user_id_users",
        "conversations",
        "users",
        ["owner_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_conversations_interested_user_id_users",
        "conversations",
        "users",
        ["interested_user_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.alter_column("conversations", "owner_user_id", nullable=False)
    op.alter_column("conversations", "interested_user_id", nullable=False)

    # Drop old constraint + column
    op.drop_constraint("uq_conversations_listing_starter", "conversations", type_="unique")
    op.drop_column("conversations", "starter_user_id")

    # New constraint + indexes
    op.create_unique_constraint(
        "uq_conversations_listing_owner_interested",
        "conversations",
        ["listing_id", "owner_user_id", "interested_user_id"],
    )
    op.create_index("ix_conversations_owner_user_id", "conversations", ["owner_user_id"], unique=False)
    op.create_index(
        "ix_conversations_interested_user_id", "conversations", ["interested_user_id"], unique=False
    )

    # participants: read tracking and index
    op.add_column("conversation_participants", sa.Column("last_read_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(
        "ix_conv_participants_conversation_id",
        "conversation_participants",
        ["conversation_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_conv_participants_conversation_id", table_name="conversation_participants")
    op.drop_column("conversation_participants", "last_read_at")

    op.drop_index("ix_conversations_interested_user_id", table_name="conversations")
    op.drop_index("ix_conversations_owner_user_id", table_name="conversations")
    op.drop_constraint("uq_conversations_listing_owner_interested", "conversations", type_="unique")

    op.add_column(
        "conversations",
        sa.Column("starter_user_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.execute("UPDATE conversations SET starter_user_id = interested_user_id")
    op.alter_column("conversations", "starter_user_id", nullable=False)
    op.create_foreign_key(
        "fk_conversations_starter_user_id_users",
        "conversations",
        "users",
        ["starter_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_unique_constraint(
        "uq_conversations_listing_starter", "conversations", ["listing_id", "starter_user_id"]
    )

    op.drop_constraint("fk_conversations_interested_user_id_users", "conversations", type_="foreignkey")
    op.drop_constraint("fk_conversations_owner_user_id_users", "conversations", type_="foreignkey")
    op.drop_column("conversations", "interested_user_id")
    op.drop_column("conversations", "owner_user_id")

