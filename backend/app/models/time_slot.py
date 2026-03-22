import uuid
from datetime import date, datetime, time
from typing import TYPE_CHECKING, Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Time,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel

if TYPE_CHECKING:
    from app.models.booking import Booking
    from app.models.master import MasterProfile


class TimeSlot(BaseModel):
    __tablename__ = "time_slots"

    master_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("master_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    is_booked: Mapped[bool] = mapped_column(
        Boolean, server_default="false", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    master: Mapped["MasterProfile"] = relationship(
        "MasterProfile", back_populates="time_slots"
    )
    booking: Mapped[Optional["Booking"]] = relationship(
        "Booking", back_populates="slot", uselist=False
    )

    __table_args__ = (
        UniqueConstraint("master_id", "date", "start_time", name="uq_time_slots_master_date_start"),
        Index("ix_time_slots_master_id_date", "master_id", "date"),
    )

    def __repr__(self) -> str:
        return f"<TimeSlot {self.id} {self.date} {self.start_time}-{self.end_time}>"
