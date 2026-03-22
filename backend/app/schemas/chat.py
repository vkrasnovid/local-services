from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.master import UserBrief


class MessageBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    content: str
    sender_id: UUID
    created_at: datetime


class ChatRoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    counterparty: UserBrief
    last_message: Optional[MessageBrief] = None
    unread_count: int


class MessageResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    sender_id: UUID
    content: str
    image_url: Optional[str] = None
    is_read: bool
    created_at: datetime


class MessageCreate(BaseModel):
    content: str
    image_url: Optional[str] = None
