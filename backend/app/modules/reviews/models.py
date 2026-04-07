from __future__ import annotations

import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class Review(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "reviews"
    __table_args__ = (
        CheckConstraint("rating >= 1 AND rating <= 5", name="ck_reviews_rating_range"),
        UniqueConstraint("reviewer_id", "target_user_id", "listing_id", name="uq_reviews_pair_listing"),
        Index("ix_reviews_target_user_id_created_at", "target_user_id", "created_at"),
        Index("ix_reviews_listing_id", "listing_id"),
    )

    reviewer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    target_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )

    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    text: Mapped[str | None] = mapped_column(Text, nullable=True)

    reviewer: Mapped["User"] = relationship(
        foreign_keys=[reviewer_id], back_populates="reviews_written"
    )
    target_user: Mapped["User"] = relationship(
        foreign_keys=[target_user_id], back_populates="reviews_received"
    )
    listing: Mapped["Listing | None"] = relationship(back_populates="reviews")


from app.modules.users.models import User  # noqa: E402
from app.modules.listings.models import Listing  # noqa: E402

