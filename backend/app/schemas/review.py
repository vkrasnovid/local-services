from datetime import datetime
from uuid import UUID
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.master import UserBrief


class ReviewCreate(BaseModel):
    booking_id: UUID
    rating: int = Field(..., ge=1, le=5)
    text: Optional[str] = None


class ReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    booking_id: UUID
    client: UserBrief
    rating: int
    text: Optional[str] = None
    master_reply: Optional[str] = None
    created_at: datetime


class ReviewReply(BaseModel):
    text: str


class RatingSummary(BaseModel):
    average: float
    count: int
    distribution: dict[str, int]


class ReviewListResponse(BaseModel):
    items: list[ReviewResponse]
    total: int
    page: int
    page_size: int
    pages: int
    rating_summary: RatingSummary
