from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class StartConversationRequest(BaseModel):
    listing_id: UUID


class ConversationOut(BaseModel):
    id: UUID
    listing_id: UUID
    owner_user_id: UUID
    interested_user_id: UUID
    created_at: datetime
    updated_at: datetime


class ConversationListResponse(BaseModel):
    items: list[ConversationOut] = Field(default_factory=list)


class ConversationSummaryOut(BaseModel):
    id: UUID
    listing_id: UUID
    other_user_id: UUID
    last_message_at: datetime | None
    last_read_at: datetime | None
    unread: bool


class ConversationSummaryListResponse(BaseModel):
    items: list[ConversationSummaryOut] = Field(default_factory=list)


class SendMessageRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class MessageOut(BaseModel):
    id: UUID
    conversation_id: UUID
    sender_id: UUID
    body: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[MessageOut] = Field(default_factory=list)


class MarkReadRequest(BaseModel):
    # mark as read up to "now" by default
    read_at: datetime | None = None

