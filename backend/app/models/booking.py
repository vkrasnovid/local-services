import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel, TimestampMixin

if TYPE_CHECKING:
    from app.models.chat import ChatRoom
    from app.models.master import MasterProfile
    from app.models.payment import Payment
    from app.models.review import Review
    from app.models.service import Service
    from app.models.time_slot import TimeSlot
    from app.models.user import User


class Booking(BaseModel, TimestampMixin):
    __tablename__ = "bookings"

    client_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_profiles.id"),
        nullable=False,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("services.id"),
        nullable=False,
    )
    slot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("time_slots.id"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    price: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2), nullable=True
    )
    address: Mapped[Optional[str]] = mapped_column(
        String(500), nullable=True
    )
    is_online: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    cancel_reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    cancelled_by: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True
    )

    # Relationships
    client: Mapped["User"] = relationship(
        "User", back_populates="bookings", foreign_keys=[client_id]
    )
    master: Mapped["MasterProfile"] = relationship(
        "MasterProfile", back_populates="bookings"
    )
    service: Mapped["Service"] = relationship(
        "Service", back_populates="bookings"
    )
    slot: Mapped["TimeSlot"] = relationship(
        "TimeSlot", back_populates="booking"
    )
    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="booking", uselist=False
    )
    review: Mapped[Optional["Review"]] = relationship(
        "Review", back_populates="booking", uselist=False
    )
    chat_room: Mapped[Optional["ChatRoom"]] = relationship(
        "ChatRoom", back_populates="booking", uselist=False
    )

    __table_args__ = (
        Index("ix_bookings_client_id", "client_id"),
        Index("ix_bookings_master_id", "master_id"),
        Index("ix_bookings_status", "status"),
        Index("ix_bookings_created_at", "created_at"),
    )

    def __repr__(self) -> str:
        return f"<Booking {self.id} status={self.status}>"
