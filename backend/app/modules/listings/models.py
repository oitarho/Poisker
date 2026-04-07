from __future__ import annotations

import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ListingKind(str, enum.Enum):
    product = "product"
    service = "service"


class ListingStatus(str, enum.Enum):
    draft = "draft"
    pending = "pending"
    active = "active"
    archived = "archived"
    rejected = "rejected"


class Listing(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "listings"
    __table_args__ = (
        Index("ix_listings_kind_status_published_at", "kind", "status", "published_at"),
        Index("ix_listings_location_id", "location_id"),
        Index("ix_listings_category_id", "category_id"),
        Index("ix_listings_owner_id", "owner_id"),
        CheckConstraint("price >= 0", name="ck_listings_price_nonnegative"),
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    location_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("locations.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("categories.id", ondelete="RESTRICT"), nullable=False
    )

    kind: Mapped[ListingKind] = mapped_column(Enum(ListingKind, name="listing_kind"), nullable=False)
    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"), nullable=False, index=True
    )

    title: Mapped[str] = mapped_column(String(120), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    price: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, server_default="0")

    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True, index=True)

    # ranking support
    views_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    favorites_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    boost_score: Mapped[float] = mapped_column(Numeric(8, 3), nullable=False, server_default="0")

    owner: Mapped["User"] = relationship(back_populates="listings")
    location: Mapped["Location"] = relationship(back_populates="listings")
    category: Mapped["Category"] = relationship(back_populates="listings")

    photos: Mapped[list["ListingPhoto"]] = relationship(
        back_populates="listing", cascade="all, delete-orphan", order_by="ListingPhoto.sort_order"
    )
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="listing")
    conversations: Mapped[list["Conversation"]] = relationship(back_populates="listing")
    reviews: Mapped[list["Review"]] = relationship(back_populates="listing")
    moderation_logs: Mapped[list["ModerationLog"]] = relationship(back_populates="listing")


class ListingPhoto(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "listing_photos"
    __table_args__ = (
        UniqueConstraint("listing_id", "sort_order", name="uq_listing_photos_listing_sort"),
        Index("ix_listing_photos_listing_id", "listing_id"),
    )

    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="CASCADE"), nullable=False
    )
    key: Mapped[str] = mapped_column(String(500), nullable=False)
    content_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")

    listing: Mapped["Listing"] = relationship(back_populates="photos")


from app.modules.users.models import User  # noqa: E402
from app.modules.locations.models import Location  # noqa: E402
from app.modules.categories.models import Category  # noqa: E402
from app.modules.favorites.models import Favorite  # noqa: E402
from app.modules.chats.models import Conversation  # noqa: E402
from app.modules.reviews.models import Review  # noqa: E402
from app.modules.moderation.models import ModerationLog  # noqa: E402

