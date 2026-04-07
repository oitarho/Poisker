from __future__ import annotations

import enum
import uuid

from sqlalchemy import Enum, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class ModerationEntityType(str, enum.Enum):
    listing = "listing"
    review = "review"
    user = "user"
    message = "message"


class ModerationLog(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "moderation_logs"
    __table_args__ = (
        Index("ix_moderation_logs_entity", "entity_type", "entity_id", "created_at"),
        Index("ix_moderation_logs_actor_admin_user_id", "actor_admin_user_id"),
    )

    actor_admin_user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True
    )

    entity_type: Mapped[ModerationEntityType] = mapped_column(
        Enum(ModerationEntityType, name="moderation_entity_type"), nullable=False
    )
    entity_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)

    action: Mapped[str] = mapped_column(String(64), nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    extra: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    # Optional FK to listing for fast joins when the moderated entity is a listing.
    listing_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("listings.id", ondelete="SET NULL"), nullable=True
    )

    actor_admin_user: Mapped["User | None"] = relationship()
    listing: Mapped["Listing | None"] = relationship(back_populates="moderation_logs")


from app.modules.users.models import User  # noqa: E402
from app.modules.listings.models import Listing  # noqa: E402

