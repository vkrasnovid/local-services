import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.user import User


class ChatRoom(BaseModel):
    __tablename__ = "chat_rooms"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id"),
        unique=True,
        nullable=False,
    )
    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    master_user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking", back_populates="chat_room"
    )
    client: Mapped["User"] = relationship(
        "User", foreign_keys=[client_id]
    )
    master_user: Mapped["User"] = relationship(
        "User", foreign_keys=[master_user_id]
    )
    messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="room"
    )

    def __repr__(self) -> str:
        return f"<ChatRoom {self.id} booking={self.booking_id}>"


class Message(BaseModel):
    __tablename__ = "messages"

    room_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("chat_rooms.id", ondelete="CASCADE"),
        nullable=False,
    )
    sender_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    image_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    room: Mapped["ChatRoom"] = relationship(
        "ChatRoom", back_populates="messages"
    )
    sender: Mapped["User"] = relationship(
        "User", back_populates="sent_messages"
    )

    __table_args__ = (
        Index("ix_messages_room_id_created_at", "room_id", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Message {self.id} room={self.room_id}>"
