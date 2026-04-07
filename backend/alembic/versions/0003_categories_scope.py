"""categories scope (product/service/both)

Revision ID: 0003_categories_scope
Revises: 0002_locations_hierarchy
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0003_categories_scope"
down_revision = "0002_locations_hierarchy"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "DO $$ BEGIN CREATE TYPE category_scope AS ENUM ('product','service','both'); "
        "EXCEPTION WHEN duplicate_object THEN NULL; END $$;"
    )
    op.add_column(
        "categories",
        sa.Column(
            "scope",
            postgresql.ENUM("product", "service", "both", name="category_scope", create_type=False),
            nullable=True,
        ),
    )
    op.execute("UPDATE categories SET scope='both' WHERE scope IS NULL;")
    op.alter_column("categories", "scope", nullable=False)
    op.create_index("ix_categories_scope", "categories", ["scope"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_categories_scope", table_name="categories")
    op.drop_column("categories", "scope")
    op.execute("DROP TYPE category_scope;")

