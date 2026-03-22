import uuid
from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Index, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, BaseModel, TimestampMixin

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.chat import ChatRoom, Message
    from app.models.master import MasterProfile
    from app.models.notification import FcmToken, Notification
    from app.models.refresh_token import RefreshToken
    from app.models.review import Review


class User(BaseModel, TimestampMixin):
    __tablename__ = "users"

    phone: Mapped[Optional[str]] = mapped_column(
        String(20), unique=True, nullable=True
    )
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(
        String(20), nullable=False, server_default="client"
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    avatar_url: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    is_active: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )

    # Relationships
    master_profile: Mapped[Optional["MasterProfile"]] = relationship(
        "MasterProfile", back_populates="user", uselist=False
    )
    refresh_tokens: Mapped[List["RefreshToken"]] = relationship(
        "RefreshToken", back_populates="user"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="client", foreign_keys="Booking.client_id"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="client"
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification", back_populates="user"
    )
    fcm_tokens: Mapped[List["FcmToken"]] = relationship(
        "FcmToken", back_populates="user"
    )
    sent_messages: Mapped[List["Message"]] = relationship(
        "Message", back_populates="sender"
    )

    __table_args__ = (
        Index("ix_users_phone", "phone"),
        Index("ix_users_email", "email"),
        Index("ix_users_role", "role"),
        Index("ix_users_city", "city"),
    )

    def __repr__(self) -> str:
        return f"<User {self.id} {self.email or self.phone}>"
