from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import aliased

from app.api.deps import DbSession
from app.core.errors import AppError, ForbiddenError, NotFoundError
from app.modules.auth.deps import CurrentUser
from app.modules.chats.models import Conversation, ConversationParticipant, Message
from app.modules.chats.schemas import (
    ConversationListResponse,
    ConversationOut,
    ConversationSummaryListResponse,
    ConversationSummaryOut,
    MarkReadRequest,
    MessageListResponse,
    MessageOut,
    SendMessageRequest,
    StartConversationRequest,
)
from app.modules.listings.models import Listing

router = APIRouter(prefix="/chats", tags=["chats"])


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _conv_out(c: Conversation) -> ConversationOut:
    return ConversationOut(
        id=c.id,
        listing_id=c.listing_id,
        owner_user_id=c.owner_user_id,
        interested_user_id=c.interested_user_id,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


def _msg_out(m: Message) -> MessageOut:
    return MessageOut(
        id=m.id,
        conversation_id=m.conversation_id,
        sender_id=m.sender_id,
        body=m.body,
        created_at=m.created_at,
    )


class ConversationAlreadyExistsError(AppError):
    def __init__(self) -> None:
        super().__init__(code="conversation_exists", message="Conversation already exists", status_code=409)


async def _get_conversation_for_user(db: DbSession, *, conversation_id: UUID, user_id: UUID) -> Conversation:
    conv = await db.scalar(select(Conversation).where(Conversation.id == conversation_id))
    if conv is None:
        raise NotFoundError("Conversation not found")
    if user_id not in (conv.owner_user_id, conv.interested_user_id):
        raise ForbiddenError("Not a participant")
    return conv


@router.post("/conversations", response_model=ConversationOut, status_code=201)
async def start_conversation(
    payload: StartConversationRequest,
    db: DbSession,
    user: CurrentUser,
) -> ConversationOut:
    listing = await db.scalar(select(Listing).where(Listing.id == payload.listing_id))
    if listing is None:
        raise NotFoundError("Listing not found")

    owner_id = listing.owner_id
    interested_id = user.id
    if owner_id == interested_id:
        raise AppError(code="cannot_message_self", message="Cannot start a conversation with yourself", status_code=400)

    existing = await db.scalar(
        select(Conversation).where(
            Conversation.listing_id == listing.id,
            Conversation.owner_user_id == owner_id,
            Conversation.interested_user_id == interested_id,
        )
    )
    if existing is not None:
        return _conv_out(existing)

    conv = Conversation(listing_id=listing.id, owner_user_id=owner_id, interested_user_id=interested_id)
    db.add(conv)
    await db.flush()

    db.add_all(
        [
            ConversationParticipant(conversation_id=conv.id, user_id=owner_id, last_read_at=None),
            ConversationParticipant(conversation_id=conv.id, user_id=interested_id, last_read_at=None),
        ]
    )

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        # In case of a race, fetch the row.
        row = await db.scalar(
            select(Conversation).where(
                Conversation.listing_id == listing.id,
                Conversation.owner_user_id == owner_id,
                Conversation.interested_user_id == interested_id,
            )
        )
        if row is None:
            raise ConversationAlreadyExistsError()
        return _conv_out(row)

    await db.refresh(conv)
    return _conv_out(conv)


@router.get("/conversations", response_model=ConversationListResponse)
async def list_my_conversations(
    db: DbSession, user: CurrentUser, limit: int = 50, offset: int = 0
) -> ConversationListResponse:
    stmt = (
        select(Conversation)
        .where(or_(Conversation.owner_user_id == user.id, Conversation.interested_user_id == user.id))
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )
    rows = (await db.scalars(stmt)).all()
    return ConversationListResponse(items=[_conv_out(x) for x in rows])


@router.get("/conversations/summary", response_model=ConversationSummaryListResponse)
async def list_my_conversations_summary(
    db: DbSession, user: CurrentUser, limit: int = 50, offset: int = 0
) -> ConversationSummaryListResponse:
    """
    MVP-optimized list endpoint for UI:
    - includes last_message_at
    - includes last_read_at for current user
    - computes unread boolean
    """

    cp = aliased(ConversationParticipant)
    last_msg_subq = (
        select(Message.conversation_id, func.max(Message.created_at).label("last_message_at"))
        .group_by(Message.conversation_id)
        .subquery()
    )

    stmt = (
        select(Conversation, cp.last_read_at, last_msg_subq.c.last_message_at)
        .join(cp, (cp.conversation_id == Conversation.id) & (cp.user_id == user.id))
        .outerjoin(last_msg_subq, last_msg_subq.c.conversation_id == Conversation.id)
        .where(or_(Conversation.owner_user_id == user.id, Conversation.interested_user_id == user.id))
        .order_by(Conversation.updated_at.desc())
        .limit(limit)
        .offset(offset)
    )

    rows = (await db.execute(stmt)).all()

    items: list[ConversationSummaryOut] = []
    for conv, last_read_at, last_message_at in rows:
        other_user_id = conv.interested_user_id if conv.owner_user_id == user.id else conv.owner_user_id
        unread = False
        if last_message_at is not None:
            if last_read_at is None or last_message_at > last_read_at:
                unread = True
        items.append(
            ConversationSummaryOut(
                id=conv.id,
                listing_id=conv.listing_id,
                other_user_id=other_user_id,
                last_message_at=last_message_at,
                last_read_at=last_read_at,
                unread=unread,
            )
        )
    return ConversationSummaryListResponse(items=items)


@router.get("/conversations/{conversation_id}/messages", response_model=MessageListResponse)
async def get_conversation_messages(
    conversation_id: UUID,
    db: DbSession,
    user: CurrentUser,
    limit: int = 50,
    before: datetime | None = None,
) -> MessageListResponse:
    await _get_conversation_for_user(db, conversation_id=conversation_id, user_id=user.id)

    stmt = select(Message).where(Message.conversation_id == conversation_id).order_by(Message.created_at.desc()).limit(limit)
    if before is not None:
        stmt = stmt.where(Message.created_at < before)
    rows = (await db.scalars(stmt)).all()
    # return in chronological order for UI
    rows = list(reversed(rows))
    return MessageListResponse(items=[_msg_out(x) for x in rows])


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
async def send_message(
    conversation_id: UUID,
    payload: SendMessageRequest,
    db: DbSession,
    user: CurrentUser,
) -> MessageOut:
    conv = await _get_conversation_for_user(db, conversation_id=conversation_id, user_id=user.id)

    msg = Message(conversation_id=conv.id, sender_id=user.id, body=payload.body)
    db.add(msg)
    await db.commit()
    await db.refresh(msg)
    return _msg_out(msg)


@router.post("/conversations/{conversation_id}/read", response_model=dict)
async def mark_messages_read(
    conversation_id: UUID,
    payload: MarkReadRequest,
    db: DbSession,
    user: CurrentUser,
) -> dict:
    await _get_conversation_for_user(db, conversation_id=conversation_id, user_id=user.id)
    read_at = payload.read_at or _now()
    participant = await db.scalar(
        select(ConversationParticipant).where(
            ConversationParticipant.conversation_id == conversation_id,
            ConversationParticipant.user_id == user.id,
        )
    )
    if participant is None:
        raise ForbiddenError("Not a participant")
    participant.last_read_at = read_at
    await db.commit()
    return {"status": "ok", "read_at": read_at.isoformat()}


# --- Optional local dev websocket (no Redis yet) ---
# This is intentionally simple: it validates membership, then echoes messages.
# Later we can back it with Redis PubSub or Postgres NOTIFY for multi-worker.
_ws_connections: dict[UUID, set[WebSocket]] = {}


@router.websocket("/ws/{conversation_id}")
async def chat_ws(websocket: WebSocket, conversation_id: UUID):
    await websocket.accept()
    # MVP: no auth over WS yet; keep endpoint for local experiments.
    # Proper WS auth will be added later (JWT in query/header).
    conns = _ws_connections.setdefault(conversation_id, set())
    conns.add(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            # broadcast
            for ws in list(conns):
                try:
                    await ws.send_text(text)
                except Exception:
                    conns.discard(ws)
    except WebSocketDisconnect:
        conns.discard(websocket)

