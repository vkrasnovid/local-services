import json
import logging
from uuid import UUID

from fastapi import WebSocket, WebSocketDisconnect, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.core.security import verify_access_token
from app.models import User, ChatRoom, Message

logger = logging.getLogger(__name__)


class ConnectionManager:
    """Manages active WebSocket connections per chat room."""

    def __init__(self):
        # room_id -> {user_id -> WebSocket}
        self.rooms: dict[str, dict[str, WebSocket]] = {}

    async def connect(self, websocket: WebSocket, room_id: str, user_id: str):
        await websocket.accept()
        if room_id not in self.rooms:
            self.rooms[room_id] = {}
        self.rooms[room_id][user_id] = websocket

    def disconnect(self, room_id: str, user_id: str):
        if room_id in self.rooms:
            self.rooms[room_id].pop(user_id, None)
            if not self.rooms[room_id]:
                del self.rooms[room_id]

    async def broadcast_to_room(self, room_id: str, message: dict, exclude_user: str | None = None):
        if room_id not in self.rooms:
            return
        for uid, ws in self.rooms[room_id].items():
            if uid != exclude_user:
                try:
                    await ws.send_json(message)
                except Exception:
                    pass


manager = ConnectionManager()


async def chat_websocket(websocket: WebSocket, room_id: str, token: str | None = None):
    """WebSocket endpoint: /ws/chat/{room_id}?token=JWT"""
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify JWT
    try:
        payload = verify_access_token(token)
        user_id = payload["sub"]
    except Exception:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    # Verify user is participant of this room
    async with async_session() as db:
        room = await db.get(ChatRoom, UUID(room_id))
        if not room or (str(room.client_id) != user_id and str(room.master_user_id) != user_id):
            await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
            return

    await manager.connect(websocket, room_id, user_id)

    try:
        while True:
            data = await websocket.receive_json()
            event = data.get("event")
            event_data = data.get("data", {})

            if event == "message.send":
                await handle_message_send(room_id, user_id, event_data)
            elif event == "message.read":
                await handle_message_read(room_id, user_id, event_data)
            elif event == "user.typing":
                await handle_typing(room_id, user_id)
            else:
                await websocket.send_json({
                    "event": "error",
                    "data": {"code": "UNKNOWN_EVENT", "message": f"Unknown event: {event}"}
                })
    except WebSocketDisconnect:
        manager.disconnect(room_id, user_id)
        # Broadcast user offline
        await manager.broadcast_to_room(room_id, {
            "event": "user.offline",
            "data": {"user_id": user_id}
        })
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(room_id, user_id)


async def handle_message_send(room_id: str, sender_id: str, data: dict):
    content = data.get("content", "")
    image_url = data.get("image_url")

    if not content and not image_url:
        return

    async with async_session() as db:
        message = Message(
            room_id=UUID(room_id),
            sender_id=UUID(sender_id),
            content=content,
            image_url=image_url,
        )
        db.add(message)
        await db.commit()
        await db.refresh(message)

        await manager.broadcast_to_room(room_id, {
            "event": "message.new",
            "data": {
                "id": str(message.id),
                "room_id": room_id,
                "sender_id": sender_id,
                "content": message.content,
                "image_url": message.image_url,
                "created_at": message.created_at.isoformat(),
            }
        })


async def handle_message_read(room_id: str, reader_id: str, data: dict):
    last_read_id = data.get("last_read_message_id")
    if not last_read_id:
        return

    async with async_session() as db:
        # Mark all messages up to last_read_id as read (only messages from the other user)
        await db.execute(
            update(Message)
            .where(
                Message.room_id == UUID(room_id),
                Message.sender_id != UUID(reader_id),
                Message.is_read == False,
                Message.id <= UUID(last_read_id),
            )
            .values(is_read=True)
        )
        await db.commit()

    await manager.broadcast_to_room(room_id, {
        "event": "message.read_receipt",
        "data": {
            "room_id": room_id,
            "reader_id": reader_id,
            "last_read_message_id": last_read_id,
        }
    }, exclude_user=reader_id)


async def handle_typing(room_id: str, user_id: str):
    await manager.broadcast_to_room(room_id, {
        "event": "user.typing",
        "data": {
            "room_id": room_id,
            "user_id": user_id,
        }
    }, exclude_user=user_id)
