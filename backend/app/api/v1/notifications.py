import math
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_active_user
from app.models import Notification, User
from app.schemas.notification import (
    MarkReadRequest,
    MarkReadResponse,
    NotificationListResponse,
    NotificationResponse,
)

router = APIRouter()


@router.get("/", response_model=NotificationListResponse)
async def list_notifications(
    is_read: bool | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    base_filter = Notification.user_id == current_user.id

    # Build query with optional is_read filter
    filters = [base_filter]
    if is_read is not None:
        filters.append(Notification.is_read == is_read)

    # Total count
    count_result = await db.execute(
        select(func.count(Notification.id)).where(*filters)
    )
    total = count_result.scalar()

    # Unread count (always for all user's notifications)
    unread_result = await db.execute(
        select(func.count(Notification.id)).where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
    )
    unread_count = unread_result.scalar()

    # Fetch notifications
    offset = (page - 1) * page_size
    result = await db.execute(
        select(Notification)
        .where(*filters)
        .order_by(Notification.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    notifications = result.scalars().all()

    items = [NotificationResponse.model_validate(n) for n in notifications]

    return NotificationListResponse(
        items=items,
        total=total,
        unread_count=unread_count,
        page=page,
        page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


@router.patch("/read", response_model=MarkReadResponse)
async def mark_notifications_read(
    data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        update(Notification)
        .where(
            Notification.id.in_(data.notification_ids),
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .returning(Notification.id)
    )
    marked_ids = result.scalars().all()
    await db.commit()

    return MarkReadResponse(marked_read=len(marked_ids))


@router.patch("/read-all", response_model=MarkReadResponse)
async def mark_all_notifications_read(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    result = await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .returning(Notification.id)
    )
    marked_ids = result.scalars().all()
    await db.commit()

    return MarkReadResponse(marked_read=len(marked_ids))
