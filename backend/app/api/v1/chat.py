import os
import uuid as uuid_mod
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import ChatRoom, Message, User
from app.schemas.chat import (
    ChatRoomResponse,
    MessageBrief,
    MessageCreate,
    MessageResponse,
)
from app.schemas.master import UserBrief

router = APIRouter()

UPLOAD_DIR = Path("/opt/local-services/backend/uploads/chat")


async def _get_room_or_403(
    room_id: UUID,
    current_user: User,
    db: AsyncSession,
) -> ChatRoom:
    result = await db.execute(
        select(ChatRoom)
        .options(
            selectinload(ChatRoom.client),
            selectinload(ChatRoom.master_user),
        )
        .where(ChatRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if not room:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat room not found",
        )
    if current_user.id not in (room.client_id, room.master_user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this chat room",
        )
    return room


@router.get("/", response_model=list[ChatRoomResponse])
async def list_chat_rooms(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        select(ChatRoom)
        .options(
            selectinload(ChatRoom.client),
            selectinload(ChatRoom.master_user),
        )
        .where(
            (ChatRoom.client_id == current_user.id)
            | (ChatRoom.master_user_id == current_user.id)
        )
        .order_by(ChatRoom.created_at.desc())
    )
    rooms = result.scalars().all()

    items = []
    for room in rooms:
        # Get last message
        last_msg_result = await db.execute(
            select(Message)
            .where(Message.room_id == room.id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )
        last_msg = last_msg_result.scalar_one_or_none()

        # Get unread count (messages not sent by current user and not read)
        unread_result = await db.execute(
            select(func.count(Message.id)).where(
                Message.room_id == room.id,
                Message.sender_id != current_user.id,
                Message.is_read == False,
            )
        )
        unread_count = unread_result.scalar()

        # Determine counterparty
        if current_user.id == room.client_id:
            counterparty = room.master_user
        else:
            counterparty = room.client

        items.append(
            ChatRoomResponse(
                id=room.id,
                booking_id=room.booking_id,
                counterparty=UserBrief.model_validate(counterparty),
                last_message=MessageBrief.model_validate(last_msg)
                if last_msg
                else None,
                unread_count=unread_count,
            )
        )

    return items


@router.get("/{room_id}/messages")
async def get_messages(
    room_id: UUID,
    before: UUID | None = Query(None),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_room_or_403(room_id, current_user, db)

    query = select(Message).where(Message.room_id == room_id)

    if before:
        # Get the created_at of the cursor message
        cursor_result = await db.execute(
            select(Message.created_at).where(Message.id == before)
        )
        cursor_ts = cursor_result.scalar_one_or_none()
        if cursor_ts:
            query = query.where(Message.created_at < cursor_ts)

    query = query.order_by(Message.created_at.desc()).limit(limit + 1)

    result = await db.execute(query)
    messages = result.scalars().all()

    has_more = len(messages) > limit
    messages = messages[:limit]

    items = [
        MessageResponse(
            id=m.id,
            sender_id=m.sender_id,
            content=m.content or "",
            image_url=m.image_url,
            is_read=m.is_read,
            created_at=m.created_at,
        )
        for m in messages
    ]

    return {"items": items, "has_more": has_more}


@router.post("/{room_id}/messages", response_model=MessageResponse)
async def send_message(
    room_id: UUID,
    data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_room_or_403(room_id, current_user, db)

    message = Message(
        room_id=room_id,
        sender_id=current_user.id,
        content=data.content,
        image_url=data.image_url,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        content=message.content or "",
        image_url=message.image_url,
        is_read=message.is_read,
        created_at=message.created_at,
    )


@router.post("/{room_id}/image", response_model=MessageResponse)
async def send_image_message(
    room_id: UUID,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    await _get_room_or_403(room_id, current_user, db)

    # Validate file
    if file.content_type not in ("image/jpeg", "image/png"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only JPEG and PNG images are allowed",
        )

    contents = await file.read()
    if len(contents) > 10 * 1024 * 1024:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size must not exceed 10MB",
        )

    # Save file
    ext = "jpg" if file.content_type == "image/jpeg" else "png"
    filename = f"{uuid_mod.uuid4()}.{ext}"
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    filepath = UPLOAD_DIR / filename
    with open(filepath, "wb") as f:
        f.write(contents)

    image_url = f"/uploads/chat/{filename}"

    message = Message(
        room_id=room_id,
        sender_id=current_user.id,
        content="",
        image_url=image_url,
    )
    db.add(message)
    await db.commit()
    await db.refresh(message)

    return MessageResponse(
        id=message.id,
        sender_id=message.sender_id,
        content=message.content or "",
        image_url=message.image_url,
        is_read=message.is_read,
        created_at=message.created_at,
    )
