from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class User(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    full_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)

    is_email_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_phone_verified: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")

    rating: Mapped[float] = mapped_column(nullable=False, server_default="0")
    reviews_count: Mapped[int] = mapped_column(nullable=False, server_default="0")

    last_login_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    sessions: Mapped[list["RefreshToken"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    listings: Mapped[list["Listing"]] = relationship(back_populates="owner")
    favorites: Mapped[list["Favorite"]] = relationship(back_populates="user")

    sent_messages: Mapped[list["Message"]] = relationship(back_populates="sender")
    reviews_written: Mapped[list["Review"]] = relationship(
        foreign_keys="Review.reviewer_id", back_populates="reviewer"
    )
    reviews_received: Mapped[list["Review"]] = relationship(
        foreign_keys="Review.target_user_id", back_populates="target_user"
    )


class RefreshToken(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """
    Server-side refresh token record (supports logout/rotation later).
    We store a token identifier (jti) instead of the raw JWT.
    """

    __tablename__ = "refresh_tokens"
    __table_args__ = (
        UniqueConstraint("jti", name="uq_refresh_tokens_jti"),
        Index("ix_refresh_tokens_user_id_created_at", "user_id", "created_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    jti: Mapped[str] = mapped_column(String(64), nullable=False)
    revoked: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)

    user: Mapped["User"] = relationship(back_populates="sessions")


# late imports for type checking / relationship targets
from app.modules.favorites.models import Favorite  # noqa: E402
from app.modules.listings.models import Listing  # noqa: E402
from app.modules.chats.models import Message  # noqa: E402
from app.modules.reviews.models import Review  # noqa: E402

