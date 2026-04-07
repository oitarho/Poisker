"""locations hierarchy and geo fields

Revision ID: 0002_locations_hierarchy
Revises: 0001_initial
Create Date: 2026-04-07
"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision = "0002_locations_hierarchy"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE location_type AS ENUM ('republic','district','city','village');")

    op.add_column("locations", sa.Column("type", sa.Enum(name="location_type"), nullable=True))
    op.add_column(
        "locations",
        sa.Column("parent_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("locations.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column("locations", sa.Column("latitude", sa.Numeric(10, 7), nullable=True))
    op.add_column("locations", sa.Column("longitude", sa.Numeric(10, 7), nullable=True))

    # backfill existing rows (if any) as republic
    op.execute("UPDATE locations SET type='republic' WHERE type IS NULL;")
    op.alter_column("locations", "type", nullable=False)

    op.create_index("ix_locations_parent_id", "locations", ["parent_id"], unique=False)
    op.create_index("ix_locations_type", "locations", ["type"], unique=False)
    op.create_index("ix_locations_parent_type", "locations", ["parent_id", "type"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_locations_parent_type", table_name="locations")
    op.drop_index("ix_locations_type", table_name="locations")
    op.drop_index("ix_locations_parent_id", table_name="locations")

    op.drop_column("locations", "longitude")
    op.drop_column("locations", "latitude")
    op.drop_column("locations", "parent_id")
    op.drop_column("locations", "type")

    op.execute("DROP TYPE location_type;")

