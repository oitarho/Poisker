from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class LocationType(str, enum.Enum):
    republic = "republic"
    district = "district"
    city = "city"
    village = "village"


class Location(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "locations"
    __table_args__ = (
        UniqueConstraint("slug", name="uq_locations_slug"),
        Index("ix_locations_name", "name"),
        Index("ix_locations_parent_id", "parent_id"),
        Index("ix_locations_type", "type"),
        Index("ix_locations_parent_type", "parent_id", "type"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(200), nullable=False)

    type: Mapped[LocationType] = mapped_column(
        Enum(LocationType, name="location_type"), nullable=False
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="SET NULL"), nullable=True
    )

    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)

    parent: Mapped["Location | None"] = relationship(remote_side="Location.id", back_populates="children")
    children: Mapped[list["Location"]] = relationship(back_populates="parent")

    listings: Mapped[list["Listing"]] = relationship(back_populates="location")


from app.modules.listings.models import Listing  # noqa: E402

