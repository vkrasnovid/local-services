from datetime import datetime
from uuid import UUID
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    type: str
    title: str
    body: str
    data: Optional[dict[str, Any]] = None
    is_read: bool
    created_at: datetime


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    unread_count: int
    page: int
    page_size: int
    pages: int


class MarkReadRequest(BaseModel):
    notification_ids: list[UUID]


class MarkReadResponse(BaseModel):
    marked_read: int


class FcmTokenCreate(BaseModel):
    token: str
    device_info: Optional[str] = None
