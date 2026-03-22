from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.payment import TransactionItem


class UsersStats(BaseModel):
    total: int
    new_today: int
    new_this_week: int
    by_role: dict[str, int]


class BookingsStats(BaseModel):
    total: int
    active: int
    completed_this_week: int
    cancelled_this_week: int


class RevenueStats(BaseModel):
    total: float
    this_week: float
    platform_fees_total: float
    platform_fees_this_week: float


class DashboardStats(BaseModel):
    users: UsersStats
    bookings: BookingsStats
    revenue: RevenueStats
    masters_pending_verification: int
    reviews_pending_moderation: int


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    role: Optional[str] = None


class VerificationUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class AdminReviewUpdate(BaseModel):
    is_visible: bool


class CategoryCreate(BaseModel):
    name: str
    slug: str
    icon: Optional[str] = None
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    icon: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    name: str
    slug: str
    icon: Optional[str] = None
    sort_order: int
    is_active: bool


class AdminPayoutUpdate(BaseModel):
    status: str
    reason: Optional[str] = None


class TransactionListResponse(BaseModel):
    items: list[TransactionItem]
    total: int
    page: int
    page_size: int
    pages: int
    totals: dict[str, Any]
