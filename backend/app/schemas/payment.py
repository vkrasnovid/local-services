from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    amount: float
    platform_fee: float
    master_amount: float
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime


class PayoutCreate(BaseModel):
    amount: float
    card_last4: str


class PayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    amount: float
    status: str
    card_last4: str
    processed_at: Optional[datetime] = None
    created_at: datetime


class TransactionItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: Optional[UUID] = None
    service_name: Optional[str] = None
    amount: float
    status: str
    type: str
    created_at: datetime


class BalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    balance: float
    total_earned: float
    total_withdrawn: float
    recent_payouts: list[PayoutResponse] = []


class WebhookPayload(BaseModel):
    type: str
    event: str
    object: dict[str, Any]
