import math
import uuid
from typing import Any, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import (
    Booking,
    ChatRoom,
    MasterProfile,
    Service,
    TimeSlot,
    User,
)
from app.schemas.booking import BookingCreate


async def create_booking(
    db: AsyncSession,
    client_id: uuid.UUID,
    data: BookingCreate,
) -> Booking:
    """Create a booking: verify service, slot availability, ownership, snapshot price, create chat."""
    # Verify service exists
    svc_result = await db.execute(
        select(Service).where(Service.id == data.service_id)
    )
    service = svc_result.scalar_one_or_none()
    if not service:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Service not found",
        )

    # Verify slot exists and is not booked
    slot_result = await db.execute(
        select(TimeSlot).where(TimeSlot.id == data.slot_id)
    )
    slot = slot_result.scalar_one_or_none()
    if not slot:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Time slot not found",
        )
    if slot.is_booked:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Time slot is already booked",
        )

    # Verify service belongs to the same master as the slot
    if service.master_id != slot.master_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Service does not belong to the master of this time slot",
        )

    # Mark slot as booked
    slot.is_booked = True

    # Create booking with price snapshot
    booking = Booking(
        client_id=client_id,
        master_id=service.master_id,
        service_id=service.id,
        slot_id=slot.id,
        price=service.price,
        address=data.address,
        is_online=data.is_online,
    )
    db.add(booking)
    await db.flush()

    # Get master's user_id for chat room
    master_result = await db.execute(
        select(MasterProfile.user_id).where(
            MasterProfile.id == service.master_id
        )
    )
    master_user_id = master_result.scalar_one()

    # Create chat room
    chat_room = ChatRoom(
        booking_id=booking.id,
        client_id=client_id,
        master_user_id=master_user_id,
    )
    db.add(chat_room)

    await db.commit()
    await db.refresh(booking)
    return booking


# Valid status transitions: (current, new) -> allowed roles
_TRANSITIONS: dict[tuple[str, str], set[str]] = {
    ("pending", "confirmed"): {"master"},
    ("pending", "cancelled"): {"client", "master"},
    ("confirmed", "in_progress"): {"master"},
    ("confirmed", "cancelled"): {"client", "master"},
    ("in_progress", "completed"): {"master"},
}


async def update_booking_status(
    db: AsyncSession,
    booking_id: uuid.UUID,
    user: User,
    new_status: str,
    cancel_reason: Optional[str] = None,
) -> Booking:
    """Update booking status with transition validation."""
    result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.slot))
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Determine user's role in this booking
    roles_in_booking: set[str] = set()
    if booking.client_id == user.id:
        roles_in_booking.add("client")

    # Check if user is the master
    master_result = await db.execute(
        select(MasterProfile.user_id).where(
            MasterProfile.id == booking.master_id
        )
    )
    master_user_id = master_result.scalar_one_or_none()
    if master_user_id == user.id:
        roles_in_booking.add("master")

    if not roles_in_booking:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this booking",
        )

    transition_key = (booking.status, new_status)
    allowed_roles = _TRANSITIONS.get(transition_key)

    if allowed_roles is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot transition from '{booking.status}' to '{new_status}'",
        )

    if not roles_in_booking & allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Your role cannot perform this status transition",
        )

    booking.status = new_status

    if new_status == "cancelled":
        booking.cancel_reason = cancel_reason
        booking.cancelled_by = "client" if "client" in roles_in_booking else "master"
        # Free up the slot
        booking.slot.is_booked = False

    await db.commit()
    await db.refresh(booking)
    return booking


async def get_user_bookings(
    db: AsyncSession,
    user_id: uuid.UUID,
    role: str = "client",
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> dict[str, Any]:
    """List bookings from client or master perspective."""
    if role == "master":
        # Find master profile
        mp_result = await db.execute(
            select(MasterProfile.id).where(MasterProfile.user_id == user_id)
        )
        master_profile_id = mp_result.scalar_one_or_none()
        if not master_profile_id:
            return {
                "items": [],
                "total": 0,
                "page": page,
                "page_size": page_size,
                "pages": 0,
            }
        query = select(Booking).where(Booking.master_id == master_profile_id)
    else:
        query = select(Booking).where(Booking.client_id == user_id)

    if status_filter:
        query = query.where(Booking.status == status_filter)

    # Count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    # Order and paginate
    query = (
        query.options(
            selectinload(Booking.service),
            selectinload(Booking.slot),
            selectinload(Booking.client),
            selectinload(Booking.master).selectinload(MasterProfile.user),
        )
        .order_by(Booking.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )

    result = await db.execute(query)
    bookings = result.scalars().all()

    items = []
    for b in bookings:
        # Counterparty depends on perspective
        if role == "master":
            counterparty = b.client
        else:
            counterparty = b.master.user if b.master else None

        items.append(
            {
                "id": b.id,
                "service": b.service,
                "slot": b.slot,
                "status": b.status,
                "price": float(b.price) if b.price else 0,
                "counterparty": counterparty,
                "created_at": b.created_at,
            }
        )

    pages = math.ceil(total / page_size) if page_size else 0

    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": pages,
    }


async def get_booking_detail(
    db: AsyncSession,
    booking_id: uuid.UUID,
    user_id: uuid.UUID,
) -> Booking:
    """Get full booking detail. Verify user is a participant."""
    result = await db.execute(
        select(Booking)
        .options(
            selectinload(Booking.service),
            selectinload(Booking.slot),
            selectinload(Booking.client),
            selectinload(Booking.master).selectinload(MasterProfile.user),
            selectinload(Booking.payment),
            selectinload(Booking.chat_room),
        )
        .where(Booking.id == booking_id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Booking not found",
        )

    # Verify participant
    is_client = booking.client_id == user_id
    is_master = booking.master and booking.master.user_id == user_id

    if not is_client and not is_master:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a participant of this booking",
        )

    return booking
