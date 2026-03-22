from datetime import date, datetime, time
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.master import UserBrief


class ServiceBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    price: float
    duration_minutes: Optional[int] = None


class TimeSlotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    date: date
    start_time: time
    end_time: time
    is_booked: bool


class TimeSlotCreate(BaseModel):
    date: date
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Time in HH:MM format")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$", description="Time in HH:MM format")


class BulkSlotCreate(BaseModel):
    slots: list[TimeSlotCreate]


class BulkSlotResponse(BaseModel):
    created: int
    items: list[TimeSlotResponse]


class PaymentBrief(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: str
    amount: Optional[float] = None
    confirmation_url: Optional[str] = None


class BookingCreate(BaseModel):
    service_id: UUID
    slot_id: UUID
    address: Optional[str] = None
    is_online: bool = False


class BookingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    master_id: UUID
    service: ServiceBrief
    slot: TimeSlotResponse
    status: str
    price: float
    address: Optional[str] = None
    is_online: bool
    payment: Optional[PaymentBrief] = None
    created_at: datetime


class BookingDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    client_id: UUID
    master_id: UUID
    client: UserBrief
    master: UserBrief
    service: ServiceBrief
    slot: TimeSlotResponse
    status: str
    price: float
    address: Optional[str] = None
    is_online: bool
    payment: Optional[PaymentBrief] = None
    chat_room_id: Optional[UUID] = None
    created_at: datetime


class BookingStatusUpdate(BaseModel):
    status: str
    cancel_reason: Optional[str] = None


class BookingListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    service: ServiceBrief
    slot: TimeSlotResponse
    status: str
    price: float
    counterparty: UserBrief
    created_at: datetime
