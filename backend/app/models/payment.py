import uuid
from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, ClassVar, Optional

from sqlalchemy import DateTime, ForeignKey, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.master import MasterProfile


class Payment(BaseModel):
    __tablename__ = "payments"

    booking_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("bookings.id"),
        unique=True,
        nullable=False,
    )
    yukassa_payment_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    platform_fee: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    master_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), nullable=False
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    paid_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    refunded_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSONB, nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    booking: Mapped["Booking"] = relationship(
        "Booking", back_populates="payment"
    )

    # Transient attribute for passing confirmation_url in responses
    _confirmation_url: ClassVar[Optional[str]] = None

    @property
    def confirmation_url(self) -> Optional[str]:
        return self._confirmation_url

    @confirmation_url.setter
    def confirmation_url(self, value: str) -> None:
        self._confirmation_url = value

    def __repr__(self) -> str:
        return f"<Payment {self.id} status={self.status}>"


class Payout(BaseModel):
    __tablename__ = "payouts"

    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_profiles.id"),
        nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    card_last4: Mapped[Optional[str]] = mapped_column(
        String(4), nullable=True
    )
    processed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    master: Mapped["MasterProfile"] = relationship(
        "MasterProfile", back_populates="payouts"
    )

    def __repr__(self) -> str:
        return f"<Payout {self.id} status={self.status}>"
