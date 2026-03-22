import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.category import Category
    from app.models.payment import Payout
    from app.models.portfolio import PortfolioImage
    from app.models.review import Review
    from app.models.service import Service
    from app.models.time_slot import TimeSlot
    from app.models.user import User


class MasterProfile(BaseModel):
    __tablename__ = "master_profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        unique=True,
        nullable=False,
    )
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    category_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    district: Mapped[Optional[str]] = mapped_column(
        String(100), nullable=True
    )
    rating_avg: Mapped[Decimal] = mapped_column(
        Numeric(3, 2), server_default="0", nullable=False
    )
    rating_count: Mapped[int] = mapped_column(
        Integer, server_default="0", nullable=False
    )
    verification_status: Mapped[str] = mapped_column(
        String(20), server_default="pending", nullable=False
    )
    verification_docs: Mapped[Optional[dict]] = mapped_column(
        JSONB, nullable=True
    )
    work_hours: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    is_available: Mapped[bool] = mapped_column(
        Boolean, server_default="true", nullable=False
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), server_default="0", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User", back_populates="master_profile"
    )
    category: Mapped[Optional["Category"]] = relationship(
        "Category", back_populates="master_profiles"
    )
    services: Mapped[List["Service"]] = relationship(
        "Service", back_populates="master"
    )
    portfolio_images: Mapped[List["PortfolioImage"]] = relationship(
        "PortfolioImage", back_populates="master"
    )
    time_slots: Mapped[List["TimeSlot"]] = relationship(
        "TimeSlot", back_populates="master"
    )
    bookings: Mapped[List["Booking"]] = relationship(
        "Booking", back_populates="master"
    )
    reviews: Mapped[List["Review"]] = relationship(
        "Review", back_populates="master"
    )
    payouts: Mapped[List["Payout"]] = relationship(
        "Payout", back_populates="master"
    )

    __table_args__ = (
        Index("ix_master_profiles_user_id", "user_id"),
        Index("ix_master_profiles_category_id", "category_id"),
        Index("ix_master_profiles_verification_status", "verification_status"),
        Index("ix_master_profiles_rating_avg", "rating_avg"),
    )

    def __repr__(self) -> str:
        return f"<MasterProfile {self.id} user={self.user_id}>"
